"""Phase 1 CLI: run ingestion and inspect results for spot-checking.

Usage:
    python3 -m workout_selector.cli ingest --dir DIR --db DB_PATH [--force]
    python3 -m workout_selector.cli stats --db DB_PATH
    python3 -m workout_selector.cli show --db DB_PATH --name SUBSTRING
"""
import argparse
import json
import sqlite3
import sys

from . import db as dbmod
from .deliveries import DeliveryError, cancel, list_active, schedule
from .ingest import ingest_directory
from .selection import build_criteria, rank, resolve_targets, search


def _read_key(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def cmd_ingest(args):
    stats = ingest_directory(args.dir, args.db, force=args.force)
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def cmd_stats(args):
    conn = dbmod.connect(args.db)
    total = conn.execute("SELECT COUNT(*) c FROM workouts").fetchone()["c"]
    print("total workouts:", total)
    print("\nby structure_type:")
    for r in conn.execute(
        "SELECT structure_type, COUNT(*) c FROM workouts GROUP BY structure_type ORDER BY c DESC"
    ):
        print(" ", r["structure_type"], r["c"])
    print("\nby primary_type:")
    for r in conn.execute(
        "SELECT primary_type, COUNT(*) c FROM workouts GROUP BY primary_type ORDER BY c DESC"
    ):
        print(" ", r["primary_type"], r["c"])
    print("\npower_estimated (Zone-based fallback used):",
          conn.execute("SELECT COUNT(*) c FROM workouts WHERE power_estimated=1").fetchone()["c"])
    print("\ningest_errors:")
    for r in conn.execute("SELECT filepath, error FROM ingest_errors ORDER BY id"):
        print(" ", r["filepath"], "->", r["error"])
    conn.close()


def cmd_show(args):
    conn = dbmod.connect(args.db)
    rows = conn.execute(
        "SELECT * FROM workouts WHERE name LIKE ? OR filename LIKE ? LIMIT ?",
        ("%%%s%%" % args.name, "%%%s%%" % args.name, args.limit),
    ).fetchall()
    if not rows:
        print("no match for", args.name)
        return
    for r in rows:
        d = dict(r)
        tags = [t["tag"] for t in conn.execute(
            "SELECT tag FROM tags WHERE workout_id=?", (r["id"],)
        )]
        d["tags"] = tags
        print(json.dumps(d, ensure_ascii=False, indent=2))
        print("-" * 60)
    conn.close()


def cmd_select(args):
    conn = dbmod.connect(args.db)
    c = build_criteria(
        duration_min=args.duration_min, duration_max=args.duration_max,
        tss_min=args.tss_min, tss_max=args.tss_max,
        if_min=args.if_min, if_max=args.if_max,
        primary_type=args.primary_type, structure_type=args.structure_type,
        zone=args.zone, zone_min_pct=args.zone_min_pct,
        cadence=args.cadence, high_cadence=args.high_cadence,
        low_cadence=args.low_cadence, freeride=args.freeride,
        warmup=args.warmup, cooldown=args.cooldown,
        sport_type=args.sport_type, tags=args.tags, sub_type=args.sub_type,
        include_duplicates=args.include_duplicates,
    )
    rows = search(conn, c)

    target_duration_sec, target_tss = resolve_targets(
        duration_min=args.duration_min, duration_max=args.duration_max, target_duration=args.target_duration,
        tss_min=args.tss_min, tss_max=args.tss_max, target_tss=args.target_tss,
    )

    top = rank(rows, target_duration_sec, target_tss, limit=args.limit)
    print("matched: %d, showing top %d" % (len(rows), len(top)))
    for r in top:
        print(json.dumps({
            "id": r["id"], "name": r["name"], "filename": r["filename"],
            "duration_min": round(r["duration_sec"] / 60, 1),
            "tss": round(r["tss"], 1) if r["tss"] is not None else None,
            "if": round(r["if_frac"], 3) if r["if_frac"] is not None else None,
            "primary_type": r["primary_type"], "structure_type": r["structure_type"],
            "has_warmup": bool(r["has_warmup"]), "has_cooldown": bool(r["has_cooldown"]),
        }, ensure_ascii=False))
    conn.close()


def cmd_deliver(args):
    conn = dbmod.connect(args.db)
    api_key = _read_key(args.key_file)
    try:
        result = schedule(conn, args.workout_id, args.date, api_key, args.athlete_id, replace=args.replace)
    except DeliveryError as e:
        print("ERROR:", e)
        sys.exit(1)
    print(json.dumps(result, ensure_ascii=False))
    conn.close()


def cmd_cancel_delivery(args):
    conn = dbmod.connect(args.db)
    api_key = _read_key(args.key_file)
    try:
        cancel(conn, args.delivery_id, api_key, args.athlete_id)
    except DeliveryError as e:
        print("ERROR:", e)
        sys.exit(1)
    print("cancelled delivery", args.delivery_id)
    conn.close()


def cmd_deliveries(args):
    conn = dbmod.connect(args.db)
    for r in list_active(conn):
        print(json.dumps(dict(r), ensure_ascii=False))
    conn.close()


def main(argv=None):
    parser = argparse.ArgumentParser(prog="workout_selector.cli")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_ingest = sub.add_parser("ingest", help="scan a directory of .zwo files into the catalog DB")
    p_ingest.add_argument("--dir", required=True)
    p_ingest.add_argument("--db", required=True)
    p_ingest.add_argument("--force", action="store_true", help="re-analyze even unchanged files")
    p_ingest.set_defaults(func=cmd_ingest)

    p_stats = sub.add_parser("stats", help="print aggregate counts from the catalog DB")
    p_stats.add_argument("--db", required=True)
    p_stats.set_defaults(func=cmd_stats)

    p_show = sub.add_parser("show", help="print full analysis for workouts matching a name substring")
    p_show.add_argument("--db", required=True)
    p_show.add_argument("--name", required=True)
    p_show.add_argument("--limit", type=int, default=5)
    p_show.set_defaults(func=cmd_show)

    p_select = sub.add_parser("select", help="search + rank workouts by target duration/TSS (F3)")
    p_select.add_argument("--db", required=True)
    p_select.add_argument("--duration-min", type=float, help="minutes")
    p_select.add_argument("--duration-max", type=float, help="minutes")
    p_select.add_argument("--tss-min", type=float)
    p_select.add_argument("--tss-max", type=float)
    p_select.add_argument("--if-min", type=float)
    p_select.add_argument("--if-max", type=float)
    p_select.add_argument("--primary-type", help="comma-separated, OR'd: recovery,endurance,tempo,threshold,vo2,anaerobic,mixed "
                                                  "(sweet-spot sessions aren't a primary_type value -- filter --sub-type sweetspot_tight instead)")
    p_select.add_argument("--structure-type", help="comma-separated, OR'd: steady,interval,mixed")
    p_select.add_argument("--sub-type", help="comma-separated, AND'd: is_rest_day,sweetspot_loose,sweetspot_tight,"
                                              "has_freeride,has_ramp,has_maxeffort,has_max_sprint,has_cadence,has_high_cadence,has_low_cadence")
    p_select.add_argument("--zone", type=int, help="1-6, used with --zone-min-pct")
    p_select.add_argument("--zone-min-pct", type=float)
    p_select.add_argument("--cadence", choices=["yes", "no", "any"], default="any")
    p_select.add_argument("--high-cadence", choices=["yes", "no", "any"], default="any")
    p_select.add_argument("--low-cadence", choices=["yes", "no", "any"], default="any")
    p_select.add_argument("--freeride", choices=["yes", "no", "any"], default="any")
    p_select.add_argument("--warmup", choices=["yes", "no", "any"], default="any")
    p_select.add_argument("--cooldown", choices=["yes", "no", "any"], default="any")
    p_select.add_argument("--sport-type")
    p_select.add_argument("--tags", help="comma-separated, AND'd")
    p_select.add_argument("--include-duplicates", action="store_true",
                           help="don't collapse workouts with identical structure (same content_hash)")
    p_select.add_argument("--target-duration", type=float, help="minutes; defaults to midpoint of --duration-min/-max")
    p_select.add_argument("--target-tss", type=float, help="defaults to midpoint of --tss-min/-max")
    p_select.add_argument("--limit", type=int, default=10)
    p_select.set_defaults(func=cmd_select)

    p_deliver = sub.add_parser("deliver", help="register a workout on the intervals.icu calendar (F4)")
    p_deliver.add_argument("--db", required=True)
    p_deliver.add_argument("--workout-id", type=int, required=True)
    p_deliver.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_deliver.add_argument("--key-file", default="./intervals_key")
    p_deliver.add_argument("--athlete-id", default="YOUR_ATHLETE_ID")
    p_deliver.add_argument("--replace", action="store_true", help="delete+recreate if that date already has an active delivery")
    p_deliver.set_defaults(func=cmd_deliver)

    p_cancel = sub.add_parser("cancel-delivery", help="remove a delivery from the intervals.icu calendar (F4)")
    p_cancel.add_argument("--db", required=True)
    p_cancel.add_argument("--delivery-id", type=int, required=True)
    p_cancel.add_argument("--key-file", default="./intervals_key")
    p_cancel.add_argument("--athlete-id", default="YOUR_ATHLETE_ID")
    p_cancel.set_defaults(func=cmd_cancel_delivery)

    p_deliveries = sub.add_parser("deliveries", help="list active deliveries")
    p_deliveries.add_argument("--db", required=True)
    p_deliveries.set_defaults(func=cmd_deliveries)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main(sys.argv[1:])
