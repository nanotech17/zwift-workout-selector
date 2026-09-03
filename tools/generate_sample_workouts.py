"""Generates synthetic .zwo sample workouts covering ZWS's searchable option
space (主タイプ/構造/副タイプ/時間/TSS/IF), as a copyright-clean substitute
for real internet-sourced or workouts.wad-extracted files used as demo data.

Every generated file is tagged <tags><tag name="sample"/></tags> (picked up
automatically as an `embedded` tag by ingest.py — no app code change needed)
and, before being written to its final name, is round-tripped through this
repo's own zwo_parser/metrics modules: a candidate is regenerated with fresh
random parameters (up to --retries times) until it actually lands in its
intended primary_type/structure_type/sub_types bucket. This guarantees the
sample data can never silently diverge from the app's real classification
logic (owner decision 2026-09: sample count 150, see conversation record).

Usage:
    .venv/bin/python tools/generate_sample_workouts.py [--out DIR] [--seed N]
"""
import argparse
import os
import random
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workout_selector.zwo_parser import parse_zwo  # noqa: E402
from workout_selector.metrics import compute_metrics  # noqa: E402

DEFAULT_OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sample_workouts")
MAX_RETRIES = 40

PRIMARY_ZONES = {"recovery": 1, "endurance": 2, "tempo": 3, "threshold": 4, "vo2": 5, "anaerobic": 6}
DURATION_TIERS_SEC = {"short": (15 * 60, 30 * 60), "medium": (45 * 60, 75 * 60), "long": (90 * 60, 150 * 60)}
ZONE_BAND = {1: (0.50, 0.58), 2: (0.64, 0.73), 3: (0.80, 0.87), 4: (0.92, 1.02), 5: (1.07, 1.16), 6: (1.22, 1.45)}
MAIN_SET_CAP_SEC = {1: None, 2: None, 3: 60 * 60, 4: 40 * 60, 5: 8 * 60, 6: 4 * 60}
INTERVAL_ON_OFF_SEC = {1: (240, 120), 2: (240, 120), 3: (180, 120), 4: (120, 90), 5: (60, 90), 6: (30, 90)}

PRIMARY_LABEL = {
    "recovery": "Recovery", "endurance": "Endurance", "tempo": "Tempo",
    "threshold": "Threshold", "vo2": "VO2max", "anaerobic": "Anaerobic", "mixed": "Mixed",
}
STRUCTURE_LABEL = {
    "steady": "Steady", "interval": "Interval", "mixed": "Mixed structure", "rest": "Rest day",
}

TITLE_TEMPLATES = [
    "Sample: {primary_en} {structure_en} {dur}min",
    "Sample: {primary_en} type {structure_en} ({dur}min)",
    "Sample: {structure_en} - {primary_en} {dur}min",
]
DESC_TEMPLATE = (
    "Auto-generated sample workout for verifying ZWS's search features. "
    "primary_type={primary_en} / structure={structure_en} / duration={dur}min / TSS={tss} / IF={iff}. "
    "Not intended to represent a real training effect.\n"
    "ZWSの検索機能を確認するために自動生成したサンプルワークアウトです。"
    "主タイプ={primary_en} / 構造={structure_en} / 時間={dur}分 / TSS={tss} / IF={iff}。"
    "実在のトレーニング効果を意図したものではありません。"
)
REST_TITLE = "Sample: Rest Day #{n}"
REST_DESC = (
    "Auto-generated rest-day sample for verifying ZWS's search features.\n"
    "ZWSの検索機能を確認するために自動生成した休養日サンプルです。"
)


# --- XML step builders ------------------------------------------------

def e(tag, attrs, children=()):
    el = ET.Element(tag, {k: str(v) for k, v in attrs.items()})
    for c in children:
        el.append(c)
    return el


def e_warmup(dur, lo, hi, cadence=None):
    a = {"Duration": int(dur), "PowerLow": f"{lo:.3f}", "PowerHigh": f"{hi:.3f}"}
    if cadence:
        a["Cadence"] = int(cadence)
    return e("Warmup", a)


