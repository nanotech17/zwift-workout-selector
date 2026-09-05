""".zwo (Zwift workout XML) parser.

Normalizes the various real-world element/attribute spellings found in the
wild (case variants, Zone-based power instead of numeric %FTP, etc.) into a
flat list of Step objects that metrics.py can analyze.
"""
import math
import os
from dataclasses import dataclass, field
from typing import List, Optional, Dict
# .zwo files can come from third-party sources (Zwift forums, workouts.wad
# extraction) — defusedxml guards xml.etree.ElementTree's parse against
# entity-expansion ("billion laughs") DoS payloads while staying API-
# compatible (same Element/ParseError types; verified 2026-09). Its own
# attack-detected exceptions (EntitiesForbidden etc.) subclass ValueError,
# not ParseError, so they're caught separately below.
import defusedxml.ElementTree as ET
from defusedxml.common import DefusedXmlException

# defusedxml only guards XML-parser-level attacks (entity expansion etc.) —
# a well-formed .zwo with an absurd *semantic* value (Repeat="100000000",
# Duration="999999999999", ...) parses fine and then blows up CPU/RAM
# building Step objects or the per-second profile in metrics.py. These
# bound every such value at generous multiples of anything seen in the real
# ~3,400-workout catalog this app was built against (max Repeat 63, max
# duration 13.6h, max file 29KB) — see the 2026-09 review for the exact
# empirical check. Centralized here so they read as one security boundary.
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024       # 10 MiB
MAX_REPEAT = 1000
MAX_TOTAL_STEPS = 10_000
MAX_TOTAL_DURATION_SEC = 24 * 3600           # 24h — also the effective
                                              # per-step ceiling (no separate
                                              # tighter cap: real "Dynamic
                                              # Workouts" route files use a
                                              # single ~13.6h step for the
                                              # whole ride — see 2026-09
                                              # regression found against the
                                              # real catalog. A step can't
                                              # exceed this without
                                              # immediately tripping the
                                              # running total in _add_step,
                                              # so a separate bound added no
                                              # protection, only false
                                              # rejections.
MAX_NAME_LEN = 1_000
MAX_DESCRIPTION_LEN = 100_000
MAX_TAG_LEN = 1_000

# Real files contain case variants of the "official" tag names
# (e.g. "Freeride", "cooldown", "SolidState" as a typo for "SteadyState").
_CANONICAL_TAGS = {
    "warmup": "Warmup",
    "cooldown": "Cooldown",
    "steadystate": "SteadyState",
    "solidstate": "SteadyState",
    "intervalst": "IntervalsT",
    "ramp": "Ramp",
    "freeride": "FreeRide",
    "maxeffort": "MaxEffort",
    "restday": "RestDay",
    "textevent": "textevent",
}

# Zwift's own 6-zone bands (see workout-selector.md §7). Used only as a
# fallback when a step specifies its target via Zone="N" instead of an
# explicit %FTP, since Zone alone gives no exact number.
ZONE_MIDPOINT_FRAC = {1: 0.55, 2: 0.675, 3: 0.83, 4: 0.98, 5: 1.13, 6: 1.30}


@dataclass
class Step:
    kind: str  # warmup | cooldown | ramp | steady | interval_on | interval_off | freeride | maxeffort | rest
    duration_sec: float
    power_low: Optional[float] = None   # fraction of FTP at segment start
    power_high: Optional[float] = None  # fraction of FTP at segment end (== power_low if constant)
    cadence_low: Optional[float] = None
    cadence_high: Optional[float] = None
    power_estimated: bool = False       # True if power_low/high came from a Zone=N fallback
    # <TextEvent timeoffset="..."> children, freeride steps only (used by
    # metrics.py's FreeRide bucket classifier to detect a "coached drill"
    # block vs. a quiet one — see workout_selector.md FreeRide §, 2026-09).
    textevent_offsets: List[float] = field(default_factory=list)
    # Zwift's own "this step is part of an official FTP test" markers —
    # SteadyState ramptest="1" (ramp-style test), FreeRide ftptest="1"
    # (classic 20min-style test), or a FreeRide carrying a
    # <gameplayevent type="GPE_SIMPLE_FTP_ESTIMATION"> child (the "Simple
    # FTP Test" variant). Content-based, so it works regardless of title —
    # e.g. "Flat Out Fast" and "Test Day Ride" carry no FTP-test wording at
    # all (owner survey, 2026-09). Used by metrics.py's ftp_test primary_type.
    is_ftp_test_marker: bool = False


@dataclass
class WorkoutDoc:
    filepath: str
    name: Optional[str] = None
    author: Optional[str] = None
    description: Optional[str] = None
    sport_type: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    category_override: Optional[str] = None
    embedded_tags: List[str] = field(default_factory=list)
    steps: List[Step] = field(default_factory=list)
    num_blocks: int = 0          # count of raw <workout> child elements (pre-expansion)
    num_intervals: int = 0       # total IntervalsT repeat count, summed
    warnings: List[str] = field(default_factory=list)


