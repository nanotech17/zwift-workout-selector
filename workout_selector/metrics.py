"""Derives §7 analysis metrics (NP/IF/TSS, zone distribution, structure,
primary type) from a parsed WorkoutDoc."""
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .zwo_parser import WorkoutDoc

# Zwift's actual in-game 6-zone %FTP bands, per
# https://zwiftinsider.com/power-zone-colors/ (workout-selector.md §7).
# Upper bound of each band; the last zone (6) is open-ended. Zone 1 is the
# only exclusive-upper boundary (Zwift: "below 60%" for Z1, "60-75%" for
# Z2) — see _zone_of, which special-cases it. These are NOT the classic
# Coggan zones, which run one point higher at each Z3+ boundary
# (76-90/91-105/106-120/121+) — Zwift's in-game bands are consistently
# shifted down by one point from Z3 up.
ZONE_BOUNDS = [(1, 0.60), (2, 0.75), (3, 0.89), (4, 1.04), (5, 1.18), (6, None)]

# A workout authored at e.g. 104.45%FTP is presented everywhere in this UI
# rounded to "104%" (display rounds to the nearest whole point), so a value
# a fraction over a zone's boundary reads as if it were exactly on it —
# yet used to fall into the next zone up. This tolerance makes
# classification match that rounded reading: half a point over a
# boundary still counts as the lower zone; a full half-point over tips
# it to the next one (owner decision 2026-09, from "Week 2.5 - Climbing
# Sustained Threshold", authored at 104.45% and expected to read as Z4).
ZONE_BOUNDARY_TOLERANCE = 0.005

# Legacy "spent meaningful time near sweet spot" signal — powers the
# `sweet_spot` auto_tag below via sweet_spot_pct. Independent of, and not to
# be confused with, the stricter SWEETSPOT_* definition further down (which
# drives the separate `sweetspot` tag, no underscore).
SWEET_SPOT_LOW, SWEET_SPOT_HIGH = 0.88, 0.94

# A step counts as "interval work" for structure classification once it
# makes up at least this share of powered time; below that it reads as
# steady riding with a couple of surges rather than a true interval set.
INTERVAL_STRUCTURE_THRESHOLD = 0.60

# Warmup/cooldown are preamble/wind-down, not the workout's actual content,
# so they're excluded from both primary-zone and structure_type math (spec
# §7: "主ゾーン（最大滞在ゾーン、またはメインセットのゾーン）").
#
# interval_off is deliberately *not* excluded here, even though it's the
# "rest between reps" — earlier versions of this code excluded it, which
# broke workouts where the off phase is far longer than the on phase (e.g.
# IntervalsT OnDuration=10s/OffDuration=290s: a long endurance base pace
# with brief 10s openers, not real recovery from real effort). Excluding it
# outright made a handful of 10s spikes at 130% outweigh 2000+ seconds at
# 70% and the ride read as "anaerobic". Leaving it in and letting
# power^PRIMARY_ZONE_WEIGHT_EXPONENT weighting (below) do the down-weighting
# instead handles both shapes correctly — verified against every interval
# workout this module's classification has been fixed for so far.
NON_WORK_KINDS = {"warmup", "cooldown"}

# Some authors set an all-out-effort step's target power to an arbitrary,
# physiologically-unsustainable value instead of using <MaxEffort>, with
# descriptions like "ignore the power target here" — conventionally an
# exact 300%FTP (74 occurrences of precisely that value catalog-wide,
# 2026-09 survey, versus a smooth, continuous spread of real short-burst
# anaerobic targets from 150% up through 280%). Treated the same as
# MaxEffort/FreeRide: excluded from NP/TSS, duration still counts. Was
# 1.80 (180%FTP), which caught genuine ~30s anaerobic-capacity targets in
# the 180-280% range too (e.g. "The Wringer" at 205%, "Anaerobic Blasts"
# at 225%) and silently dropped them from classification entirely,
# misreading recovery-heavy interval workouts as primary_type=recovery
# since only the easy portions between bursts remained. Raised to sit
# just under the 300% convention instead (owner decision, 2026-09).
EXTREME_POWER_FRAC = 2.95

