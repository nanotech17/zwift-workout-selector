"""Phase 4: Web console backend (workout-selector.md §5 F5).

Run with:
    .venv/bin/uvicorn workout_selector.web:app --host 0.0.0.0 --port 8000

Config via env vars (all optional, defaults match the rest of the app):
    WS_DB_PATH        default ./data/catalog.db
    WS_INTERVALS_KEY  default ./intervals_key
    WS_ATHLETE_ID     default YOUR_ATHLETE_ID
    WS_DEMO_MODE      default unset (off). Set to "1" for a read-only demo
                      deployment (e.g. Cloud Run): all mutating endpoints
                      return 403, and GET /api/settings reports demo_mode
                      so the frontend can hide/disable the corresponding UI.
"""
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import db as dbmod
from . import intervals_api as api
from . import settings as settingsmod
from .deliveries import DeliveryError, cancel as cancel_delivery, list_active, schedule, sync_active
from .ingest import ingest_directory
from .selection import build_criteria, rank, resolve_targets, search, sort_field_rows
from .zwo_parser import ZwoParseError, parse_zwo

DB_PATH = os.environ.get("WS_DB_PATH", "./data/catalog.db")
KEY_FILE = os.environ.get("WS_INTERVALS_KEY", "./intervals_key")
# Seed default for the first run only — once set, the settings screen's
# value (in the settings table) takes over; see _athlete_id.
ATHLETE_ID_ENV_DEFAULT = os.environ.get("WS_ATHLETE_ID", "YOUR_ATHLETE_ID")
DEMO_MODE = os.environ.get("WS_DEMO_MODE") == "1"
STATIC_DIR = Path(__file__).resolve().parent.parent / "web" / "static"

app = FastAPI(title="Zwift Workout Selector")


def _demo_guard() -> None:
    """Blocks every mutating endpoint in a read-only demo deployment. The
    frontend also hides/disables the corresponding controls, but the API
    itself must refuse independently — a demo container is reachable
    directly, without going through the UI."""
    if DEMO_MODE:
        raise HTTPException(403, "demo mode: this action is disabled")


def _conn() -> sqlite3.Connection:
    return dbmod.connect(DB_PATH)


def _athlete_id(conn: sqlite3.Connection) -> str:
    return settingsmod.get_setting(conn, settingsmod.ATHLETE_ID) or ATHLETE_ID_ENV_DEFAULT


def _read_key() -> str:
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        return f.read().strip()


def _key_is_set() -> bool:
    return os.path.isfile(KEY_FILE) and os.path.getsize(KEY_FILE) > 0


def _write_key(value: str) -> None:
    with open(KEY_FILE, "w", encoding="utf-8") as f:
        f.write(value.strip() + "\n")


def _summary(r: dict) -> dict:
    return {
        "id": r["id"], "name": r["name"], "filename": r["filename"],
        "category": r["category"], "subcategory": r["subcategory"],
        "category_override": r["category_override"],
        "duration_min": round(r["duration_sec"] / 60, 1),
        "tss": round(r["tss"], 1) if r["tss"] is not None else None,
        "if": round(r["if_frac"], 3) if r["if_frac"] is not None else None,
        "primary_type": r["primary_type"], "structure_type": r["structure_type"],
        "has_cadence": bool(r["has_cadence"]), "has_high_cadence": bool(r["has_high_cadence"]),
        "has_low_cadence": bool(r["has_low_cadence"]), "has_freeride": bool(r["has_freeride"]),
        "has_warmup": bool(r["has_warmup"]), "has_cooldown": bool(r["has_cooldown"]),
        "sweet_spot_pct": r["sweet_spot_pct"],
        "zone_pcts": json.loads(r["zone_pcts"] or "{}"),
    }


