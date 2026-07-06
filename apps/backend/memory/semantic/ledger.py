"""SQLite CRUD for the `memories` table — the source of truth for semantic memory.

Same shape as tasks.py/reminders.py etc.: thin functions over one table, no
interpretation of the data. Scoring lives in ranking.py, state-transition policy
in lifecycle.py; this file only reads and writes rows. The only thing that makes
this table special is that every row also has a corresponding vector in LanceDB
(vector_store.py) — but that correspondence is service.py's concern.

Column semantics (2.2):
  tier              short_term|medium_term|long_term|archived|forgotten (ranking.py)
  importance        write-time prior in [0,1]
  access_count      reinforcement counter, bumped by record_access
  last_accessed_at  last time the memory was touched or reinforced (recency ref)
  deleted_at        soft-delete tombstone; non-NULL ⇒ invisible to recall
  supersedes_id     this row replaces that older row (versioning chain)
  content_hash      dedup key over normalized text (+source_type)
  embedding_*       provenance of the vector, so a model upgrade is detectable

Column semantics (2.7 — entity-extraction state):
  entities_extracted_at  when Brain's extraction sweep successfully processed
                         this row; NULL ⇒ still pending. This stamp is what
                         makes extraction idempotent: a processed memory can
                         never be re-extracted, so graph edges are never
                         double-reinforced by re-reading the same evidence.
  extraction_attempts    how many sweeps have tried; the sweep stops retrying
                         past its max, so one malformed memory can't wedge the
                         pipeline forever (poison-pill guard).
"""

import json
from typing import Optional

from .. import _connection


def insert(
    memory_id: str,
    text: str,
    source_type: str,
    source_id: Optional[str],
    metadata: dict,
    content_hash: str,
    importance: float,
    tier: str,
    embedding_model: str,
    embedding_version: str,
    embedding_dimension: int,
    supersedes_id: Optional[str] = None,
) -> str:
    created_at = _connection.now()
    with _connection.connect() as con:
        con.execute(
            """INSERT INTO memories
               (id, text, source_type, source_id, metadata, content_hash,
                tier, importance, access_count, last_accessed_at, supersedes_id,
                deleted_at, embedding_model, embedding_version, embedding_dimension,
                created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?, NULL, ?, ?, ?, ?)""",
            (memory_id, text, source_type, source_id, json.dumps(metadata),
             content_hash, tier, importance, supersedes_id,
             embedding_model, embedding_version, embedding_dimension, created_at),
        )
    return created_at


# ── Reads ────────────────────────────────────────────────────────────────────


def get(memory_id: str) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    return dict(row) if row else None


def get_by_ids(ids: list[str]) -> dict[str, dict]:
    if not ids:
        return {}
    placeholders = ",".join("?" for _ in ids)
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            f"SELECT * FROM memories WHERE id IN ({placeholders})", ids
        ).fetchall()
    return {r["id"]: dict(r) for r in rows}


def get_all() -> list[dict]:
    """Every row, oldest first — used only by rebuild_index() (includes deleted)."""
    with _connection.connect(rows=True) as con:
        rows = con.execute("SELECT * FROM memories ORDER BY created_at").fetchall()
    return [dict(r) for r in rows]


def get_active() -> list[dict]:
    """Non-deleted rows in a recallable/scorable state — used by maintenance."""
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM memories WHERE deleted_at IS NULL ORDER BY created_at"
        ).fetchall()
    return [dict(r) for r in rows]


_SORT_COLUMNS = {
    "created_at": "created_at",
    "importance": "importance",
    "access_count": "access_count",
    "tier": "tier",
}


def list_active(
    limit: int = 50,
    offset: int = 0,
    tier: Optional[str] = None,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
) -> list[dict]:
    """Paginated browse over active (non-deleted) memory rows."""
    conditions = ["deleted_at IS NULL"]
    params: list = []

    if tier:
        conditions.append("tier = ?")
        params.append(tier)
    if source_type:
        conditions.append("source_type = ?")
        params.append(source_type)
    if search:
        conditions.append("text LIKE ?")
        params.append(f"%{search.strip()}%")

    sort_col = _SORT_COLUMNS.get(sort, "created_at")
    order_dir = "DESC" if order.lower() == "desc" else "ASC"
    where = " AND ".join(conditions)
    query = (
        f"SELECT * FROM memories WHERE {where} "
        f"ORDER BY {sort_col} {order_dir} LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    with _connection.connect(rows=True) as con:
        rows = con.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def count_active(
    tier: Optional[str] = None,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
) -> int:
    """Count active rows, optionally filtered."""
    conditions = ["deleted_at IS NULL"]
    params: list = []

    if tier:
        conditions.append("tier = ?")
        params.append(tier)
    if source_type:
        conditions.append("source_type = ?")
        params.append(source_type)
    if search:
        conditions.append("text LIKE ?")
        params.append(f"%{search.strip()}%")

    where = " AND ".join(conditions)
    with _connection.connect() as con:
        row = con.execute(
            f"SELECT COUNT(*) FROM memories WHERE {where}", params
        ).fetchone()
    return int(row[0])


def count_active_by_tier() -> dict[str, int]:
    """Active memory counts grouped by tier."""
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """SELECT tier, COUNT(*) AS n FROM memories
               WHERE deleted_at IS NULL GROUP BY tier ORDER BY tier"""
        ).fetchall()
    return {r["tier"]: r["n"] for r in rows}