# Stricter "dedicated sustained sweet spot session" definition (owner spec,
# 2026-09), used only for the `sweetspot` tag — see _is_sweetspot_workout.
# Used to live as an override of primary_type ("tempo" -> "sweetspot"), but
# that made it mutually exclusive with primary_type=threshold/tempo even
# though a real sweet-spot session's dominant zone is often already
# threshold. Moved to an independent tag so it can coexist with both.
SWEETSPOT_TAG_LOW, SWEETSPOT_TAG_HIGH = 0.85, 0.95
SWEETSPOT_HIGH_FRAC = 1.05
SWEETSPOT_RECOVERY_FRAC = 0.60  # "easy recovery" excluded from WORK_TIME — matches Zwift's Z1 (Recovery) upper bound
SWEETSPOT_MIN_SS_SECONDS = 20 * 60
SWEETSPOT_SS_RATIO_MIN = 0.50
SWEETSPOT_HIGH_RATIO_MAX = 0.10

HIGH_CADENCE_RPM = 100
LOW_CADENCE_RPM = 70

# Z1-dominant is only "recovery" up to this length; longer than that reads as
# a deliberate long easy ride (endurance base), not a recovery spin, even
# though the zone weighting alone can't tell the two apart (owner spec,
# 2026-09).
RECOVERY_MAX_DURATION_SEC = 90 * 60

# Some authors hand-roll an interval set as a plain alternating sequence of
# <SteadyState> blocks instead of <IntervalsT> (num_intervals stays 0, every
# step is kind="steady"). Raw-seconds zone tallying can't tell "on" from
# "off" in that case — the long easy stretches out-count the short hard ones
# and the workout reads as "recovery". Weighting each second by power^N
# instead of counting it flat fixes this: easy seconds contribute much less,
# so the zone containing the real work can still win even at a time
# disadvantage.
#
# N=4, matching NP's own weighting, not something milder — an N=2 compromise
# was tried in between and seemed to fix an "easy ride with brief 10s/130%FTP
# openers" case that N=4 read as anaerobic, but that turned out to be a
# misdiagnosis: the real cause was interval_off being excluded from this sum
# entirely (see NON_WORK_KINDS above — no longer excluded), which starved
# the workout's actual base pace of any weight regardless of N. With that
# fixed, N=4 correctly handles both extremes: long recovery diluting real
# work (a hard effort mistaken for "recovery"), and a brief opener diluted by
# a long easy base (an easy ride mistaken for "anaerobic") — verified against
# five real workouts spanning both failure shapes plus one genuine 60s/150-
# 170%FTP max-effort case that N=2 got wrong (recovery instead of anaerobic;
# N=2 wasn't a strong enough weighting to let three 60s max efforts outweigh
# four 360s recovery blocks between them).
#
# Variability Index (NP / average power) then does the analogous job for
# structure_type when no <IntervalsT> was found: a VI this far above 1.0
# means the power trace is spiky enough to be an interval set in substance,
# regardless of which XML element the author used to write it.
VI_INTERVAL_THRESHOLD = 1.15
VI_MIXED_THRESHOLD = 1.08

PRIMARY_ZONE_WEIGHT_EXPONENT = 4