@app.get("/api/tags")
def api_tags():
    # Scoped to 'embedded' only — sub_types (2026-09) get their own
    # dedicated checkboxes in the search form instead of living in this
    # free-text tag cloud, per the owner's tag-cleanup decision.
    conn = _conn()
    rows = conn.execute(
        "SELECT tag, COUNT(*) c FROM tags WHERE tag_type = 'embedded' GROUP BY tag ORDER BY c DESC"
    ).fetchall()
    conn.close()
    return [{"tag": r["tag"], "count": r["c"]} for r in rows]


@app.get("/api/workouts")
def api_search(
    duration_min: Optional[float] = None, duration_max: Optional[float] = None,
    tss_min: Optional[float] = None, tss_max: Optional[float] = None,
    if_min: Optional[float] = None, if_max: Optional[float] = None,
    primary_type: Optional[str] = None, structure_type: Optional[str] = None,
    zone: Optional[int] = None, zone_min_pct: Optional[float] = None,
    cadence: Optional[str] = None, high_cadence: Optional[str] = None,
    low_cadence: Optional[str] = None, freeride: Optional[str] = None,
    warmup: Optional[str] = None, cooldown: Optional[str] = None,
    sport_type: Optional[str] = None, tags: Optional[str] = None,
    tags_mode: Optional[str] = None, sub_type: Optional[str] = None, name_query: Optional[str] = None,
    target_duration: Optional[float] = None, target_tss: Optional[float] = None,
    sort_field: Optional[str] = None, sort_dir: str = "asc", offset: int = 0,
    limit: int = 20, include_duplicates: bool = False, favorites_only: bool = False,
):
    conn = _conn()
    c = build_criteria(
        duration_min=duration_min, duration_max=duration_max,
        tss_min=tss_min, tss_max=tss_max, if_min=if_min, if_max=if_max,
        primary_type=primary_type, structure_type=structure_type,
        zone=zone, zone_min_pct=zone_min_pct,
        cadence=cadence, high_cadence=high_cadence, low_cadence=low_cadence,
        freeride=freeride, warmup=warmup, cooldown=cooldown,
        sport_type=sport_type, tags=tags, tags_mode=tags_mode, sub_type=sub_type, name_query=name_query,
        include_duplicates=include_duplicates, favorites_only=favorites_only,
        # A settings-screen switch, not a per-search checkbox (owner
        # decision 2026-09) — flipped once when moving from demo to
        # production use, rather than re-checked on every search.
        hide_sample=settingsmod.get_hide_sample_tag(conn),
    )
    rows = search(conn, c)
    # Always rank/sort the FULL matched set first, then slice a page out of
    # it (owner decision 2026-09: never let 件数 narrow what's searched —
    # only what's shown at once; 並べ替え needs the same full-set treatment
    # to be correct, not just a reorder of whatever page was fetched).
    if sort_field:
        ordered = sort_field_rows(rows, sort_field, sort_dir)
    else:
        td, tt = resolve_targets(
            duration_min=duration_min, duration_max=duration_max, target_duration=target_duration,
            tss_min=tss_min, tss_max=tss_max, target_tss=target_tss,
        )
        ordered = rank(rows, td, tt, limit=len(rows), direction=sort_dir)
    top = ordered[offset: offset + limit]

    tag_map = {}
    delivery_map = {}
    favorite_ids = set()
    if top:
        ids = [r["id"] for r in top]
        placeholders = ",".join("?" * len(ids))
        for row in conn.execute(
            "SELECT workout_id, tag FROM tags WHERE workout_id IN (%s)" % placeholders, ids
        ):
            tag_map.setdefault(row["workout_id"], []).append(row["tag"])
        # Powers each result card's "配信予定あり" badge — otherwise whether
        # a candidate is already scheduled is only visible inside its own
        # expanded detail panel, easy to miss while comparing candidates
        # (owner audit, 2026-09).
        for row in conn.execute(
            "SELECT workout_id, scheduled_date FROM deliveries WHERE status = 'active' AND workout_id IN (%s)" % placeholders, ids
        ):
            delivery_map.setdefault(row["workout_id"], []).append(row["scheduled_date"])
        favorite_ids = {
            row["workout_id"]
            for row in conn.execute("SELECT workout_id FROM favorites WHERE workout_id IN (%s)" % placeholders, ids)
        }
    conn.close()

    results = []
    for r in top:
        s = _summary(r)
        s["tags"] = sorted(tag_map.get(r["id"], []))
        s["active_deliveries"] = sorted(d for d in delivery_map.get(r["id"], []) if d)
        s["is_favorite"] = r["id"] in favorite_ids
        # Embedded here (rather than left to a per-card GET .../steps call)
        # so a page of results costs one HTTP round trip, not one plus N —
        # the frontend used to fan out a parallel steps fetch per card,
        # which meant a single search burst Cloud Run's containerConcurrency
        # (owner audit, 2026-09). Parse cost is unchanged, just no longer
        # paid once per network round trip.
        try:
            s["steps"] = [
                {
                    "kind": st.kind, "duration_sec": st.duration_sec,
                    "power_low": st.power_low, "power_high": st.power_high,
                    "cadence_low": st.cadence_low, "cadence_high": st.cadence_high,
                }
                for st in parse_zwo(r["filepath"]).steps
            ]
        except ZwoParseError:
            s["steps"] = []
        results.append(s)
    return {"matched": len(rows), "results": results, "offset": offset, "limit": limit}


