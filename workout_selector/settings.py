"""Web-console-editable configuration, backed by the `settings` key/value
table (db.py). Goal (owner request): configure and operate this app entirely
from the browser, without hand-editing config files or running the CLI.

Values are plain strings in the table; JSON-encode anything else before
calling set_setting/get_setting_json.
"""
import json
import re
import sqlite3
from typing import Any, List, Optional

from .metrics import DEFAULT_TUNING
from .metrics import ZONE_BOUNDS as _DEFAULT_ZONE_BOUNDS_TUPLES

# Known keys. ATHLETE_ID falls back to the pre-existing WS_ATHLETE_ID env var
# (web.py) so upgrading doesn't silently change an already-configured
# athlete id; ZWO_DIR has no env-var equivalent since it was previously only
# ever passed as a one-off `cli.py ingest --dir` argument.
ZWO_DIR = "zwo_dir"
ATHLETE_ID = "intervals_athlete_id"
LAST_SCAN_RESULT = "last_scan_result"  # JSON: {"at": iso8601, **ingest_directory() stats}

# Off by default so a fresh install's demo `sample`-tagged workouts (see
# tools/generate_sample_workouts.py) show up in search right away; the owner
# flips this on once real workouts are loaded and the samples become noise
# (owner decision 2026-09) rather than deleting the sample files themselves.
HIDE_SAMPLE_TAG = "hide_sample_tag"

# Classification tuning (owner "C" phase — starting with zone bounds/colors,
# the highest-churn item). Stored as JSON; metrics.py takes these as an
# explicit parameter rather than importing settings itself, so it stays a
# pure function of (doc, config) with no DB/import dependency of its own —
# ingest.py is the one place that reads settings and threads the value
# through (see ingest_directory).
CONFIG_ZONE_BOUNDS = "zone_bounds"
CONFIG_ZONE_COLORS = "zone_colors"
CONFIG_TUNING = "tuning"  # sweet spot / structure / cadence / extreme-power — see metrics.DEFAULT_TUNING

# (min, max) sanity ranges for each tuning field. Percent/ratio fields are
# fractions (0-1) to match how the rest of the config API represents %FTP
# (zone_bounds) — the settings-screen form converts to/from whole-percent
# display, same as it already does for zone boundaries.
_TUNING_RANGES = {
    "sweet_spot_low": (0.0, 3.0),
    "sweet_spot_high": (0.0, 3.0),
    "sweet_spot_tag_min_pct": (0.0, 100.0),
    "sweetspot_tag_low": (0.0, 3.0),
    "sweetspot_tag_high": (0.0, 3.0),
    "sweetspot_high_frac": (0.0, 5.0),
    "sweetspot_recovery_frac": (0.0, 1.0),
    "sweetspot_min_minutes": (0.0, 180.0),
    "sweetspot_ss_ratio_min": (0.0, 1.0),
    "sweetspot_high_ratio_max": (0.0, 1.0),
    "interval_structure_threshold": (0.0, 1.0),
    "vi_interval_threshold": (1.0, 3.0),
    "vi_mixed_threshold": (1.0, 3.0),
    "high_cadence_rpm": (40, 250),
    "low_cadence_rpm": (20, 150),
    "extreme_power_frac": (1.0, 10.0),
}

# [[zone, upper_frac_or_None], ...] — mirrors metrics.ZONE_BOUNDS, just JSON-
# shaped (tuples -> lists, so a fresh DB's GET /api/config round-trips the
# exact same shape a POST would send back).
DEFAULT_ZONE_BOUNDS: List[list] = [[z, u] for z, u in _DEFAULT_ZONE_BOUNDS_TUPLES]

# Not in metrics.py at all — the zone colors were previously only a display
# concern hardcoded in app.js (ZONE_COLOR), never used in classification math.
DEFAULT_ZONE_COLORS = {
    "1": "#9aa0a6", "2": "#4c8bf5", "3": "#34a853",
    "4": "#fbbc04", "5": "#ff9800", "6": "#ea4335",
}

_HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


def get_setting(conn: sqlite3.Connection, key: str, default: Optional[str] = None) -> Optional[str]:
    row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row is not None else default


