"""F3: search/filter (AND-combined, range-based) + closeness-to-target
ranking, per workout-selector.md §5 F3."""
import json
import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class Criteria:
    duration_min_sec: Optional[int] = None
    duration_max_sec: Optional[int] = None
    tss_min: Optional[float] = None
    tss_max: Optional[float] = None
    if_min: Optional[float] = None
    if_max: Optional[float] = None
    primary_types: Optional[List[str]] = None    # OR among these
    structure_types: Optional[List[str]] = None  # OR among these
    zone: Optional[int] = None                   # 1-6, used with zone_min_pct
    zone_min_pct: Optional[float] = None
    has_cadence: Optional[bool] = None
    has_high_cadence: Optional[bool] = None
    has_low_cadence: Optional[bool] = None
    has_freeride: Optional[bool] = None
    has_warmup: Optional[bool] = None
    has_cooldown: Optional[bool] = None
    sport_type: Optional[str] = None
    tags: Optional[List[str]] = None             # combined per tags_mode; tag_type='embedded'
    tags_mode: str = "and"                        # "and": must have all: "or": must have any
    sub_types: Optional[List[str]] = None          # AND: must have all; tag_type='sub_type'
    name_query: Optional[str] = None              # substring match against name, case-insensitive
    include_rest_days: bool = False
    dedupe_identical: bool = True                 # collapse same-content workouts (e.g. a
                                                   # training plan reusing one session across weeks)
    favorites_only: bool = False                  # workout_id present in the `favorites` table
    hide_sample: bool = False                     # excludes tag_type='embedded' tag='sample'


_FLAG_COLUMNS = (
    "has_cadence", "has_high_cadence", "has_low_cadence",
    "has_freeride", "has_warmup", "has_cooldown",
)


def search(conn: sqlite3.Connection, c: Criteria) -> List[dict]:
    where: List[str] = []
    params: List[Any] = []

    if not c.include_rest_days:
        where.append("is_rest_day = 0")
    if c.duration_min_sec is not None:
        where.append("duration_sec >= ?"); params.append(c.duration_min_sec)
    if c.duration_max_sec is not None:
        where.append("duration_sec <= ?"); params.append(c.duration_max_sec)
    if c.tss_min is not None:
        where.append("tss >= ?"); params.append(c.tss_min)
    if c.tss_max is not None:
        where.append("tss <= ?"); params.append(c.tss_max)
    if c.if_min is not None:
        where.append("if_frac >= ?"); params.append(c.if_min)
    if c.if_max is not None:
        where.append("if_frac <= ?"); params.append(c.if_max)
    if c.primary_types:
        where.append("primary_type IN (%s)" % ",".join("?" * len(c.primary_types)))
        params.extend(c.primary_types)
    if c.structure_types:
        where.append("structure_type IN (%s)" % ",".join("?" * len(c.structure_types)))
        params.extend(c.structure_types)
    if c.sport_type:
        where.append("sport_type = ?"); params.append(c.sport_type)
    if c.name_query:
        # Space-separated terms all must appear somewhere in the name (any
        # order) — e.g. "sst med" matches "SST (Med)" even though it isn't
        # a literal substring of the title (owner request, 2026-09).
        for term in c.name_query.split():
            where.append("name LIKE ? ESCAPE '\\'")
            escaped = term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            params.append(f"%{escaped}%")
    for flag_name in _FLAG_COLUMNS:
        val = getattr(c, flag_name)
        if val is not None:
            where.append("%s = ?" % flag_name)
            params.append(1 if val else 0)

    sql = "SELECT * FROM workouts"
    if where:
        sql += " WHERE " + " AND ".join(where)

    rows = [dict(r) for r in conn.execute(sql, params).fetchall()]

    # zone_pcts and tags are JSON / a join, respectively — cheaper to
    # post-filter in Python than to fight SQLite's JSON1 availability, and
    # the catalog (~1500 rows) is small enough that this costs nothing.
    if c.zone is not None and c.zone_min_pct is not None:
        rows = [
            r for r in rows
            if json.loads(r["zone_pcts"] or "{}").get(str(c.zone), 0) >= c.zone_min_pct
        ]

    if c.tags:
        wanted = {t.strip().lower() for t in c.tags}
        ids = [r["id"] for r in rows]
        tag_map: Dict[int, set] = {}
        if ids:
            placeholders = ",".join("?" * len(ids))
            for row in conn.execute(
                "SELECT workout_id, tag FROM tags WHERE tag_type = 'embedded' AND workout_id IN (%s)" % placeholders,
                ids,
            ):
                tag_map.setdefault(row["workout_id"], set()).add(row["tag"])
        if c.tags_mode == "or":
            rows = [r for r in rows if wanted & tag_map.get(r["id"], set())]
        else:
            rows = [r for r in rows if wanted <= tag_map.get(r["id"], set())]

    if c.sub_types:
        # Always AND (owner decision 2026-09) — sub_types are independent
        # boolean characteristics a workout can have several of at once,
        # like the フラグ section's selects, not a single category like
        # primary_type where checking several means "any of these".
        wanted_sub = {s.strip().lower() for s in c.sub_types}
        ids = [r["id"] for r in rows]
        sub_map: Dict[int, set] = {}
        if ids:
            placeholders = ",".join("?" * len(ids))
            for row in conn.execute(
                "SELECT workout_id, tag FROM tags WHERE tag_type = 'sub_type' AND workout_id IN (%s)" % placeholders,
                ids,
            ):
                sub_map.setdefault(row["workout_id"], set()).add(row["tag"])
        rows = [r for r in rows if wanted_sub <= sub_map.get(r["id"], set())]

    if c.favorites_only:
        favorite_ids = {row["workout_id"] for row in conn.execute("SELECT workout_id FROM favorites")}
        rows = [r for r in rows if r["id"] in favorite_ids]

    if c.hide_sample:
        sample_ids = {
            row["workout_id"] for row in conn.execute(
                "SELECT workout_id FROM tags WHERE tag_type = 'embedded' AND tag = 'sample'"
            )
        }
        rows = [r for r in rows if r["id"] not in sample_ids]

    if c.dedupe_identical:
        rows = dedupe_by_content(rows)

    return rows