@app.get("/api/workouts/{workout_id}")
def api_detail(workout_id: int):
    conn = _conn()
    row = conn.execute("SELECT * FROM workouts WHERE id = ?", (workout_id,)).fetchone()
    if row is None:
        conn.close()
        raise HTTPException(404, "workout not found")
    tags = [t["tag"] for t in conn.execute("SELECT tag FROM tags WHERE workout_id = ?", (workout_id,))]
    is_favorite = conn.execute("SELECT 1 FROM favorites WHERE workout_id = ?", (workout_id,)).fetchone() is not None
    conn.close()
    d = dict(row)
    d["zone_pcts"] = json.loads(d["zone_pcts"] or "{}")
    d["tags"] = tags
    d["is_favorite"] = is_favorite
    d["duration_min"] = round(d["duration_sec"] / 60, 1) if d["duration_sec"] else None
    return d


@app.put("/api/workouts/{workout_id}/favorite")
def api_favorite_set(workout_id: int):
    _demo_guard()
    conn = _conn()
    if conn.execute("SELECT 1 FROM workouts WHERE id = ?", (workout_id,)).fetchone() is None:
        conn.close()
        raise HTTPException(404, "workout not found")
    conn.execute(
        "INSERT OR IGNORE INTO favorites (workout_id, created_at) VALUES (?, ?)",
        (workout_id, time.strftime("%Y-%m-%dT%H:%M:%S")),
    )
    conn.commit()
    conn.close()
    return {"is_favorite": True}


@app.delete("/api/workouts/{workout_id}/favorite")
def api_favorite_unset(workout_id: int):
    _demo_guard()
    conn = _conn()
    conn.execute("DELETE FROM favorites WHERE workout_id = ?", (workout_id,))
    conn.commit()
    conn.close()
    return {"is_favorite": False}