# FreeRide has no %FTP target of its own — ERG unlocks and the rider just
# pedals free, so by default (bucket ③ below) it's excluded from NP/TSS
# entirely, same as MaxEffort. But real catalog usage of FreeRide splits
# into three shapes (owner survey, 2026-09, 165 deduped has_freeride=1
# workouts):
#   ① recovery/endurance-like — an easy spin block in an otherwise easy
#     ride (e.g. a genuine "Free Ride" session). Treated as flat Z1.
#   ② threshold/vo2/anaerobic-like — FreeRide standing in for an
#     all-out/cadence/sprint drill the author didn't want ERG locking
#     (short repeated bursts, or sitting alongside independently-hard
#     IntervalsT/Ramp content elsewhere in the same file). Given a
#     duration-tiered representative %FTP (power-duration-curve shaped:
#     short = much harder than long).
#   ③ others/indeterminate — everything else, most often a long FreeRide
#     block carrying periodic coaching TextEvents (cadence drill,
#     structured-but-unquantifiable). Left exactly as before: excluded
#     from intensity math, duration-only. Deliberately not interpreted via
#     TextEvent message text — the owner's call, since a free-text/NLP
#     read is "計算式化するのが困難" (too hard to turn into a formula) and
#     the structural signals below already cover ①/② well enough.
#
# Classification uses only structural signals (element durations/counts,
# textevent counts/offsets, the file's own non-FreeRide zone content) —
# never coaching text — in this priority order (validated against the
# survey's spot-checks, including "Week 7.2 - Cadence Into Over-Unders",
# which an earlier ordering wrongly bucketed as ① despite carrying a real
# PowerOnZone=5 IntervalsT block elsewhere in the file):
#   1. >=3 short (<=45s) FreeRide blocks in the file -> ② (repeated bursts
#      are a sprint/cadence drill, not an easy spin)
#   2. non-FreeRide content elsewhere in the file reaches zone>=4 -> ②
#      (independent proof this is a hard session; a long ambiguous
#      FreeRide block next to it isn't hiding anything, so ③'s rationale
#      doesn't apply)
#   3. a long (>=180s) FreeRide block has >=3 TextEvents at distinct
#      nonzero offsets -> ③ (periodic coaching cues = a structured drill
#      script, not a quiet easy spin, but not quantifiable either)
#   4. non-FreeRide content stays <=zone 3 AND every FreeRide block in the
#      file carries at most one TextEvent -> ① (quiet, easy)
#   5. anything left -> ③
FREERIDE_SHORT_SEC = 45
FREERIDE_LONG_SEC = 180
FREERIDE_SHORT_BURST_COUNT_MIN = 3
FREERIDE_PERIODIC_TEXTEVENT_MIN = 3

FREERIDE_BUCKET1_FRAC = 0.55  # flat Z1, reuses zwo_parser.ZONE_MIDPOINT_FRAC[1]

# Duration-tiered representative %FTP for bucket ②, owner spec 2026-09
# ("計算が複雑になりすぎたり、副作用が起きる懸念" was evaluated and judged
# safe: max value 1.70 stays well under EXTREME_POWER_FRAC, so imputed
# FreeRide steps never trip the has_max_sprint exclusion). (upper_bound_sec,
# representative_frac); a block longer than the last tier's bound falls
# back to that tier's value.
FREERIDE_BUCKET2_TIERS = [
    (30, 1.70),     # <=30s: sprint / anaerobic
    (120, 1.30),    # 30s-2min: anaerobic capacity
    (300, 1.13),    # 2-5min: VO2max
    (600, 1.05),    # 5-10min: VO2max-threshold
    (1200, 0.98),   # 10-20min: threshold
    (3600, 0.95),   # 20-60min: around FTP
]

