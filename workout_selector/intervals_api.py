"""Raw intervals.icu API calls (workout-selector.md §8). No third-party
dependencies — uses stdlib urllib, since Phase 1-3 don't need the FastAPI
stack yet."""
import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

API_BASE = "https://intervals.icu/api/v1"


class IntervalsApiError(Exception):
    pass


def _auth_header(api_key: str) -> str:
    token = base64.b64encode(("API_KEY:%s" % api_key).encode("utf-8")).decode("ascii")
    return "Basic %s" % token


def _q(value) -> str:
    """URL-encodes a value for use as a path segment. athlete_id (settings
    screen) and scheduled_date/time (delivery form) reach here with no
    format validation upstream — without this, a value containing URL-
    special characters (/, &, #, ?) could alter the request path or inject
    extra query parameters into the intervals.icu request instead of being
    treated as literal data (owner-directed security fix, 2026-09)."""
    return urllib.parse.quote(str(value), safe="")


def _request(method: str, url: str, api_key: str, body: Optional[dict] = None) -> dict:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", _auth_header(api_key))
    req.add_header("Content-Type", "application/json")
    # Cloudflare 403s (error 1010) on the default "Python-urllib/x.y" UA.
    req.add_header("User-Agent", "workout-selector/0.1 (+local)")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")
        raise IntervalsApiError("%s %s -> HTTP %s: %s" % (method, url, e.code, detail))
    except urllib.error.URLError as e:
        raise IntervalsApiError("%s %s -> %s" % (method, url, e))


def create_event(api_key: str, athlete_id: str, name: str, description: str,
                  scheduled_date: str, zwo_xml: str, filename: str,
                  scheduled_time: Optional[str] = None) -> dict:
    """POST .../events — registers a WORKOUT event on the athlete's calendar.
    intervals.icu assigns its own event id; the caller must record it (§8:
    no client-side UID, so upsert-based idempotency isn't possible).

    scheduled_time is "HH:MM" (from the UI's <input type="time">) or None,
    in which case the event defaults to midnight local, same as before time
    selection existed."""
    url = "%s/athlete/%s/events" % (API_BASE, _q(athlete_id))
    body = {
        "category": "WORKOUT",
        "type": "Ride",
        "start_date_local": "%sT%s:00" % (scheduled_date, scheduled_time or "00:00"),
        "name": name,
        "description": description or "",
        "filename": filename,
        "file_contents": zwo_xml,
    }
    return _request("POST", url, api_key, body)


def delete_event(api_key: str, athlete_id: str, event_id) -> None:
    url = "%s/athlete/%s/events/%s" % (API_BASE, _q(athlete_id), _q(event_id))
    _request("DELETE", url, api_key, None)


def list_events(api_key: str, athlete_id: str, oldest: str, newest: str,
                 category: str = "WORKOUT") -> list:
    """GET .../events — used to reconcile locally-recorded deliveries
    against what's actually still on intervals.icu's calendar. An event
    deleted directly there (or via Zwift) leaves no trace here otherwise —
    §8 notes intervals assigns its own event ids, so there's no client UID
    it could notify us through. oldest/newest are "YYYY-MM-DD"."""
    query = urllib.parse.urlencode({"oldest": oldest, "newest": newest, "category": category})
    url = "%s/athlete/%s/events?%s" % (API_BASE, _q(athlete_id), query)
    result = _request("GET", url, api_key, None)
    return result if isinstance(result, list) else []


def get_athlete(api_key: str, athlete_id: str) -> dict:
    """GET .../athlete/{id} — read-only profile fetch, used only as a
    connection test from the settings screen (no calendar side effects)."""
    url = "%s/athlete/%s" % (API_BASE, _q(athlete_id))
    return _request("GET", url, api_key, None)