def set_setting(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    conn.commit()


def get_setting_json(conn: sqlite3.Connection, key: str) -> Optional[Any]:
    raw = get_setting(conn, key)
    return json.loads(raw) if raw is not None else None


def set_setting_json(conn: sqlite3.Connection, key: str, value: Any) -> None:
    set_setting(conn, key, json.dumps(value))


def get_zone_bounds(conn: sqlite3.Connection) -> List[list]:
    return get_setting_json(conn, CONFIG_ZONE_BOUNDS) or DEFAULT_ZONE_BOUNDS


def get_zone_colors(conn: sqlite3.Connection) -> dict:
    return get_setting_json(conn, CONFIG_ZONE_COLORS) or DEFAULT_ZONE_COLORS


def get_hide_sample_tag(conn: sqlite3.Connection) -> bool:
    return bool(get_setting_json(conn, HIDE_SAMPLE_TAG))


def validate_zone_bounds(bounds: Any) -> List[list]:
    """6 entries, zones 1..6 in order, strictly-increasing upper bounds,
    zone 6 open-ended (upper=null) — the shape _zone_of()/app.js's zoneOf()
    both assume."""
    if not isinstance(bounds, list) or len(bounds) != 6:
        raise ValueError("zone_bounds must have exactly 6 entries (zones 1-6)")
    out = []
    prev_upper = 0.0
    for i, entry in enumerate(bounds):
        if not (isinstance(entry, (list, tuple)) and len(entry) == 2):
            raise ValueError("each zone_bounds entry must be [zone, upper]")
        zone, upper = entry
        if zone != i + 1:
            raise ValueError("zone_bounds must list zones 1-6 in order")
        if i == len(bounds) - 1:
            if upper is not None:
                raise ValueError("zone 6 (last) must be open-ended: upper=null")
            out.append([zone, None])
        else:
            if not isinstance(upper, (int, float)) or isinstance(upper, bool):
                raise ValueError("zone %d upper bound must be a number" % zone)
            if not (prev_upper < upper <= 5.0):
                raise ValueError(
                    "zone %d upper bound (%.3f) must be greater than the previous "
                    "zone's and at most 5.0 (500%%FTP)" % (zone, upper)
                )
            out.append([zone, float(upper)])
            prev_upper = upper
    return out


def validate_zone_colors(colors: Any) -> dict:
    if not isinstance(colors, dict):
        raise ValueError("zone_colors must be an object keyed by zone number")
    out = {}
    for zone in ("1", "2", "3", "4", "5", "6"):
        v = colors.get(zone)
        if not isinstance(v, str) or not _HEX_COLOR_RE.match(v):
            raise ValueError("zone_colors[%s] must be a #RRGGBB hex color" % zone)
        out[zone] = v.lower()
    return out


def get_tuning(conn: sqlite3.Connection) -> dict:
    return get_setting_json(conn, CONFIG_TUNING) or dict(DEFAULT_TUNING)


def validate_tuning(data: Any) -> dict:
    """Requires the full set of tuning keys (like validate_zone_bounds — the
    settings-screen form always submits its whole current state, not a
    partial diff), each within a sane range, plus a few cross-field
    consistency checks that would otherwise silently produce dead branches
    in metrics.py's classification logic."""
    if not isinstance(data, dict):
        raise ValueError("tuning must be an object")
    missing = set(_TUNING_RANGES) - set(data)
    if missing:
        raise ValueError("tuning is missing keys: %s" % ", ".join(sorted(missing)))
    extra = set(data) - set(_TUNING_RANGES)
    if extra:
        raise ValueError("unknown tuning keys: %s" % ", ".join(sorted(extra)))

    out = {}
    for key, (lo, hi) in _TUNING_RANGES.items():
        value = data[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError("tuning[%s] must be a number" % key)
        if not (lo <= value <= hi):
            raise ValueError("tuning[%s] must be between %s and %s" % (key, lo, hi))
        out[key] = float(value)

    if out["sweet_spot_low"] >= out["sweet_spot_high"]:
        raise ValueError("sweet_spot_low must be less than sweet_spot_high")
    if out["sweetspot_tag_low"] >= out["sweetspot_tag_high"]:
        raise ValueError("sweetspot_tag_low must be less than sweetspot_tag_high")
    if out["vi_mixed_threshold"] > out["vi_interval_threshold"]:
        raise ValueError("vi_mixed_threshold must be <= vi_interval_threshold")
    if out["low_cadence_rpm"] >= out["high_cadence_rpm"]:
        raise ValueError("low_cadence_rpm must be less than high_cadence_rpm")
    return out