# Settings-screen-configurable tuning (C phase, continued from zone bounds).
# Deliberately excludes PRIMARY_ZONE_WEIGHT_EXPONENT above — that exponent's
# effect on classification is far less predictable to a non-developer than
# "a threshold in %FTP/minutes/ratio", and it isn't one of the items the
# owner asked to expose. compute_metrics()/_is_sweetspot_workout() take a
# `tuning` dict (merged over this default) the same way zone_bounds works;
# ingest.py is the only caller that reads settings and threads it through.
DEFAULT_TUNING = {
    "sweet_spot_low": SWEET_SPOT_LOW,
    "sweet_spot_high": SWEET_SPOT_HIGH,
    "sweet_spot_tag_min_pct": 15.0,
    "sweetspot_tag_low": SWEETSPOT_TAG_LOW,
    "sweetspot_tag_high": SWEETSPOT_TAG_HIGH,
    "sweetspot_high_frac": SWEETSPOT_HIGH_FRAC,
    "sweetspot_recovery_frac": SWEETSPOT_RECOVERY_FRAC,
    "sweetspot_min_minutes": SWEETSPOT_MIN_SS_SECONDS / 60,
    "sweetspot_ss_ratio_min": SWEETSPOT_SS_RATIO_MIN,
    "sweetspot_high_ratio_max": SWEETSPOT_HIGH_RATIO_MAX,
    "interval_structure_threshold": INTERVAL_STRUCTURE_THRESHOLD,
    "vi_interval_threshold": VI_INTERVAL_THRESHOLD,
    "vi_mixed_threshold": VI_MIXED_THRESHOLD,
    "high_cadence_rpm": HIGH_CADENCE_RPM,
    "low_cadence_rpm": LOW_CADENCE_RPM,
    "extreme_power_frac": EXTREME_POWER_FRAC,
}


def _zone_of(power_frac: float, bounds=ZONE_BOUNDS) -> int:
    """bounds defaults to the Zwift-reference ZONE_BOUNDS above, but callers
    that go through the settings screen's configurable zone boundaries
    (ingest.py) pass the owner's current values instead — see
    settings.get_zone_bounds. This function stays a pure function of its
    arguments either way; it never reads settings itself."""
    if power_frac < bounds[0][1] + ZONE_BOUNDARY_TOLERANCE:  # Z1 is exclusive at its top ("below 60%")
        return 1
    for zone, upper in bounds[1:]:
        if upper is None or power_frac < upper + ZONE_BOUNDARY_TOLERANCE:
            return zone
    return 6


def _is_sweetspot_workout(doc: WorkoutDoc, tuning: dict) -> bool:
    """Owner's stricter Sweet Spot test (2026-09): a dedicated sustained
    sweet-spot session, not just "spent some time near sweet spot power".

    SS_TIME   = time at tuning["sweetspot_tag_low"]-["sweetspot_tag_high"] FTP, over the whole workout
    HIGH_TIME = time above tuning["sweetspot_high_frac"] FTP, over the whole workout
    WORK_TIME = time excluding warmup/cooldown and "easy recovery"
                (below tuning["sweetspot_recovery_frac"] FTP)

    Qualifies when SS_TIME >= tuning["sweetspot_min_minutes"] AND
    SS_TIME/WORK_TIME >= tuning["sweetspot_ss_ratio_min"] AND
    HIGH_TIME/WORK_TIME <= tuning["sweetspot_high_ratio_max"]. Runs its own
    pass over doc.steps rather than reusing compute_metrics' profile loop,
    since that loop excludes FreeRide/MaxEffort and extreme-power steps
    entirely (right for NP/TSS, wrong here — SS/HIGH/WORK are defined over
    the literal power trace with no such exclusions)."""
    ss_low, ss_high = tuning["sweetspot_tag_low"], tuning["sweetspot_tag_high"]
    high_frac = tuning["sweetspot_high_frac"]
    recovery_frac = tuning["sweetspot_recovery_frac"]

    ss_time = 0.0
    high_time = 0.0
    work_time = 0.0

    for s in doc.steps:
        dur = s.duration_sec or 0
        if dur <= 0:
            continue
        non_work_kind = s.kind in NON_WORK_KINDS

        if s.power_low is None:
            # FreeRide/MaxEffort: no %FTP target, so unclassifiable as
            # SS/HIGH, but still real work content (not easy recovery).
            if not non_work_kind and s.kind != "rest":
                work_time += dur
            continue

        n = int(round(dur))
        if n <= 0:
            continue
        for i in range(n):
            frac = i / n
            p = s.power_low + (s.power_high - s.power_low) * frac
            if ss_low <= p <= ss_high:
                ss_time += 1
            if p > high_frac:
                high_time += 1
            if not non_work_kind and p >= recovery_frac:
                work_time += 1

    if work_time <= 0:
        return False
    return (
        ss_time >= tuning["sweetspot_min_minutes"] * 60
        and (ss_time / work_time) >= tuning["sweetspot_ss_ratio_min"]
        and (high_time / work_time) <= tuning["sweetspot_high_ratio_max"]
    )