def e_cooldown(dur, hi, lo, cadence=None):
    a = {"Duration": int(dur), "PowerLow": f"{hi:.3f}", "PowerHigh": f"{lo:.3f}"}
    if cadence:
        a["Cadence"] = int(cadence)
    return e("Cooldown", a)


def e_steady(dur, power, cadence=None):
    a = {"Duration": int(dur), "Power": f"{power:.3f}"}
    if cadence:
        a["Cadence"] = int(cadence)
    return e("SteadyState", a)


def e_intervals(repeat, on_dur, on_power, off_dur, off_power, cadence=None, cadence_rest=None):
    a = {"Repeat": int(repeat), "OnDuration": int(on_dur), "OffDuration": int(off_dur),
         "OnPower": f"{on_power:.3f}", "OffPower": f"{off_power:.3f}"}
    if cadence:
        a["Cadence"] = int(cadence)
    if cadence_rest:
        a["CadenceResting"] = int(cadence_rest)
    return e("IntervalsT", a)


def e_ramp(dur, lo, hi):
    return e("Ramp", {"Duration": int(dur), "PowerLow": f"{lo:.3f}", "PowerHigh": f"{hi:.3f}"})


def e_freeride(dur):
    return e("FreeRide", {"Duration": int(dur)})


def e_maxeffort(dur):
    return e("MaxEffort", {"Duration": int(dur)})


def e_restday():
    return e("RestDay", {"Duration": 0})


def build_zwo(name, description, steps):
    root = ET.Element("workout_file")
    ET.SubElement(root, "author").text = "ZWS Sample Generator"
    ET.SubElement(root, "name").text = name
    ET.SubElement(root, "description").text = description
    ET.SubElement(root, "sportType").text = "bike"
    tags_el = ET.SubElement(root, "tags")
    ET.SubElement(tags_el, "tag", {"name": "sample"})
    workout_el = ET.SubElement(root, "workout")
    for s in steps:
        workout_el.append(s)
    return root


# --- structure-family builders -----------------------------------------

def _cadence_for(flags, rng):
    if flags.get("high_cadence"):
        return rng.randint(102, 112)
    if flags.get("low_cadence"):
        return rng.randint(52, 65)
    return None


def _extra_flag_steps(flags, rng, ref_power):
    """freeride/ramp/maxeffort/max_sprint blocks shared by every structure
    family — factored out after the first draft silently dropped these for
    the mixed/sweetspot builders, which left their has_* sub_type unmet."""
    steps = []
    if flags.get("freeride"):
        steps.append(e_freeride(rng.randint(180, 420)))
    if flags.get("ramp"):
        steps.append(e_ramp(rng.randint(120, 300), ref_power * 0.8, ref_power))
    if flags.get("maxeffort"):
        steps.append(e_maxeffort(rng.randint(15, 30)))
    if flags.get("max_sprint"):
        steps.append(e_steady(10, rng.uniform(3.0, 3.3)))
    return steps


def make_steady(zone, total_sec, flags, rng):
    power = rng.uniform(*ZONE_BAND[zone])
    has_warmup = flags.get("has_warmup", True)
    has_cooldown = flags.get("has_cooldown", True)
    cap = MAIN_SET_CAP_SEC[zone]
    main_sec = total_sec * 0.7
    if cap and main_sec > cap:
        # A short capped main block (VO2/anaerobic) would otherwise be
        # dwarfed by warmup/cooldown sized off the full (long) tier target,
        # which drags NP/avg apart enough to misclassify structure_type as
        # "mixed" — size warmup/cooldown off the actual main block instead.
        main_sec = cap
        warm_sec = int(main_sec * 0.3) if has_warmup else 0
        cool_sec = int(main_sec * 0.3) if has_cooldown else 0
    else:
        warm_sec = int(total_sec * 0.15) if has_warmup else 0
        cool_sec = int(total_sec * 0.15) if has_cooldown else 0
        main_sec = total_sec - warm_sec - cool_sec
    cadence = _cadence_for(flags, rng)
    steps = []
    if warm_sec:
        steps.append(e_warmup(warm_sec, 0.5, min(power, 0.75)))
    steps.append(e_steady(main_sec, power, cadence))
    if flags.get("freeride"):
        steps.append(e_freeride(rng.randint(180, 420)))
    if flags.get("ramp"):
        steps.append(e_ramp(rng.randint(120, 300), power * 0.8, power))
    if flags.get("maxeffort"):
        steps.append(e_maxeffort(rng.randint(15, 30)))
    if flags.get("max_sprint"):
        steps.append(e_steady(10, rng.uniform(3.0, 3.3)))
    if cool_sec:
        steps.append(e_cooldown(cool_sec, min(power, 0.75), 0.5))
    return steps