def dedupe_by_content(rows: List[dict]) -> List[dict]:
    """Keeps one row per distinct content_hash (structural fingerprint —
    see metrics.compute_content_hash), dropping later duplicates. Ordered by
    id first so the result is deterministic regardless of the caller's
    row order; rank() re-sorts afterwards anyway."""
    seen = set()
    deduped = []
    for r in sorted(rows, key=lambda r: r["id"]):
        h = r["content_hash"]
        if h:
            if h in seen:
                continue
            seen.add(h)
        deduped.append(r)
    return deduped


def _tri(v: Optional[str]) -> Optional[bool]:
    """'yes'/'no'/'any'(or None) -> True/False/None. Shared by the CLI and
    the web API so tri-state flag parsing stays in one place."""
    if v is None:
        return None
    v = v.lower()
    if v == "yes":
        return True
    if v == "no":
        return False
    return None


def _split(v) -> Optional[List[str]]:
    if v is None:
        return None
    if isinstance(v, str):
        return [x.strip() for x in v.split(",") if x.strip()]
    return list(v)


def build_criteria(*, duration_min=None, duration_max=None, tss_min=None, tss_max=None,
                    if_min=None, if_max=None, primary_type=None, structure_type=None,
                    zone=None, zone_min_pct=None, cadence=None, high_cadence=None,
                    low_cadence=None, freeride=None, warmup=None, cooldown=None,
                    sport_type=None, tags=None, tags_mode=None, sub_type=None, name_query=None,
                    include_duplicates=False, favorites_only=False, hide_sample=False) -> Criteria:
    """Builds a Criteria from the "friendly" units both the CLI and the web
    API accept: duration in minutes, tri-state flags as yes/no/any strings,
    comma-separated lists as plain strings."""
    return Criteria(
        duration_min_sec=int(duration_min * 60) if duration_min is not None else None,
        duration_max_sec=int(duration_max * 60) if duration_max is not None else None,
        tss_min=tss_min, tss_max=tss_max, if_min=if_min, if_max=if_max,
        primary_types=_split(primary_type), structure_types=_split(structure_type),
        zone=zone, zone_min_pct=zone_min_pct,
        has_cadence=_tri(cadence), has_high_cadence=_tri(high_cadence),
        has_low_cadence=_tri(low_cadence), has_freeride=_tri(freeride),
        has_warmup=_tri(warmup), has_cooldown=_tri(cooldown),
        sport_type=sport_type, tags=_split(tags),
        tags_mode="or" if (tags_mode or "").lower() == "or" else "and",
        sub_types=_split(sub_type),
        name_query=name_query.strip() if name_query else None,
        dedupe_identical=not include_duplicates,
        favorites_only=favorites_only,
        hide_sample=hide_sample,
    )


def resolve_targets(duration_min=None, duration_max=None, target_duration=None,
                     tss_min=None, tss_max=None, target_tss=None):
    """Target duration (seconds) / TSS for rank(): explicit target wins,
    otherwise falls back to the midpoint of a given min/max range."""
    if target_duration is not None:
        td = target_duration * 60
    elif duration_min is not None and duration_max is not None:
        td = (duration_min + duration_max) / 2 * 60
    else:
        td = None

    tt = target_tss if target_tss is not None else (
        (tss_min + tss_max) / 2 if tss_min is not None and tss_max is not None else None
    )
    return td, tt


def rank(rows: List[dict], target_duration_sec: Optional[float] = None,
         target_tss: Optional[float] = None, limit: int = 10) -> List[dict]:
    """Sorts by closeness to the given target(s) (relative distance, summed
    when both are given); rows missing a needed value sort last."""

    def score(r):
        s = 0.0
        if target_duration_sec:
            s += abs(r["duration_sec"] - target_duration_sec) / target_duration_sec
        if target_tss:
            if r["tss"] is None:
                return float("inf")
            s += abs(r["tss"] - target_tss) / target_tss
        return s

    return sorted(rows, key=score)[:limit]


# Maps the search UI's 並べ替え field values to the row dict keys `search()`
# actually returns (raw DB column names, not the /api/workouts response's
# renamed fields — e.g. the UI's "duration_min" sorts by seconds).
_SORT_FIELDS = {"duration_min": "duration_sec", "tss": "tss", "if": "if_frac"}


def sort_field_rows(rows: List[dict], field: str, direction: str = "asc") -> List[dict]:
    """Sorts the full matched set by a plain field instead of target-closeness
    (2026-09: 並べ替え is server-side so it's correct across the whole match
    set, not just whatever page happened to be fetched). Rows missing the
    value sort last regardless of direction, matching rank()'s convention."""
    key = _SORT_FIELDS.get(field)
    if key is None:
        return rows
    reverse = direction == "desc"

    def sort_key(r):
        v = r.get(key)
        if v is None:
            return (1, 0)
        return (0, -v if reverse else v)

    return sorted(rows, key=sort_key)