@dataclass
class Metrics:
    duration_sec: int = 0
    powered_duration_sec: int = 0
    avg_intensity: Optional[float] = None
    np_frac: Optional[float] = None
    if_frac: Optional[float] = None
    tss: Optional[float] = None
    num_blocks: int = 0
    num_intervals: int = 0
    work_rest_ratio: Optional[float] = None
    structure_type: str = "steady"
    has_cadence: bool = False
    has_freeride: bool = False
    has_ramp: bool = False
    has_maxeffort: bool = False
    has_max_sprint: bool = False
    has_high_cadence: bool = False
    has_low_cadence: bool = False
    has_warmup: bool = False
    has_cooldown: bool = False
    is_rest_day: bool = False
    primary_zone: Optional[int] = None
    primary_type: str = "mixed"
    zone_pcts: Dict[int, float] = field(default_factory=dict)
    sweet_spot_pct: float = 0.0
    power_estimated: bool = False
    # The 10-value 副タイプ (sub-type) vocabulary — kept separate from
    # doc.embedded_tags (the workout file's own free-form <tags>) so ingest
    # can store them under a distinct tag_type instead of mixing the two
    # (owner decision, 2026-09). Deliberately excludes primary_type/
    # structure_type: those already have dedicated columns + search UI, so
    # duplicating them here would just re-pollute the tag pool they were
    # split out to avoid.
    sub_types: List[str] = field(default_factory=list)
    content_hash: str = ""


def compute_content_hash(doc: WorkoutDoc) -> str:
    """A fingerprint of the workout's actual structure (sport + each step's
    kind/duration/power/cadence) — independent of name, description,
    uniqueId, or coaching text. Used to spot two files that are the same
    session in substance (e.g. a training plan reusing one workout across
    several weeks under different names) so search can dedupe them."""
    parts = [doc.sport_type or ""]
    for s in doc.steps:
        parts.append("|".join(str(v) for v in (
            s.kind,
            round(s.duration_sec, 1),
            round(s.power_low, 4) if s.power_low is not None else "",
            round(s.power_high, 4) if s.power_high is not None else "",
            round(s.cadence_low, 1) if s.cadence_low is not None else "",
            round(s.cadence_high, 1) if s.cadence_high is not None else "",
        )))
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _freeride_bucket2_value(duration_sec: float) -> float:
    for upper, frac in FREERIDE_BUCKET2_TIERS:
        if duration_sec <= upper:
            return frac
    return FREERIDE_BUCKET2_TIERS[-1][1]


def _freeride_structural_signals(doc: WorkoutDoc):
    """(short_burst_count, long_block_has_periodic_textevents,
    every_block_has_at_most_one_textevent) — see the FreeRide classification
    comment above PRIMARY_ZONE_WEIGHT_EXPONENT."""
    short_count = 0
    long_block_periodic = False
    textevent_counts = []
    for s in doc.steps:
        if s.kind != "freeride":
            continue
        dur = s.duration_sec or 0.0
        textevent_counts.append(len(s.textevent_offsets))
        if dur <= FREERIDE_SHORT_SEC:
            short_count += 1
        elif dur >= FREERIDE_LONG_SEC:
            distinct_nonzero = len([o for o in s.textevent_offsets if o > 0])
            if distinct_nonzero >= FREERIDE_PERIODIC_TEXTEVENT_MIN:
                long_block_periodic = True
    all_quiet = all(c <= 1 for c in textevent_counts) if textevent_counts else True
    return short_count, long_block_periodic, all_quiet