def find_active_duplicate(content_hash: str) -> Optional[dict]:
    """The live (not soft-deleted) row with this content hash, if any.

    Dedup only considers active rows: a forgotten memory sharing text with a new
    one shouldn't block re-remembering it. Returns the oldest match so repeated
    duplicates all fold into the first original.
    """
    if not content_hash:
        return None
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """SELECT * FROM memories
               WHERE content_hash = ? AND deleted_at IS NULL
               ORDER BY created_at LIMIT 1""",
            (content_hash,),
        ).fetchone()
    return dict(row) if row else None


def get_purgeable(cutoff_iso: str) -> list[str]:
    """Ids of forgotten memories soft-deleted before `cutoff_iso` — hard-purge set."""
    with _connection.connect() as con:
        rows = con.execute(
            "SELECT id FROM memories WHERE deleted_at IS NOT NULL AND deleted_at < ?",
            (cutoff_iso,),
        ).fetchall()
    return [r[0] for r in rows]


def count(include_deleted: bool = False) -> int:
    sql = "SELECT COUNT(*) FROM memories"
    if not include_deleted:
        sql += " WHERE deleted_at IS NULL"
    with _connection.connect() as con:
        return con.execute(sql).fetchone()[0]


# ── Writes / state transitions (thin; policy decided by callers) ──────────────


def set_tier(memory_id: str, tier: str) -> None:
    with _connection.connect() as con:
        con.execute("UPDATE memories SET tier = ? WHERE id = ?", (tier, memory_id))


def touch(memory_id: str) -> None:
    """Mark 'seen' — refresh recency without counting it as reinforcement."""
    with _connection.connect() as con:
        con.execute(
            "UPDATE memories SET last_accessed_at = ? WHERE id = ?",
            (_connection.now(), memory_id),
        )


def record_access(ids: list[str]) -> None:
    """Mark 'used' — increment reinforcement counter and refresh recency."""
    if not ids:
        return
    now = _connection.now()
    with _connection.connect() as con:
        con.executemany(
            "UPDATE memories SET access_count = access_count + 1, last_accessed_at = ? WHERE id = ?",
            [(now, mid) for mid in ids],
        )


def soft_delete(memory_id: str) -> None:
    """Set the tombstone and move to the forgotten tier. Recoverable via restore."""
    with _connection.connect() as con:
        con.execute(
            "UPDATE memories SET deleted_at = ?, tier = ? WHERE id = ?",
            (_connection.now(), "forgotten", memory_id),
        )


def restore(memory_id: str, tier: str) -> None:
    """Clear the tombstone and re-enter the lifecycle at `tier`."""
    with _connection.connect() as con:
        con.execute(
            "UPDATE memories SET deleted_at = NULL, tier = ? WHERE id = ?",
            (tier, memory_id),
        )


def hard_delete(ids: list[str]) -> None:
    """Permanent row removal — only called by maintenance after retention."""
    if not ids:
        return
    placeholders = ",".join("?" for _ in ids)
    with _connection.connect() as con:
        con.execute(f"DELETE FROM memories WHERE id IN ({placeholders})", ids)


# ── Entity-extraction state (2.7; policy decided by Brain's sweep) ───────────


def pending_extraction(limit: int, max_attempts: int,
                       tiers: tuple[str, ...]) -> list[dict]:
    """Oldest live rows not yet entity-extracted and not retried out.

    Only rows in `tiers` (the caller passes the active tiers) are eligible:
    archived rows are superseded/stale history whose facts may no longer hold,
    and tombstoned rows are invisible everywhere else too.
    """
    tier_marks = ",".join("?" for _ in tiers)
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            f"""SELECT id, text, source_type, created_at FROM memories
                WHERE entities_extracted_at IS NULL
                  AND deleted_at IS NULL
                  AND extraction_attempts < ?
                  AND tier IN ({tier_marks})
                ORDER BY created_at
                LIMIT ?""",
            (max_attempts, *tiers, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def record_extraction_attempt(ids: list[str]) -> None:
    """Count a sweep touching these rows — before the attempt, so a crash
    mid-extraction still counts against the retry budget."""
    if not ids:
        return
    with _connection.connect() as con:
        con.executemany(
            "UPDATE memories SET extraction_attempts = extraction_attempts + 1 WHERE id = ?",
            [(mid,) for mid in ids],
        )


def mark_extracted(ids: list[str]) -> None:
    """Stamp rows as successfully entity-extracted — they leave the pending set
    permanently (and drop out of the partial index)."""
    if not ids:
        return
    now = _connection.now()
    with _connection.connect() as con:
        con.executemany(
            "UPDATE memories SET entities_extracted_at = ? WHERE id = ?",
            [(now, mid) for mid in ids],
        )


def set_embedding_meta(memory_id: str, model: str, version: str, dimension: int) -> None:
    """Record which provider produced this row's current vector (rebuild_index)."""
    with _connection.connect() as con:
        con.execute(
            """UPDATE memories
               SET embedding_model = ?, embedding_version = ?, embedding_dimension = ?
               WHERE id = ?""",
            (model, version, dimension, memory_id),
        )