class ZwoParseError(Exception):
    pass


def _f(attrs: Dict[str, str], key: str) -> Optional[float]:
    v = attrs.get(key)
    if v is None or v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None


def _resolve_power(attrs: Dict[str, str], power_key: str, low_key: str, high_key: str, zone_key: str):
    """Returns (power_low, power_high, estimated) as fractions of FTP, or (None, None, False)."""
    p = _f(attrs, power_key)
    if p is not None:
        return p, p, False
    lo, hi = _f(attrs, low_key), _f(attrs, high_key)
    if lo is not None and hi is not None:
        return lo, hi, False
    zone = _f(attrs, zone_key)
    if zone is not None:
        v = ZONE_MIDPOINT_FRAC.get(int(zone))
        if v is not None:
            return v, v, True
    return None, None, False


def _cadence(attrs: Dict[str, str]):
    lo = _f(attrs, "CadenceLow")
    hi = _f(attrs, "CadenceHigh")
    single = _f(attrs, "Cadence")
    if single is not None and lo is None and hi is None:
        lo = hi = single
    return lo, hi


def _check_duration(sec: float, what: str) -> float:
    """Rejects a Duration/OnDuration/OffDuration value outright rather than
    clamping it — NaN/inf parse successfully via float() and would otherwise
    reach range()/int(round()) downstream (metrics.py). The upper bound
    itself is enforced by _add_step's running total against
    MAX_TOTAL_DURATION_SEC, not here — see that constant's comment."""
    if not math.isfinite(sec) or sec < 0:
        raise ZwoParseError("%s out of range: %r" % (what, sec))
    return sec