def make_sweetspot_tight(total_sec, flags, rng):
    """Dedicated construction for the strict sweetspot_tight tag: one long
    (>=20min work) block held at 88-92%FTP (inside the 85-95% SS band, and
    high enough above the 60%FTP recovery floor / low enough below the
    105%FTP "high" ceiling that the ratio tests in
    metrics._is_sweetspot_workout clear comfortably), main-set-only."""
    power = rng.uniform(0.90, 0.93)  # stays clear of the zone3/4 boundary (~0.895)
    warm_sec = int(total_sec * 0.15)
    cool_sec = int(total_sec * 0.15)
    main_sec = max(20 * 60 + 60, total_sec - warm_sec - cool_sec)
    cadence = _cadence_for(flags, rng)
    steps = [e_warmup(warm_sec, 0.5, 0.75), e_steady(main_sec, power, cadence)]
    steps += _extra_flag_steps(flags, rng, power)
    steps.append(e_cooldown(cool_sec, 0.75, 0.5))
    return steps


def make_sweetspot_loose(total_sec, flags, rng):
    """Looser than make_sweetspot_tight: only needs >=15% of total powered
    time in the 88-94%FTP band (sweet_spot_tag_min_pct), no minimum-minutes
    or high-power-ratio requirement — a single main block covering roughly
    half the workout comfortably clears that bar regardless of duration
    tier."""
    power = rng.uniform(0.88, 0.94)
    warm_sec = int(total_sec * 0.2)
    cool_sec = int(total_sec * 0.2)
    main_sec = total_sec - warm_sec - cool_sec
    cadence = _cadence_for(flags, rng)
    steps = [e_warmup(warm_sec, 0.5, 0.75), e_steady(main_sec, power, cadence)]
    steps += _extra_flag_steps(flags, rng, power)
    steps.append(e_cooldown(cool_sec, 0.75, 0.5))
    return steps