@app.get("/api/workouts/{workout_id}/steps")
def api_steps(workout_id: int):
    """Block breakdown for the detail view (§5 F5) — re-parses the .zwo on
    demand rather than duplicating it into the DB; the catalog is local
    files, so this is cheap and always reflects the file's current content.
    """
    conn = _conn()
    row = conn.execute("SELECT filepath FROM workouts WHERE id = ?", (workout_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(404, "workout not found")
    try:
        doc = parse_zwo(row["filepath"])
    except ZwoParseError as e:
        raise HTTPException(500, str(e))
    return [
        {
            "kind": s.kind, "duration_sec": s.duration_sec,
            "power_low": s.power_low, "power_high": s.power_high,
            "cadence_low": s.cadence_low, "cadence_high": s.cadence_high,
        }
        for s in doc.steps
    ]


@app.get("/api/workouts/{workout_id}/download")
def api_download(workout_id: int):
    _demo_guard()
    conn = _conn()
    row = conn.execute("SELECT filepath, filename FROM workouts WHERE id = ?", (workout_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(404, "workout not found")
    if not os.path.exists(row["filepath"]):
        raise HTTPException(404, "file missing on disk")
    return FileResponse(row["filepath"], media_type="application/xml", filename=row["filename"])


class DeliverRequest(BaseModel):
    workout_id: int
    # Enforced (not just documented) since these flow unescaped into the
    # intervals.icu request URL/query string downstream (intervals_api.py) —
    # the UI's <input type="date">/<input type="time"> always produce these
    # exact formats, so this rejects nothing a real client would ever send.
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$")  # YYYY-MM-DD
    time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")  # HH:MM, blank -> midnight
    replace: bool = False


@app.get("/api/deliveries")
def api_deliveries():
    conn = _conn()
    rows = [dict(r) for r in list_active(conn)]
    conn.close()
    return rows


@app.post("/api/deliveries/sync")
def api_deliveries_sync():
    _demo_guard()
    if not _key_is_set():
        raise HTTPException(400, "intervals.icu API key is not set")
    conn = _conn()
    try:
        stats = sync_active(conn, _read_key(), _athlete_id(conn))
    except api.IntervalsApiError as e:
        raise HTTPException(502, str(e))
    finally:
        conn.close()
    return stats


@app.post("/api/deliveries")
def api_deliver(req: DeliverRequest):
    _demo_guard()
    conn = _conn()
    try:
        result = schedule(conn, req.workout_id, req.date, _read_key(), _athlete_id(conn),
                           replace=req.replace, scheduled_time=req.time or None)
    except DeliveryError as e:
        conn.close()
        raise HTTPException(409, str(e))
    conn.close()
    return result


@app.delete("/api/deliveries/{delivery_id}")
def api_cancel(delivery_id: int):
    _demo_guard()
    conn = _conn()
    try:
        cancel_delivery(conn, delivery_id, _read_key(), _athlete_id(conn))
    except DeliveryError as e:
        conn.close()
        raise HTTPException(404, str(e))
    conn.close()
    return {"cancelled": delivery_id}


# --- Settings screen (owner request: configure/operate entirely from the
# browser, no hand-edited config files or CLI). A: data source + rescan.
# B: intervals.icu connection. ---

class SettingsUpdate(BaseModel):
    zwo_dir: Optional[str] = None
    intervals_athlete_id: Optional[str] = None
    hide_sample_tag: Optional[bool] = None


def _settings_payload(conn: sqlite3.Connection) -> dict:
    zwo_dir = settingsmod.get_setting(conn, settingsmod.ZWO_DIR)
    return {
        "zwo_dir": zwo_dir,
        "zwo_dir_exists": bool(zwo_dir) and os.path.isdir(zwo_dir),
        "intervals_athlete_id": _athlete_id(conn),
        "intervals_key_set": _key_is_set(),
        "last_scan": settingsmod.get_setting_json(conn, settingsmod.LAST_SCAN_RESULT),
        "hide_sample_tag": settingsmod.get_hide_sample_tag(conn),
        "demo_mode": DEMO_MODE,
    }


@app.get("/api/settings")
def api_get_settings():
    conn = _conn()
    payload = _settings_payload(conn)
    conn.close()
    return payload


@app.post("/api/settings")
def api_update_settings(req: SettingsUpdate):
    _demo_guard()
    conn = _conn()
    if req.zwo_dir is not None:
        if not os.path.isdir(req.zwo_dir):
            conn.close()
            raise HTTPException(400, "directory not found: %s" % req.zwo_dir)
        settingsmod.set_setting(conn, settingsmod.ZWO_DIR, req.zwo_dir)
    if req.intervals_athlete_id is not None:
        v = req.intervals_athlete_id.strip()
        if not v:
            conn.close()
            raise HTTPException(400, "athlete id must not be empty")
        settingsmod.set_setting(conn, settingsmod.ATHLETE_ID, v)
    if req.hide_sample_tag is not None:
        settingsmod.set_setting_json(conn, settingsmod.HIDE_SAMPLE_TAG, bool(req.hide_sample_tag))
    payload = _settings_payload(conn)
    conn.close()
    return payload


class ApiKeyUpdate(BaseModel):
    api_key: str


@app.post("/api/settings/intervals-key")
def api_update_key(req: ApiKeyUpdate):
    _demo_guard()
    v = req.api_key.strip()
    if not v:
        raise HTTPException(400, "api key must not be empty")
    _write_key(v)
    return {"intervals_key_set": True}


@app.post("/api/settings/test-connection")
def api_test_connection():
    _demo_guard()
    if not _key_is_set():
        raise HTTPException(400, "intervals.icu API key is not set")
    conn = _conn()
    athlete_id = _athlete_id(conn)
    conn.close()
    try:
        profile = api.get_athlete(_read_key(), athlete_id)
    except api.IntervalsApiError as e:
        raise HTTPException(502, str(e))
    return {"ok": True, "athlete_id": athlete_id, "name": profile.get("name")}


@app.post("/api/ingest")
def api_ingest(force: bool = False):
    _demo_guard()
    conn = _conn()
    zwo_dir = settingsmod.get_setting(conn, settingsmod.ZWO_DIR)
    conn.close()
    if not zwo_dir:
        raise HTTPException(400, "zwo_dir is not configured yet — set it in settings first")
    if not os.path.isdir(zwo_dir):
        raise HTTPException(400, "configured zwo_dir not found: %s" % zwo_dir)

    stats = ingest_directory(zwo_dir, DB_PATH, force=force)

    conn = _conn()
    settingsmod.set_setting_json(conn, settingsmod.LAST_SCAN_RESULT, {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"), "force": force, **stats,
    })
    conn.close()
    return stats


@app.get("/api/ingest-errors")
def api_ingest_errors(limit: int = 100):
    conn = _conn()
    rows = [dict(r) for r in conn.execute(
        "SELECT filepath, error, occurred_at FROM ingest_errors ORDER BY id DESC LIMIT ?", (limit,)
    )]
    conn.close()
    return rows


# --- Classification tuning (C phase, starting with zone bounds/colors).
# Saving here only updates the settings table — it does NOT recompute
# anything already in the DB. The frontend is expected to tell the owner to
# rerun "再スキャン(全件)" (POST /api/ingest?force=true) afterwards. ---

class ConfigUpdate(BaseModel):
    zone_bounds: Optional[list] = None
    zone_colors: Optional[dict] = None
    tuning: Optional[dict] = None


def _config_payload(conn: sqlite3.Connection) -> dict:
    return {
        "zone_bounds": settingsmod.get_zone_bounds(conn),
        "zone_colors": settingsmod.get_zone_colors(conn),
        "tuning": settingsmod.get_tuning(conn),
    }


@app.get("/api/config")
def api_get_config():
    conn = _conn()
    payload = _config_payload(conn)
    conn.close()
    return payload


@app.post("/api/config")
def api_update_config(req: ConfigUpdate):
    _demo_guard()
    conn = _conn()
    try:
        if req.zone_bounds is not None:
            settingsmod.set_setting_json(
                conn, settingsmod.CONFIG_ZONE_BOUNDS, settingsmod.validate_zone_bounds(req.zone_bounds)
            )
        if req.zone_colors is not None:
            settingsmod.set_setting_json(
                conn, settingsmod.CONFIG_ZONE_COLORS, settingsmod.validate_zone_colors(req.zone_colors)
            )
        if req.tuning is not None:
            settingsmod.set_setting_json(
                conn, settingsmod.CONFIG_TUNING, settingsmod.validate_tuning(req.tuning)
            )
    except ValueError as e:
        conn.close()
        raise HTTPException(400, str(e))
    payload = _config_payload(conn)
    conn.close()
    return payload


if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
