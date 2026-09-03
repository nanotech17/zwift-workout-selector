"""F1: walks a directory of .zwo files, analyzes each, and upserts results
into the catalog DB. Re-running only re-analyzes files whose content hash
changed (source_hash), per workout-selector.md §5 F1."""
import hashlib
import json
import os
import sqlite3
import time
from dataclasses import asdict
from typing import Optional

from . import db as dbmod
from . import settings as settingsmod
from .metrics import compute_metrics
from .zwo_parser import ZwoParseError, parse_zwo


def _hash_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _find_zwo_files(root_dir: str):
    for cur, _dirs, files in os.walk(root_dir):
        for f in files:
            if f.lower().endswith(".zwo"):
                yield os.path.join(cur, f)


def _remove_deleted(conn: sqlite3.Connection, root_dir: str) -> int:
    """Drops catalog rows for files that no longer exist under root_dir
    (renamed/deleted since the last scan) — without this, a stale row's
    filepath 404s on every /steps re-parse and its profile chart silently
    renders blank (found investigating "The Gorby..." 2026-09). A workout
    with an active delivery is left in place even if its file is gone, so
    the local record needed to see/cancel that delivery isn't lost."""
    root_abs = os.path.abspath(root_dir) + os.sep
    removed = 0
    for row in conn.execute("SELECT id, filepath FROM workouts").fetchall():
        path_abs = os.path.abspath(row["filepath"])
        if not path_abs.startswith(root_abs) or os.path.exists(path_abs):
            continue
        has_active_delivery = conn.execute(
            "SELECT 1 FROM deliveries WHERE workout_id = ? AND status = 'active' LIMIT 1",
            (row["id"],),
        ).fetchone()
        if has_active_delivery:
            continue
        conn.execute("DELETE FROM workouts WHERE id = ?", (row["id"],))
        removed += 1
    return removed


def ingest_directory(root_dir: str, db_path: str, force: bool = False) -> dict:
    conn = dbmod.connect(db_path)
    # Every run rescans the whole tree, so a leftover error row can only mean
    # a *previous* run's problem (fixed since, or the file is gone) —
    # carrying it forward would misreport it as still-current in the
    # settings screen's error list (workout-selector.md §5 F5 settings work).
    conn.execute("DELETE FROM ingest_errors")
    # Settings-screen-configurable zone boundaries/tuning (C phase) — read
    # once per run, not per file, since they can't change mid-scan.
    zone_bounds = [tuple(b) for b in settingsmod.get_zone_bounds(conn)]
    tuning = settingsmod.get_tuning(conn)
    stats = {"scanned": 0, "analyzed": 0, "skipped_unchanged": 0, "errors": 0, "removed": 0}
    now = time.strftime("%Y-%m-%dT%H:%M:%S")

    for path in _find_zwo_files(root_dir):
        stats["scanned"] += 1
        try:
            source_hash = _hash_file(path)
        except OSError as e:
            _log_error(conn, path, "read error: %s" % e, now)
            stats["errors"] += 1
            continue

        if not force:
            row = conn.execute(
                "SELECT source_hash FROM workouts WHERE filepath = ?", (path,)
            ).fetchone()
            if row is not None and row["source_hash"] == source_hash:
                stats["skipped_unchanged"] += 1
                continue

        try:
            doc = parse_zwo(path)
            m = compute_metrics(doc, zone_bounds=zone_bounds, tuning=tuning)
        except ZwoParseError as e:
            _log_error(conn, path, "parse error: %s" % e, now)
            stats["errors"] += 1
            continue
        except Exception as e:  # noqa: BLE001 - must not abort the whole batch
            _log_error(conn, path, "analysis error: %s" % e, now)
            stats["errors"] += 1
            continue

        _upsert_workout(conn, path, source_hash, doc, m, now)
        stats["analyzed"] += 1

    stats["removed"] = _remove_deleted(conn, root_dir)

    conn.commit()
    conn.close()
    return stats


def _log_error(conn: sqlite3.Connection, path: str, error: str, now: str):
    conn.execute(
        "INSERT INTO ingest_errors (filepath, error, occurred_at) VALUES (?, ?, ?)",
        (path, error, now),
    )