def _freeride_surrounding_max_zone(doc: WorkoutDoc, zone_bounds, extreme_power_frac: float) -> int:
    """Highest zone reached by the file's own non-FreeRide, non-extreme
    content — independent evidence of how hard the session is."""
    max_zone = 0
    for s in doc.steps:
        if s.kind in ("freeride", "rest") or s.power_low is None:
            continue
        if s.power_low > extreme_power_frac or (s.power_high or 0) > extreme_power_frac:
            continue
        max_zone = max(max_zone, _zone_of(s.power_low, zone_bounds))
        if s.power_high is not None:
            max_zone = max(max_zone, _zone_of(s.power_high, zone_bounds))
    return max_zone


def _classify_freeride_bucket(doc: WorkoutDoc, zone_bounds, extreme_power_frac: float) -> int:
    """Returns 1/2/3 — see the FreeRide classification comment above
    PRIMARY_ZONE_WEIGHT_EXPONENT for the priority order and rationale."""
    short_count, long_block_periodic, all_quiet = _freeride_structural_signals(doc)
    max_zone = _freeride_surrounding_max_zone(doc, zone_bounds, extreme_power_frac)
    if short_count >= FREERIDE_SHORT_BURST_COUNT_MIN:
        return 2
    if max_zone >= 4:
        return 2
    if long_block_periodic:
        return 3
    if max_zone <= 3 and all_quiet:
        return 1
    return 3


