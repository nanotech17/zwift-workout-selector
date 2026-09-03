"""SQLite schema and connection helper (workout-selector.md §4)."""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT UNIQUE NOT NULL,
    filename TEXT NOT NULL,
    name TEXT,
    author TEXT,
    description TEXT,
    category TEXT,
    subcategory TEXT,
    sport_type TEXT,
    duration_sec INTEGER,
    powered_duration_sec INTEGER,
    avg_intensity REAL,
    np_frac REAL,
    if_frac REAL,
    tss REAL,
    num_blocks INTEGER,
    num_intervals INTEGER,
    work_rest_ratio REAL,
    structure_type TEXT,
    has_cadence INTEGER,
    has_freeride INTEGER,
    has_ramp INTEGER,
    has_maxeffort INTEGER,
    has_max_sprint INTEGER,
    has_high_cadence INTEGER,
    has_low_cadence INTEGER,
    has_warmup INTEGER,
    has_cooldown INTEGER,
    is_rest_day INTEGER,
    primary_zone INTEGER,
    primary_type TEXT,
    zone_pcts TEXT,
    sweet_spot_pct REAL,
    power_estimated INTEGER,
    content_hash TEXT,
    source_hash TEXT NOT NULL,
    analyzed_at TEXT NOT NULL,
    parse_warnings TEXT
);

CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL REFERENCES workouts(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    tag_type TEXT NOT NULL DEFAULT 'auto',
    UNIQUE(workout_id, tag)
);

CREATE TABLE IF NOT EXISTS deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL REFERENCES workouts(id),
    intervals_event_id TEXT,
    scheduled_date TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL,
    deleted_at TEXT
);

-- User-set state, not derived from the .zwo files — kept separate from
-- `tags` on purpose: ingest.py wipes and rebuilds a workout's tags on every
-- rescan (they're recomputed from the file each time), which would silently
-- discard a favorite marked via a shared table (owner decision, 2026-09;
-- see deliveries above for the same reasoning).
CREATE TABLE IF NOT EXISTS favorites (
    workout_id INTEGER PRIMARY KEY REFERENCES workouts(id) ON DELETE CASCADE,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingest_errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filepath TEXT NOT NULL,
    error TEXT NOT NULL,
    occurred_at TEXT NOT NULL
);

-- Web-console-editable configuration (settings.py). Small enough as a
-- generic key/value table that each new setting doesn't need its own
-- migration; values are stored as plain strings (JSON-encoded where a
-- setting isn't itself a string).
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


# Columns added to `workouts` after its initial release. CREATE TABLE IF
# NOT EXISTS only affects a brand-new DB file, so an existing one needs
# these added explicitly — kept minimal (no destructive ALTER/DROP) rather
# than requiring the DB to be rebuilt from scratch on every schema change.
_MIGRATIONS = [
    ("workouts", "content_hash", "TEXT"),
    ("workouts", "category_override", "TEXT"),
]


def _migrate(conn: sqlite3.Connection) -> None:
    for table, column, coltype in _MIGRATIONS:
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(%s)" % table)}
        if column not in cols:
            conn.execute("ALTER TABLE %s ADD COLUMN %s %s" % (table, column, coltype))


def connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    _migrate(conn)
    return conn