def make_interval(zone, total_sec, flags, rng):
    on_power = rng.uniform(*ZONE_BAND[zone])
    off_power = rng.uniform(0.45, 0.55)
    on_dur, off_dur = INTERVAL_ON_OFF_SEC[zone]
    warm_sec = int(total_sec * 0.12)
    cool_sec = int(total_sec * 0.12)
    remain = total_sec - warm_sec - cool_sec
    cycle = on_dur + off_dur
    repeat = max(3, int(remain // cycle))
    cadence = _cadence_for(flags, rng)
    steps = [e_warmup(warm_sec, 0.5, min(on_power, 0.75))]
    steps.append(e_intervals(repeat, on_dur, on_power, off_dur, off_power, cadence))
    if flags.get("freeride"):
        steps.append(e_freeride(rng.randint(180, 300)))
    if flags.get("ramp"):
        steps.append(e_ramp(rng.randint(120, 240), off_power, on_power))
    if flags.get("maxeffort"):
        steps.append(e_maxeffort(rng.randint(15, 30)))
    if flags.get("max_sprint"):
        steps.append(e_steady(10, rng.uniform(3.0, 3.3)))
    steps.append(e_cooldown(cool_sec, min(on_power, 0.75), 0.5))
    return steps


def make_mixed_two_zone(total_sec, flags, rng):
    """For primary_type="mixed" specs (no single dominant zone): two plain
    SteadyState blocks at different zone powers, no IntervalsT at all, sized
    so each ends up with a comparable power^4-weighted time share (metrics.py
    requires >=2 zones at >=25% of the main-set-weighted split) while the
    resulting VI still lands under vi_interval_threshold so structure_type
    reads "mixed" rather than "interval"."""
    # Adjacent zones + a near-50/50 time split keep both weighted shares
    # above the 25% "mixed primary_type" floor despite power^4 weighting
    # (e.g. zone3/zone4 at 50/50 duration still gives ~35/65 weighted share,
    # not a near-total washout the way a zone1/zone6 pairing would).
    zone_a = rng.randint(1, 5)
    zone_b = zone_a + 1
    power_a = rng.uniform(*ZONE_BAND[zone_a])
    power_b = rng.uniform(*ZONE_BAND[zone_b])
    warm_sec = int(total_sec * 0.12)
    cool_sec = int(total_sec * 0.12)
    main_budget = total_sec - warm_sec - cool_sec
    split = rng.uniform(0.45, 0.55)
    sec_a = max(60, int(main_budget * split))
    sec_b = max(60, main_budget - sec_a)
    cadence = _cadence_for(flags, rng)
    blocks = [e_steady(sec_a, power_a, cadence), e_steady(sec_b, power_b, cadence)]
    if rng.random() < 0.5:
        blocks.reverse()
    steps = [e_warmup(warm_sec, 0.5, min(power_a, power_b, 0.75))] + blocks
    if flags.get("freeride"):
        steps.append(e_freeride(rng.randint(180, 300)))
    if flags.get("ramp"):
        steps.append(e_ramp(rng.randint(120, 240), power_a, power_b))
    if flags.get("maxeffort"):
        steps.append(e_maxeffort(rng.randint(15, 30)))
    if flags.get("max_sprint"):
        steps.append(e_steady(10, rng.uniform(3.0, 3.3)))
    steps.append(e_cooldown(cool_sec, min(power_a, power_b, 0.75), 0.5))
    return steps


def make_mixed(zone, total_sec, flags, rng):
    """A short IntervalsT block (well under 60% of main-set time) plus a
    separate long SteadyState block at a different power, so that neither
    the interval-time-ratio nor a too-high VI trips structure_type to
    "interval" outright (metrics.py: ratio<threshold AND vi<vi_interval_
    threshold -> "mixed"). Random power/duration draws differ every retry;
    the caller's validate-and-retry loop keeps whichever draw actually lands
    in "mixed" per the real classifier rather than a hand-derived formula."""
    if zone is None:
        return make_mixed_two_zone(total_sec, flags, rng)
    warm_sec = int(total_sec * 0.12)
    cool_sec = int(total_sec * 0.12)
    main_budget = total_sec - warm_sec - cool_sec
    int_power = rng.uniform(*ZONE_BAND[min(zone + 1, 6)])
    steady_power = rng.uniform(*ZONE_BAND[zone])
    on_dur, off_dur = 60, 60
    int_block_sec = int(main_budget * rng.uniform(0.15, 0.35))
    repeat = max(2, int_block_sec // (on_dur + off_dur))
    steady_sec = max(60, main_budget - repeat * (on_dur + off_dur))
    cadence = _cadence_for(flags, rng)
    steps = [e_warmup(warm_sec, 0.5, min(steady_power, 0.75))]
    if rng.random() < 0.5:
        steps.append(e_intervals(repeat, on_dur, int_power, off_dur, steady_power * 0.9, cadence))
        steps.append(e_steady(steady_sec, steady_power, cadence))
    else:
        steps.append(e_steady(steady_sec, steady_power, cadence))
        steps.append(e_intervals(repeat, on_dur, int_power, off_dur, steady_power * 0.9, cadence))
    if flags.get("freeride"):
        steps.append(e_freeride(rng.randint(180, 300)))
    if flags.get("ramp"):
        steps.append(e_ramp(rng.randint(120, 240), steady_power, int_power))
    if flags.get("maxeffort"):
        steps.append(e_maxeffort(rng.randint(15, 30)))
    if flags.get("max_sprint"):
        steps.append(e_steady(10, rng.uniform(3.0, 3.3)))
    steps.append(e_cooldown(cool_sec, min(steady_power, 0.75), 0.5))
    return steps


# --- spec table ----------------------------------------------------------

def build_specs():
    specs = []
    zones = list(PRIMARY_ZONES)
    tiers = list(DURATION_TIERS_SEC)

    # A: 6 zones x {steady,interval} x 3 tiers x 2 variants = 72
    for zname in zones:
        for structure in ("steady", "interval"):
            for tier in tiers:
                for variant in range(2):
                    specs.append({"primary_type": zname, "structure_type": structure, "tier": tier})

    # B: primary_type=mixed x 3 tiers x 4 variants = 12
    for tier in tiers:
        for _ in range(4):
            specs.append({"primary_type": "mixed", "structure_type": "mixed", "tier": tier})

    # C: rest days = 12
    for _ in range(12):
        specs.append({"is_rest_day": True})

    # D: sweetspot_tight reinforcement (threshold/steady) = 10
    for i in range(10):
        specs.append({"primary_type": "threshold", "structure_type": "steady",
                       "tier": tiers[i % 3], "force_sweetspot_tight": True})

    # E: sweetspot_loose reinforcement = 10. Primary_type isn't pinned here:
    # sweet_spot_pct is a plain 88-94%FTP time share independent of
    # primary_type/structure_type, and forcing a *specific* target zone on
    # top of it is only physically consistent for tempo/threshold anyway
    # (that band straddles their shared boundary) — so this group just
    # verifies the tag fires and reports whichever zone the classifier picks.
    for i in range(10):
        specs.append({"primary_type": "threshold", "structure_type": "steady",
                       "tier": tiers[i % 3], "force_sweetspot_loose": True, "skip_primary_check": True})

    # F: structure_type=mixed with a concrete dominant zone = 6 zones x 2 = 12
    for zname in zones:
        for i in range(2):
            specs.append({"primary_type": zname, "structure_type": "mixed", "tier": tiers[i % 3]})

    # G: filler for extra continuous-value spread, up to 150
    i = 0
    while len(specs) < 150:
        specs.append({"primary_type": zones[i % 6], "structure_type": "steady" if i % 2 == 0 else "interval",
                       "tier": tiers[i % 3]})
        i += 1

    # deterministic flag cycling (skip rest days) so each optional sub_type
    # gets a comparable, guaranteed share rather than leaving it to chance.
    flag_cycle = [None, "high_cadence", "low_cadence", "freeride", "ramp", "maxeffort", "max_sprint"]
    idx = 0
    for spec in specs:
        if spec.get("is_rest_day"):
            continue
        flags = {}
        f = flag_cycle[idx % len(flag_cycle)]
        if f:
            flags[f] = True
        if idx % 5 == 0:
            flags["has_warmup"] = False
        if idx % 7 == 0:
            flags["has_cooldown"] = False
        spec["flags"] = flags
        idx += 1

    return specs


# --- generation + validation loop ----------------------------------------

def generate_one(spec, rng, tmp_path):
    if spec.get("is_rest_day"):
        for _ in range(1):
            steps = [e_restday()]
            root = build_zwo("tmp", "tmp", steps)
            ET.ElementTree(root).write(tmp_path, encoding="unicode", xml_declaration=False)
            m = compute_metrics(parse_zwo(tmp_path))
            return steps, m, 0, True

    zone = PRIMARY_ZONES.get(spec["primary_type"])
    tier = spec["tier"]
    flags = spec.get("flags", {})
    last = None
    for attempt in range(MAX_RETRIES):
        total_sec = rng.randint(*DURATION_TIERS_SEC[tier])
        if spec.get("force_sweetspot_tight"):
            steps = make_sweetspot_tight(total_sec, flags, rng)
        elif spec.get("force_sweetspot_loose"):
            steps = make_sweetspot_loose(total_sec, flags, rng)
        elif spec["structure_type"] == "steady":
            steps = make_steady(zone, total_sec, flags, rng)
        elif spec["structure_type"] == "interval":
            steps = make_interval(zone, total_sec, flags, rng)
        else:
            steps = make_mixed(zone, total_sec, flags, rng)

        root = build_zwo("tmp", "tmp", steps)
        ET.ElementTree(root).write(tmp_path, encoding="unicode", xml_declaration=False)
        doc = parse_zwo(tmp_path)
        m = compute_metrics(doc)
        last = (steps, m, total_sec, False)

        if spec.get("skip_primary_check"):
            ok = True
        else:
            ok = m.primary_type == spec["primary_type"] and m.structure_type == spec["structure_type"]
        if spec.get("force_sweetspot_tight"):
            ok = ok and "sweetspot_tight" in m.sub_types
        if spec.get("force_sweetspot_loose"):
            ok = ok and "sweetspot_loose" in m.sub_types
        for want_flag, want_sub in (("high_cadence", "has_high_cadence"), ("low_cadence", "has_low_cadence"),
                                     ("freeride", "has_freeride"), ("ramp", "has_ramp"),
                                     ("maxeffort", "has_maxeffort"), ("max_sprint", "has_max_sprint")):
            if flags.get(want_flag):
                ok = ok and want_sub in m.sub_types
        if ok:
            return steps, m, total_sec, True
    return last[0], last[1], last[2], False


def title_desc(spec, m, idx, rng):
    if spec.get("is_rest_day"):
        return REST_TITLE.format(n=idx), REST_DESC
    # Labels come from the achieved metrics (m), not the spec's originally
    # intended target — the two can differ for the handful of specs that
    # didn't converge within MAX_RETRIES (see the mismatch report), and the
    # title/description must describe the file that's actually on disk.
    p_en = PRIMARY_LABEL[m.primary_type]
    s_en = STRUCTURE_LABEL[m.structure_type]
    dur_min = round(m.duration_sec / 60)
    tpl = TITLE_TEMPLATES[idx % len(TITLE_TEMPLATES)]
    title = tpl.format(primary_en=p_en, structure_en=s_en, dur=dur_min)
    desc = DESC_TEMPLATE.format(
        primary_en=p_en, structure_en=s_en, dur=dur_min,
        tss=round(m.tss) if m.tss is not None else "-",
        iff=round(m.if_frac, 2) if m.if_frac is not None else "-",
    )
    return title, desc


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--seed", type=int, default=20260903)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    rng = random.Random(args.seed)
    tmp_path = os.path.join(args.out, "_tmp_candidate.zwo")

    specs = build_specs()
    coverage = {"primary_type": {}, "structure_type": {}, "sub_types": {}}
    mismatches = []
    durations, tss_vals = [], []

    for idx, spec in enumerate(specs):
        steps, m, total_sec, matched = generate_one(spec, rng, tmp_path)
        if not matched:
            mismatches.append((idx, spec, m.primary_type, m.structure_type))

        title, desc = title_desc(spec, m, idx, rng)
        root = build_zwo(title, desc, steps)
        fname = f"sample_{idx:03d}_{m.primary_type}_{m.structure_type}.zwo"
        out_path = os.path.join(args.out, fname)
        ET.ElementTree(root).write(out_path, encoding="unicode", xml_declaration=False)

        coverage["primary_type"][m.primary_type] = coverage["primary_type"].get(m.primary_type, 0) + 1
        coverage["structure_type"][m.structure_type] = coverage["structure_type"].get(m.structure_type, 0) + 1
        for st in m.sub_types:
            coverage["sub_types"][st] = coverage["sub_types"].get(st, 0) + 1
        if m.duration_sec:
            durations.append(m.duration_sec)
        if m.tss is not None:
            tss_vals.append(m.tss)

    if os.path.exists(tmp_path):
        os.remove(tmp_path)

    print(f"generated {len(specs)} files -> {args.out}")
    print("primary_type:", coverage["primary_type"])
    print("structure_type:", coverage["structure_type"])
    print("sub_types:", coverage["sub_types"])
    if durations:
        print(f"duration_min: {min(durations)//60}-{max(durations)//60} (avg {sum(durations)//len(durations)//60})")
    if tss_vals:
        print(f"tss: {min(tss_vals):.0f}-{max(tss_vals):.0f} (avg {sum(tss_vals)/len(tss_vals):.0f})")
    if mismatches:
        print(f"\n{len(mismatches)} spec(s) did not converge within {MAX_RETRIES} retries (kept closest attempt):")
        for idx, spec, actual_p, actual_s in mismatches:
            print(f"  #{idx}: wanted {spec.get('primary_type')}/{spec.get('structure_type')} "
                  f"-> got {actual_p}/{actual_s}")


if __name__ == "__main__":
    main()