def compute_metrics(doc: WorkoutDoc, zone_bounds=None, tuning=None) -> Metrics:
    zone_bounds = zone_bounds or ZONE_BOUNDS
    t = {**DEFAULT_TUNING, **(tuning or {})}
    m = Metrics(num_blocks=doc.num_blocks, num_intervals=doc.num_intervals)
    m.content_hash = compute_content_hash(doc)

    if not doc.steps or all(s.kind == "rest" for s in doc.steps):
        m.is_rest_day = True
        m.structure_type = "rest"
        m.primary_type = "recovery"
        m.sub_types.append("is_rest_day")
        return m

    m.duration_sec = int(sum(s.duration_sec for s in doc.steps))
    m.has_freeride = any(s.kind == "freeride" for s in doc.steps)
    # "FTP test" as its own primary_type, overriding whatever the zone-based
    # classification below would say (owner spec, 2026-09): title carries the
    # word "ftp test" (case-insensitive substring) AND the file has a Free
    # Ride section (the actual test effort — ERG unlocked, ramp-rate free).
    is_ftp_test = m.has_freeride and "ftp test" in (doc.name or "").lower()
    m.has_maxeffort = any(s.kind == "maxeffort" for s in doc.steps)
    m.has_ramp = any(s.kind == "ramp" for s in doc.steps)
    m.has_warmup = any(s.kind == "warmup" for s in doc.steps)
    m.has_cooldown = any(s.kind == "cooldown" for s in doc.steps)
    m.has_cadence = any(s.cadence_low or s.cadence_high for s in doc.steps)
    for s in doc.steps:
        for c in (s.cadence_low, s.cadence_high):
            if not c:
                continue
            if c >= t["high_cadence_rpm"]:
                m.has_high_cadence = True
            if c <= t["low_cadence_rpm"]:
                m.has_low_cadence = True

    # Power-per-second profile, built only from steps with a defined target.
    # FreeRide/MaxEffort/rest are excluded (no %FTP target to compute NP/TSS
    # from) but still counted in duration_sec above — except FreeRide steps
    # in bucket ①/② below, which get a locally-computed effective power
    # (doc.steps itself is never mutated, so re-running compute_metrics on
    # the same doc stays idempotent).
    freeride_bucket = _classify_freeride_bucket(doc, zone_bounds, t["extreme_power_frac"]) if m.has_freeride else None

    profile: List[float] = []
    zone_seconds: Dict[int, float] = {}
    zone_weight: Dict[int, float] = {}
    main_set_zone_weight: Dict[int, float] = {}
    sweet_spot_seconds = 0.0
    interval_seconds = 0.0
    on_seconds = 0.0
    off_seconds = 0.0
    structure_denominator_seconds = 0.0
    any_estimated = False

    for s in doc.steps:
        power_low, power_high, power_estimated = s.power_low, s.power_high, s.power_estimated
        if s.kind == "freeride" and power_low is None and freeride_bucket in (1, 2):
            if freeride_bucket == 1:
                power_low = power_high = FREERIDE_BUCKET1_FRAC
            else:
                power_low = power_high = _freeride_bucket2_value(s.duration_sec)
            power_estimated = True
        if power_low is None or s.duration_sec <= 0:
            continue
        if power_low > t["extreme_power_frac"] or power_high > t["extreme_power_frac"]:
            m.has_max_sprint = True
            continue
        n = int(round(s.duration_sec))
        if n <= 0:
            continue
        if power_estimated:
            any_estimated = True
        is_main_set = s.kind not in NON_WORK_KINDS
        if s.kind not in NON_WORK_KINDS:
            structure_denominator_seconds += n
        for i in range(n):
            frac = i / n
            p = power_low + (power_high - power_low) * frac
            profile.append(p)
            z = _zone_of(p, zone_bounds)
            zone_seconds[z] = zone_seconds.get(z, 0.0) + 1
            zone_weight[z] = zone_weight.get(z, 0.0) + p ** PRIMARY_ZONE_WEIGHT_EXPONENT
            if is_main_set:
                main_set_zone_weight[z] = main_set_zone_weight.get(z, 0.0) + p ** PRIMARY_ZONE_WEIGHT_EXPONENT
            if t["sweet_spot_low"] <= p <= t["sweet_spot_high"]:
                sweet_spot_seconds += 1
        if s.kind in ("interval_on", "interval_off"):
            interval_seconds += s.duration_sec
            if s.kind == "interval_on":
                on_seconds += s.duration_sec
            else:
                off_seconds += s.duration_sec

    m.powered_duration_sec = len(profile)
    m.power_estimated = any_estimated

    if not profile:
        m.structure_type = "steady"
        m.primary_type = "ftp_test" if is_ftp_test else "mixed"
        return m

    m.avg_intensity = sum(profile) / len(profile)

    # NP = 4th-root of the mean of a rolling-30s average power, raised to
    # the 4th power (standard normalized-power definition).
    window = 30
    if len(profile) < window:
        m.np_frac = m.avg_intensity
    else:
        p4 = [p ** 4 for p in profile]
        running = sum(p4[:window])
        rolling_means = [running / window]
        for i in range(window, len(p4)):
            running += p4[i] - p4[i - window]
            rolling_means.append(running / window)
        m.np_frac = (sum(rolling_means) / len(rolling_means)) ** 0.25

    m.if_frac = m.np_frac
    hours = m.powered_duration_sec / 3600.0
    m.tss = (m.if_frac ** 2) * hours * 100.0

    if interval_seconds > 0 and off_seconds > 0:
        m.work_rest_ratio = on_seconds / off_seconds

    # Denominator is main-set time only (warmup/cooldown pulled out per the
    # owner's instruction); falls back to total powered time in the edge
    # case of a workout that's nothing but warmup/cooldown.
    denom = structure_denominator_seconds or m.powered_duration_sec
    vi = (m.np_frac / m.avg_intensity) if m.avg_intensity else 1.0
    if interval_seconds > 0:
        ratio = interval_seconds / denom
        # A real <IntervalsT> set can still fall under the time-ratio
        # threshold when several reps are separated by long standalone
        # rest blocks *between* sets (e.g. 3 sets of 6x15s sprints, each
        # set followed by 4min easy as a plain <SteadyState>, not part of
        # any IntervalsT) — that recovery dilutes the ratio even though the
        # workout is unmistakably an interval session. A high VI (huge
        # swings between sprint and recovery power) catches those.
        if ratio >= t["interval_structure_threshold"] or vi >= t["vi_interval_threshold"]:
            m.structure_type = "interval"
        else:
            m.structure_type = "mixed"
    else:
        # No <IntervalsT> found, but the trace may still be a hand-rolled
        # interval set (see VI_INTERVAL_THRESHOLD above).
        if vi >= t["vi_interval_threshold"]:
            m.structure_type = "interval"
        elif vi >= t["vi_mixed_threshold"]:
            m.structure_type = "mixed"
        else:
            m.structure_type = "steady"

    total_zone_seconds = sum(zone_seconds.values()) or 1
    m.zone_pcts = {z: round(sec / total_zone_seconds * 100, 1) for z, sec in zone_seconds.items()}
    m.sweet_spot_pct = round(sweet_spot_seconds / total_zone_seconds * 100, 1)
    zones_for_primary = main_set_zone_weight or zone_weight
    m.primary_zone = max(zones_for_primary, key=zones_for_primary.get) if zones_for_primary else None
    primary_weight_total = sum(zones_for_primary.values()) or 1
    primary_zone_pcts = {z: w / primary_weight_total * 100 for z, w in zones_for_primary.items()}

    m.primary_type = "ftp_test" if is_ftp_test else _classify_primary_type(m, primary_zone_pcts)
    if m.sweet_spot_pct >= t["sweet_spot_tag_min_pct"]:
        m.sub_types.append("sweetspot_loose")
    # Independent of primary_type — coexists with tempo/threshold rather
    # than replacing them (see _is_sweetspot_workout).
    if m.primary_type in ("tempo", "threshold") and _is_sweetspot_workout(doc, t):
        m.sub_types.append("sweetspot_tight")
    if m.has_freeride:
        m.sub_types.append("has_freeride")
    if m.has_ramp:
        m.sub_types.append("has_ramp")
    if m.has_maxeffort:
        m.sub_types.append("has_maxeffort")
    if m.has_max_sprint:
        m.sub_types.append("has_max_sprint")
    if m.has_cadence:
        m.sub_types.append("has_cadence")
    if m.has_high_cadence:
        m.sub_types.append("has_high_cadence")
    if m.has_low_cadence:
        m.sub_types.append("has_low_cadence")

    return m


