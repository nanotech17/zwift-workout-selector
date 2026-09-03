""".zwo (Zwift workout XML) parser.

Normalizes the various real-world element/attribute spellings found in the
wild (case variants, Zone-based power instead of numeric %FTP, etc.) into a
flat list of Step objects that metrics.py can analyze.
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import xml.etree.ElementTree as ET

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


def parse_zwo(filepath: str) -> WorkoutDoc:
    try:
        tree = ET.parse(filepath)
    except ET.ParseError as e:
        raise ZwoParseError(str(e))

    root = tree.getroot()
    doc = WorkoutDoc(filepath=filepath)

    def text(tag):
        el = root.find(tag)
        return el.text.strip() if el is not None and el.text else None

    doc.name = text("name")
    doc.author = text("author")
    doc.description = text("description")
    doc.sport_type = (text("sportType") or "bike").lower()
    if doc.sport_type == "ride":
        doc.sport_type = "bike"
    doc.category = text("category")
    doc.subcategory = text("subcategory")
    doc.category_override = text("categoryOverride")

    tags_el = root.find("tags")
    if tags_el is not None:
        doc.embedded_tags = [
            t.attrib["name"] for t in tags_el.findall("tag") if t.attrib.get("name")
        ]

    workout_el = root.find("workout")
    if workout_el is None:
        doc.warnings.append("no <workout> element")
        return doc

    doc.num_blocks = len(list(workout_el))

    for el in workout_el:
        canonical = _CANONICAL_TAGS.get(el.tag.lower())
        if canonical is None:
            doc.warnings.append("unknown step element: %s" % el.tag)
            continue
        attrs = el.attrib

        if canonical == "textevent":
            continue  # coaching text only, not part of the power profile

        if canonical == "RestDay":
            doc.steps.append(Step(kind="rest", duration_sec=_f(attrs, "Duration") or 0.0))
            continue

        duration = _f(attrs, "Duration") or 0.0

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
            doc.steps.append(Step(kind=kind, duration_sec=duration,
                                   power_low=lo, power_high=hi, power_estimated=est,
                                   cadence_low=cad_lo, cadence_high=cad_hi))

        elif canonical == "SteadyState":
            lo, hi, est = _resolve_power(attrs, "Power", "PowerLow", "PowerHigh", "Zone")
            cad_lo, cad_hi = _cadence(attrs)
            doc.steps.append(Step(kind="steady", duration_sec=duration,
                                   power_low=lo, power_high=hi, power_estimated=est,
                                   cadence_low=cad_lo, cadence_high=cad_hi))

        elif canonical == "FreeRide":
            offsets = []
            for child in el:
                if child.tag.lower() != "textevent":
                    continue
                off = _f(child.attrib, "timeoffset")
                offsets.append(off if off is not None else 0.0)
            doc.steps.append(Step(kind="freeride", duration_sec=duration,
                                   textevent_offsets=offsets))

        elif canonical == "MaxEffort":
            doc.steps.append(Step(kind="maxeffort", duration_sec=duration))

        elif canonical == "IntervalsT":
            repeat = int(_f(attrs, "Repeat") or 1)
            doc.num_intervals += repeat
            on_dur = _f(attrs, "OnDuration") or 0.0
            off_dur = _f(attrs, "OffDuration") or 0.0
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
                doc.steps.append(Step(kind=on_kind, duration_sec=on_dur,
                                       power_low=on_lo, power_high=on_hi, power_estimated=on_est,
                                       cadence_low=cad_lo, cadence_high=cad_hi))
                if off_dur > 0:
                    doc.steps.append(Step(kind=off_kind, duration_sec=off_dur,
                                           power_low=off_lo, power_high=off_hi, power_estimated=off_est,
                                           cadence_low=cad_rest, cadence_high=cad_rest))

    return doc
