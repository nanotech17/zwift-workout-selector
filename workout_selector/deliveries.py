"""F4 orchestration: DB bookkeeping around the raw intervals.icu calls in
intervals_api.py (workout-selector.md §5 F4, §8).

Same-day duplicate registration is blocked unless replace=True, in which
case the existing delivery is deleted before the new one is created
("delete -> recreate", §8) — intervals.icu assigns its own event id, so a
client-side upsert isn't possible.
"""
import sqlite3
import time

from . import intervals_api as api


class DeliveryError(Exception):
    pass


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _active_delivery_for_date(conn: sqlite3.Connection, scheduled_date: str):
    return conn.execute(
        "SELECT * FROM deliveries WHERE scheduled_date = ? AND status = 'active'",
        (scheduled_date,),
    ).fetchone()


def schedule(conn: sqlite3.Connection, workout_id: int, scheduled_date: str,
             api_key: str, athlete_id: str, replace: bool = False,
             scheduled_time: str = None) -> dict:
    existing = _active_delivery_for_date(conn, scheduled_date)
    if existing is not None and not replace:
        raise DeliveryError(
            "%s already has an active delivery (delivery id=%d, event id=%s); "
            "pass replace=True to delete and recreate"
            % (scheduled_date, existing["id"], existing["intervals_event_id"])
        )

    workout = conn.execute("SELECT * FROM workouts WHERE id = ?", (workout_id,)).fetchone()
    if workout is None:
        raise DeliveryError("no workout with id %s" % workout_id)
    with open(workout["filepath"], "r", encoding="utf-8", errors="replace") as f:
        zwo_xml = f.read()

    if existing is not None and replace:
        cancel(conn, existing["id"], api_key, athlete_id)

    resp = api.create_event(
        api_key, athlete_id,
        name=workout["name"] or workout["filename"],
        description=workout["description"] or "",
        scheduled_date=scheduled_date,
        zwo_xml=zwo_xml,
        filename=workout["filename"],
        scheduled_time=scheduled_time,
    )
    event_id = str(resp.get("id"))
    now = _now()
    cur = conn.execute(
        "INSERT INTO deliveries (workout_id, intervals_event_id, scheduled_date, status, created_at) "
        "VALUES (?, ?, ?, 'active', ?)",
        (workout_id, event_id, scheduled_date, now),
    )
    conn.commit()
    return {"delivery_id": cur.lastrowid, "event_id": event_id, "scheduled_date": scheduled_date}


def cancel(conn: sqlite3.Connection, delivery_id: int, api_key: str, athlete_id: str) -> None:
    row = conn.execute("SELECT * FROM deliveries WHERE id = ?", (delivery_id,)).fetchone()
    if row is None:
        raise DeliveryError("no delivery with id %s" % delivery_id)
    if row["status"] != "active":
        raise DeliveryError("delivery %s is not active (status=%s)" % (delivery_id, row["status"]))
    api.delete_event(api_key, athlete_id, row["intervals_event_id"])
    conn.execute(
        "UPDATE deliveries SET status='deleted', deleted_at=? WHERE id=?",
        (_now(), delivery_id),
    )
    conn.commit()


def list_active(conn: sqlite3.Connection):
    return conn.execute(
        "SELECT d.*, w.name as workout_name FROM deliveries d "
        "JOIN workouts w ON w.id = d.workout_id WHERE d.status = 'active' "
        "ORDER BY d.scheduled_date"
    ).fetchall()


def sync_active(conn: sqlite3.Connection, api_key: str, athlete_id: str) -> dict:
    """Reconciles locally-active deliveries against intervals.icu's actual
    calendar (owner request, 2026-09: pressing 更新 should catch a delivery
    cancelled through another route — directly in intervals.icu or in Zwift
    — which otherwise leaves the local 'active' row stuck forever, since
    intervals events carry no client UID we'd be told a deletion through).
    Only updates local status — never calls the delete API, since the event
    is already gone there."""
    active = list_active(conn)
    if not active:
        return {"checked": 0, "removed": 0}
    dates = [r["scheduled_date"] for r in active]
    live_events = api.list_events(api_key, athlete_id, min(dates), max(dates))
    live_ids = {str(e["id"]) for e in live_events if e.get("id") is not None}
    removed = 0
    now = _now()
    for r in active:
        if str(r["intervals_event_id"]) not in live_ids:
            conn.execute(
                "UPDATE deliveries SET status='deleted', deleted_at=? WHERE id=?",
                (now, r["id"]),
            )
            removed += 1
    if removed:
        conn.commit()
    return {"checked": len(active), "removed": removed}