def _upsert_workout(conn, path, source_hash, doc, m, now):
    filename = os.path.basename(path)
    values = (
        path, filename, doc.name, doc.author, doc.description,
        doc.category, doc.subcategory, doc.category_override, doc.sport_type,
        m.duration_sec, m.powered_duration_sec, m.avg_intensity,
        m.np_frac, m.if_frac, m.tss, m.num_blocks, m.num_intervals,
        m.work_rest_ratio, m.structure_type,
        int(m.has_cadence), int(m.has_freeride), int(m.has_ramp), int(m.has_maxeffort),
        int(m.has_max_sprint), int(m.has_high_cadence), int(m.has_low_cadence),
        int(m.has_warmup), int(m.has_cooldown),
        int(m.is_rest_day), m.primary_zone, m.primary_type,
        json.dumps(m.zone_pcts), m.sweet_spot_pct, int(m.power_estimated),
        m.content_hash, source_hash, now, json.dumps(doc.warnings) if doc.warnings else None,
    )
    conn.execute(
        """
        INSERT INTO workouts (
            filepath, filename, name, author, description,
            category, subcategory, category_override, sport_type,
            duration_sec, powered_duration_sec, avg_intensity,
            np_frac, if_frac, tss, num_blocks, num_intervals,
            work_rest_ratio, structure_type,
            has_cadence, has_freeride, has_ramp, has_maxeffort, has_max_sprint,
            has_high_cadence, has_low_cadence, has_warmup, has_cooldown,
            is_rest_day, primary_zone, primary_type,
            zone_pcts, sweet_spot_pct, power_estimated,
            content_hash, source_hash, analyzed_at, parse_warnings
        ) VALUES (?,?,?,?,?, ?,?,?,?, ?,?,?, ?,?,?,?,?, ?,?, ?,?,?,?,?,?,?,?,?, ?,?,?, ?,?,?, ?,?,?,?)
        ON CONFLICT(filepath) DO UPDATE SET
            filename=excluded.filename, name=excluded.name, author=excluded.author,
            description=excluded.description, category=excluded.category,
            subcategory=excluded.subcategory, category_override=excluded.category_override,
            sport_type=excluded.sport_type,
            duration_sec=excluded.duration_sec, powered_duration_sec=excluded.powered_duration_sec,
            avg_intensity=excluded.avg_intensity, np_frac=excluded.np_frac, if_frac=excluded.if_frac,
            tss=excluded.tss, num_blocks=excluded.num_blocks, num_intervals=excluded.num_intervals,
            work_rest_ratio=excluded.work_rest_ratio, structure_type=excluded.structure_type,
            has_cadence=excluded.has_cadence, has_freeride=excluded.has_freeride,
            has_ramp=excluded.has_ramp, has_maxeffort=excluded.has_maxeffort,
            has_max_sprint=excluded.has_max_sprint,
            has_high_cadence=excluded.has_high_cadence, has_low_cadence=excluded.has_low_cadence,
            has_warmup=excluded.has_warmup, has_cooldown=excluded.has_cooldown,
            is_rest_day=excluded.is_rest_day, primary_zone=excluded.primary_zone,
            primary_type=excluded.primary_type, zone_pcts=excluded.zone_pcts,
            sweet_spot_pct=excluded.sweet_spot_pct, power_estimated=excluded.power_estimated,
            content_hash=excluded.content_hash,
            source_hash=excluded.source_hash, analyzed_at=excluded.analyzed_at,
            parse_warnings=excluded.parse_warnings
        """,
        values,
    )
    workout_id = conn.execute(
        "SELECT id FROM workouts WHERE filepath = ?", (path,)
    ).fetchone()["id"]

    conn.execute("DELETE FROM tags WHERE workout_id = ?", (workout_id,))
    seen = set()
    for tag in m.sub_types:
        norm = tag.strip().lower()
        if not norm or norm in seen:
            continue
        seen.add(norm)
        conn.execute(
            "INSERT INTO tags (workout_id, tag, tag_type) VALUES (?, ?, 'sub_type')",
            (workout_id, norm),
        )

    # doc.embedded_tags is the workout file's own free-form <tags> block.
    # For files that went through the workouts.wad conversion (tools/
    # wad_to_zwo.py), that block also has the file's category/
    # categoryOverride values folded in as plain <tag> entries — done
    # before category_override had its own column (2026-09). Anything
    # that now exactly matches doc.category or doc.category_override is
    # dropped here rather than double-stored as a generic tag too.
    category_values = {v for v in (doc.category, doc.category_override) if v}
    for tag in doc.embedded_tags:
        raw = tag.strip().rstrip(",").strip()
        norm = raw.lower()
        if not norm or norm in seen:
            continue
        if raw in category_values:
            continue
        seen.add(norm)
        conn.execute(
            "INSERT INTO tags (workout_id, tag, tag_type) VALUES (?, ?, 'embedded')",
            (workout_id, norm),
        )