def parse_zwo(filepath: str) -> WorkoutDoc:
    try:
        if os.path.getsize(filepath) > MAX_FILE_SIZE_BYTES:
            raise ZwoParseError("file too large (>%d bytes)" % MAX_FILE_SIZE_BYTES)
    except OSError as e:
        raise ZwoParseError(str(e))

    try:
        tree = ET.parse(filepath)
    except (ET.ParseError, DefusedXmlException) as e:
        raise ZwoParseError(str(e))

    root = tree.getroot()
    doc = WorkoutDoc(filepath=filepath)

    def text(tag, max_len=None):
        el = root.find(tag)
        v = el.text.strip() if el is not None and el.text else None
        if v and max_len and len(v) > max_len:
            raise ZwoParseError("<%s> too long (>%d chars)" % (tag, max_len))
        return v

    doc.name = text("name", MAX_NAME_LEN)
    doc.author = text("author", MAX_NAME_LEN)
    doc.description = text("description", MAX_DESCRIPTION_LEN)
    doc.sport_type = (text("sportType") or "bike").lower()
    if doc.sport_type == "ride":
        doc.sport_type = "bike"
    doc.category = text("category", MAX_NAME_LEN)
    doc.subcategory = text("subcategory", MAX_NAME_LEN)
    doc.category_override = text("categoryOverride", MAX_NAME_LEN)

    tags_el = root.find("tags")
    if tags_el is not None:
        doc.embedded_tags = [
            t.attrib["name"] for t in tags_el.findall("tag") if t.attrib.get("name")
        ]
        for tag in doc.embedded_tags:
            if len(tag) > MAX_TAG_LEN:
                raise ZwoParseError("tag too long (>%d chars)" % MAX_TAG_LEN)

    workout_el = root.find("workout")
    if workout_el is None:
        doc.warnings.append("no <workout> element")
        return doc

    doc.num_blocks = len(list(workout_el))

    # Total step count and total duration are tracked here (not checked once
    # at the end) so a pathological file is rejected as soon as either
    # bound is crossed, mid-expansion — not after the resources to build
    # the full list have already been spent.
    total_duration = 0.0

    def _add_step(step: Step) -> None:
        nonlocal total_duration
        if len(doc.steps) >= MAX_TOTAL_STEPS:
            raise ZwoParseError("workout has too many steps (>%d)" % MAX_TOTAL_STEPS)
        total_duration += step.duration_sec
        if total_duration > MAX_TOTAL_DURATION_SEC:
            raise ZwoParseError("workout total duration exceeds %ds" % MAX_TOTAL_DURATION_SEC)
        doc.steps.append(step)

    for el in workout_el:
        canonical = _CANONICAL_TAGS.get(el.tag.lower())
        if canonical is None:
            doc.warnings.append("unknown step element: %s" % el.tag)
            continue
        attrs = el.attrib

        if canonical == "textevent":
            continue  # coaching text only, not part of the power profile

        if canonical == "RestDay":
            _add_step(Step(kind="rest", duration_sec=_check_duration(_f(attrs, "Duration") or 0.0, "Duration")))
            continue

        duration = _check_duration(_f(attrs, "Duration") or 0.0, "Duration")

        if canonical in ("Warmup", "Cooldown", "Ramp"):
            lo, hi, est = _resolve_power(attrs, "Power", "PowerLow", "PowerHigh", "Zone")
            # Zwift's client appears to pick ramp direction from the element
            # type itself (Warmup always rises, Cooldown always falls),
            # treating PowerLow/PowerHigh as an unordered pair of bounds —
            # not, as the names suggest, "start value"/"end value". ~13% of
            # real Cooldown blocks across the catalog have PowerLow <
            # PowerHigh (the numerically-ascending order), yet the owner
            # directly confirmed in Zwift that two of them ("SST (Med)",
            # "SST (Long)") still play as a normal descending cooldown —
            # so power_low/power_high (chronological start/end everywhere
            # else in this codebase) are normalized here to match actual
            # playback direction. Ramp has no implied canonical direction
            # (used for both rising and falling mid-workout ramps) so it's
            # deliberately left as literally authored. (2026-09)
            if lo is not None and hi is not None:
                if canonical == "Warmup" and lo > hi:
                    lo, hi = hi, lo
                elif canonical == "Cooldown" and lo < hi:
                    lo, hi = hi, lo
            cad_lo, cad_hi = _cadence(attrs)
            kind = {"Warmup": "warmup", "Cooldown": "cooldown", "Ramp": "ramp"}[canonical]
            _add_step(Step(kind=kind, duration_sec=duration,
                            power_low=lo, power_high=hi, power_estimated=est,
                            cadence_low=cad_lo, cadence_high=cad_hi))

        elif canonical == "SteadyState":
            lo, hi, est = _resolve_power(attrs, "Power", "PowerLow", "PowerHigh", "Zone")
            cad_lo, cad_hi = _cadence(attrs)
            _add_step(Step(kind="steady", duration_sec=duration,
                            power_low=lo, power_high=hi, power_estimated=est,
                            cadence_low=cad_lo, cadence_high=cad_hi,
                            is_ftp_test_marker=attrs.get("ramptest") == "1"))

        elif canonical == "FreeRide":
            offsets = []
            # Most ramp tests mark their SteadyState steps with ramptest="1"
            # (handled above), but at least one real file (Zwift's onboarding
            # ramp test) marks its FreeRide steps instead — check both
            # attributes on FreeRide too (owner survey, 2026-09).
            is_ftp_test_marker = attrs.get("ftptest") == "1" or attrs.get("ramptest") == "1"
            for child in el:
                child_tag = child.tag.lower()
                if child_tag == "gameplayevent":
                    if child.attrib.get("type") == "GPE_SIMPLE_FTP_ESTIMATION":
                        is_ftp_test_marker = True
                    continue
                if child_tag != "textevent":
                    continue
                off = _f(child.attrib, "timeoffset")
                offsets.append(off if off is not None else 0.0)
            _add_step(Step(kind="freeride", duration_sec=duration,
                            textevent_offsets=offsets,
                            is_ftp_test_marker=is_ftp_test_marker))

        elif canonical == "MaxEffort":
            _add_step(Step(kind="maxeffort", duration_sec=duration))

        elif canonical == "IntervalsT":
            repeat = int(_f(attrs, "Repeat") or 1)
            if repeat > MAX_REPEAT:
                raise ZwoParseError("IntervalsT Repeat exceeds %d" % MAX_REPEAT)
            doc.num_intervals += repeat
            on_dur = _check_duration(_f(attrs, "OnDuration") or 0.0, "OnDuration")
            off_dur = _check_duration(_f(attrs, "OffDuration") or 0.0, "OffDuration")
            on_lo, on_hi, on_est = _resolve_power(attrs, "OnPower", "PowerOnLow", "PowerOnHigh", "PowerOnZone")
            off_lo, off_hi, off_est = _resolve_power(attrs, "OffPower", "PowerOffLow", "PowerOffHigh", "PowerOffZone")
            cad_lo, cad_hi = _cadence(attrs)
            cad_rest = _f(attrs, "CadenceResting")

            # Normally OnPower is the harder phase and OffPower is recovery,
            # but some authors write it the other way around (seen in
            # practice: OnPower=45%, OffPower=76% "Zone 3" with the workout's
            # own coaching text confirming Off is the real effort). Label by
            # actual intensity rather than by attribute name, so "exclude
            # interval_off from the main set" (metrics.py) always excludes
            # the true rest phase regardless of which XML slot it came from.
            on_ref = on_lo if on_lo is not None else -1.0
            off_ref = off_lo if off_lo is not None else -1.0
            on_kind, off_kind = ("interval_on", "interval_off") if on_ref >= off_ref else ("interval_off", "interval_on")

            for _ in range(repeat):
                _add_step(Step(kind=on_kind, duration_sec=on_dur,
                                power_low=on_lo, power_high=on_hi, power_estimated=on_est,
                                cadence_low=cad_lo, cadence_high=cad_hi))
                if off_dur > 0:
                    _add_step(Step(kind=off_kind, duration_sec=off_dur,
                                    power_low=off_lo, power_high=off_hi, power_estimated=off_est,
                                    cadence_low=cad_rest, cadence_high=cad_rest))

    return doc