def _classify_primary_type(m: Metrics, primary_zone_pcts: Dict[int, float]) -> str:
    # `mixed` requires structure_type=="mixed" AND no single zone dominating
    # the *main-set* training stimulus — primary_zone_pcts is the same
    # main-set-only, power^4-weighted distribution primary_zone itself is
    # picked from (2026-09: previously checked m.zone_pcts, the raw
    # all-inclusive time-based distribution used for the zone-distribution
    # chart; that let a workout's warmup/cooldown/recovery time alone push
    # it into "mixed" even when the actual work was clearly one zone — see
    # e.g. "Vo2 increase climb", whose long between-effort recoveries gave
    # Z1 36.7% of raw time versus Z5's 40.3%, while the main-set-weighted
    # view was 84.9% Z5).
    if m.structure_type == "mixed" and len([z for z, p in primary_zone_pcts.items() if p >= 25]) >= 2:
        return "mixed"
    zone_to_type = {
        1: "recovery",
        2: "endurance",
        3: "tempo",
        4: "threshold",
        5: "vo2",
        6: "anaerobic",
    }
    # No "sweetspot" here anymore — it's the independent `sweetspot` tag
    # (see compute_metrics), so it can coexist with tempo/threshold instead
    # of replacing them.
    result = zone_to_type.get(m.primary_zone, "mixed")
    if result == "recovery" and m.duration_sec > RECOVERY_MAX_DURATION_SEC:
        return "endurance"
    return result
