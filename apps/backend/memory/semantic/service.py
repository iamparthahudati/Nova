"""Public semantic-memory API — the surface memory/__init__.py re-exports.

Callers (Brain in 2.3, or anything else) never see ledger.py, vector_store.py,
ranking.py, lifecycle.py, or embedding_provider.py. They see a handful of verbs:

  write:        remember(), supersede_memory()
  read:         recall()
  reinforce:    record_access(), touch_memory()
  lifecycle:    promote_memory(), demote_memory(), archive_memory(),
                forget_memory(), restore_memory(), evaluate_memory()
  maintenance:  recalculate_scores(), maintenance()
  ops:          rebuild_index()
  extraction:   memories_pending_entity_extraction(),
                record_entity_extraction_attempt(), mark_entities_extracted()
                (2.7 — the ledger-state half of graph extraction; the judgment
                half lives in Brain, which owns *what the text means* while
                Memory owns only *which rows have been processed*)

This file is the only place that coordinates the two stores (SQLite ledger +
LanceDB vectors). Every operation that must stay consistent across both — write,
recall, purge-time vector compaction, full reindex — lives here. Operations that
are SQLite-only (tiering, soft delete, access counts) are delegated straight to
lifecycle.py and re-exported unchanged, because they never touch a vector.
"""

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone
from typing import Optional

from . import ledger, lifecycle, ranking
from .embedding_provider import get_default_provider
from .vector_store import VectorStore

# Re-export the SQLite-only lifecycle verbs verbatim: they need no vector work,
# so there's nothing for service.py to coordinate — but they belong to Memory's
# single public surface, so they flow out through here.
from .lifecycle import (  # noqa: F401  (re-exported, not used locally)
    promote_memory,
    demote_memory,
    archive_memory,
    forget_memory,
    restore_memory,
    touch_memory,
    record_access,
    evaluate_memory,
    recalculate_scores,
)

_store: Optional[VectorStore] = None

# ANN returns raw nearest neighbours; we then filter out soft-deleted/archived
# rows and re-rank the survivors by composite score, so we must over-fetch to
# still have k left after filtering. Personal-scale k is tiny, so this is cheap.
_CANDIDATE_MULTIPLIER = 4
_MIN_CANDIDATES = 20


def _get_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore(dimensions=get_default_provider().dimensions)
    return _store


def _content_hash(text: str, source_type: str) -> str:
    """Stable identity for dedup: sha256 over normalized text, scoped by source.

    Normalization (lowercase, collapse whitespace) folds trivial variants —
    "Ship  the App" and "ship the app\n" — into one identity. Scoping by
    source_type keeps the *same words* logged as a task distinct from the same
    words captured as a journal entry, because they mean different things.
    """
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    return hashlib.sha256(f"{source_type}\x00{normalized}".encode()).hexdigest()


def remember(
    text: str,
    source_type: str,
    source_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    importance: Optional[float] = None,
    supersedes_id: Optional[str] = None,
) -> str:
    """Embed and persist a memory. Returns its id (which may be an existing id).

    Write order is SQLite first (durable source of truth), LanceDB second
    (derived index) — a crash between them leaves the memory recoverable and
    rebuild_index() backfills the vector.

    Deduplication: unless this write is a supersession, an identical active
    memory is treated as a *re-occurrence*, not a new row — the existing memory
    is reinforced (record_access) and its id returned. This is what stops the
    ledger from filling with unlimited copies of a recurring statement while
    still letting genuine repetition count as a relevance signal.
    """
    text = text.strip()
    if not text:
        raise ValueError("remember() requires non-empty text")

    content_hash = _content_hash(text, source_type)

    # Dedup only applies to fresh writes. A supersession is *meant* to add a row
    # (the corrected version), so it always bypasses the duplicate check.
    if supersedes_id is None:
        existing = ledger.find_active_duplicate(content_hash)
        if existing is not None:
            lifecycle.record_access(existing["id"])  # repetition = reinforcement
            return existing["id"]

    provider = get_default_provider()
    vector = provider.embed([text])[0]
    memory_id = str(uuid.uuid4())
    if importance is None:
        importance = ranking.initial_importance(source_type, metadata)

    created_at = ledger.insert(
        memory_id, text, source_type, source_id, metadata or {},
        content_hash=content_hash,
        importance=importance,
        tier=ranking.SHORT_TERM,          # every memory is born short-term; §3
        embedding_model=provider.name,
        embedding_version=provider.version,
        embedding_dimension=provider.dimensions,
        supersedes_id=supersedes_id,
    )
    _get_store().add([{
        "id": memory_id,
        "vector": vector,
        "text": text,
        "source_type": source_type,
        "created_at": created_at,
    }])

    # Supersession moves the old memory toward archived rather than overwriting
    # it — history is preserved and walkable via the supersedes_id chain (§2).
    if supersedes_id is not None:
        lifecycle.archive_memory(supersedes_id)

    return memory_id


def supersede_memory(
    old_id: str,
    text: str,
    source_type: Optional[str] = None,
    source_id: Optional[str] = None,
    metadata: Optional[dict] = None,
    importance: Optional[float] = None,
) -> Optional[str]:
    """Correct a memory by writing a *new* row that supersedes the old one.

    The old row is archived (kept for audit/history), the new row points back at
    it via supersedes_id, and the new row becomes the live tip of the chain.
    Returns the new id, or None if old_id doesn't exist. source_type defaults to
    the superseded memory's, so a correction stays in the same semantic bucket.
    """
    old = ledger.get(old_id)
    if old is None:
        return None
    return remember(
        text,
        source_type=source_type or old["source_type"],
        source_id=source_id if source_id is not None else old["source_id"],
        metadata=metadata,
        importance=importance,
        supersedes_id=old_id,
    )


def recall(
    query: str,
    k: int = 5,
    source_type: Optional[str] = None,
    include_archived: bool = False,
    now: Optional[datetime] = None,
    config: ranking.RankingConfig = ranking.DEFAULT_CONFIG,
) -> list[dict]:
    """Semantic search, re-ranked by composite score (similarity + lifecycle).

    Pipeline: embed query → ANN over-fetch from LanceDB → join each candidate to
    its SQLite row → drop soft-deleted and (by default) archived/forgotten rows →
    score survivors with ranking.composite_query_score → return top-k.

    recall() does NOT reinforce what it returns: a candidate that surfaces here
    but is discarded by the caller shouldn't earn access credit. The caller
    reinforces the ones it actually uses via record_access (this is the seam
    Brain will use in 2.3). Filtering deleted_at here is the correctness-critical
    half of soft delete (§2): a forgotten memory is invisible the instant it's
    tombstoned, regardless of whether its vector has been compacted yet.
    """
    query = query.strip()
    if not query:
        return []
    now = now or datetime.now(timezone.utc)

    provider = get_default_provider()
    vector = provider.embed([query])[0]
    fetch = max(k * _CANDIDATE_MULTIPLIER, _MIN_CANDIDATES)
    hits = _get_store().search(vector, fetch, source_type)

    ledger_rows = ledger.get_by_ids([h["id"] for h in hits])
    allowed = ranking.ACTIVE_TIERS if not include_archived else (
        *ranking.ACTIVE_TIERS, ranking.ARCHIVED
    )

    scored = []
    for hit in hits:
        row = ledger_rows.get(hit["id"])
        if row is None:
            continue                          # vector with no ledger row (shouldn't happen)
        if row["deleted_at"] is not None:
            continue                          # soft-deleted: invisible to recall
        if row["tier"] not in allowed:
            continue
        similarity = ranking.similarity_from_distance(hit["score"])
        reference_ts = row["last_accessed_at"] or row["created_at"]
        composite = ranking.composite_query_score(
            similarity=similarity,
            importance=row["importance"],
            reference_ts=reference_ts,
            tier=row["tier"],
            access_count=row["access_count"],
            now=now,
            config=config,
        )
        scored.append({
            "id": row["id"],
            "text": row["text"],
            "source_type": row["source_type"],
            "source_id": row["source_id"],
            "metadata": json.loads(row["metadata"] or "{}"),
            "tier": row["tier"],
            "importance": row["importance"],
            "access_count": row["access_count"],
            "created_at": row["created_at"],
            "similarity": round(similarity, 4),
            "score": round(composite, 4),
        })

    scored.sort(key=lambda r: r["score"], reverse=True)
    return scored[:k]


def _format_row(row: dict) -> dict:
    """Shape a ledger row for API consumers."""
    return {
        "id": row["id"],
        "text": row["text"],
        "source_type": row["source_type"],
        "source_id": row["source_id"],
        "metadata": json.loads(row["metadata"] or "{}"),
        "tier": row["tier"],
        "importance": row["importance"],
        "access_count": row["access_count"],
        "created_at": row["created_at"],
    }


def list_memories(
    limit: int = 50,
    offset: int = 0,
    tier: Optional[str] = None,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "created_at",
    order: str = "desc",
) -> list[dict]:
    """Browse active memory rows with optional text search and sorting."""
    rows = ledger.list_active(
        limit=limit,
        offset=offset,
        tier=tier,
        source_type=source_type,
        search=search,
        sort=sort,
        order=order,
    )
    return [_format_row(row) for row in rows]


def count_active_memories(
    tier: Optional[str] = None,
    source_type: Optional[str] = None,
    search: Optional[str] = None,
) -> int:
    """Count active memory rows, optionally filtered."""
    return ledger.count_active(tier=tier, source_type=source_type, search=search)


def count_active_memories_by_tier() -> dict[str, int]:
    """Active memory counts grouped by tier."""
    return ledger.count_active_by_tier()


def maintenance(
    now: Optional[datetime] = None,
    config: ranking.RankingConfig = ranking.DEFAULT_CONFIG,
) -> dict:
    """The nightly job's memory step (§8): re-tier everything, then hard-purge.

    Two SQLite passes (delegated to lifecycle) bracket one vector-store pass
    (owned here): recalculate_scores re-tiers active rows and soft-deletes those
    that decayed below the forget floor; purge_forgotten hard-deletes rows past
    the retention window; then their vectors are compacted out of LanceDB. This
    is the only path that permanently removes anything — and only after a memory
    has been forgotten longer than config.forget_retention_hours.
    """
    result = lifecycle.recalculate_scores(now, config)
    purged = lifecycle.purge_forgotten(now, config)
    _get_store().delete(purged)
    return {"transitions": result["transitions"], "purged": purged}


# ── Entity-extraction state (2.7) ─────────────────────────────────────────────
# SQLite-only bookkeeping for Brain's extraction sweep. Memory exposes *which*
# memories still need extraction and records the outcome; it never decides what
# an entity or relation is (Rule 1 — that judgment is Brain's). No vector work,
# so these delegate straight to the ledger.


def memories_pending_entity_extraction(limit: int = 10,
                                       max_attempts: int = 3) -> list[dict]:
    """Oldest active memories Brain has not yet entity-extracted.

    Each row carries id, text, source_type, created_at — everything the
    extraction prompt needs. Rows retried `max_attempts` times are excluded
    (poison-pill guard); archived/forgotten rows are never offered.
    """
    return ledger.pending_extraction(
        max(1, int(limit)), max(1, int(max_attempts)), ranking.ACTIVE_TIERS
    )


def record_entity_extraction_attempt(ids: list[str]) -> None:
    """Count an extraction attempt against these memories (call *before* the
    attempt, so even a crash consumes retry budget)."""
    ledger.record_extraction_attempt(ids)


def mark_entities_extracted(ids: list[str]) -> None:
    """Mark memories as successfully extracted — they never re-enter the
    pending set, which is what keeps extraction idempotent."""
    ledger.mark_extracted(ids)


def rebuild_index() -> int:
    """Regenerate every vector from SQLite text with the *current* provider.

    Recovery path if LanceDB is deleted/corrupted, and the embedding-migration
    path when the model is upgraded: bump the provider (name/version/dimension),
    call this once, done — no manual migration. Every row is re-embedded and its
    embedding_model/version/dimension stamped to the current provider, and the
    LanceDB table is recreated at the provider's dimension, so a dimension change
    is handled automatically. Soft-deleted-but-not-purged rows are re-embedded
    too, so a later restore still has its vector.
    """
    rows = ledger.get_all()
    provider = get_default_provider()
    if not rows:
        _get_store().rebuild([])
        return 0

    vectors = provider.embed([r["text"] for r in rows])
    payload = [
        {
            "id": row["id"],
            "vector": vector,
            "text": row["text"],
            "source_type": row["source_type"],
            "created_at": row["created_at"],
        }
        for row, vector in zip(rows, vectors)
    ]
    written = _get_store().rebuild(payload)
    for row in rows:
        ledger.set_embedding_meta(
            row["id"], provider.name, provider.version, provider.dimensions
        )
    return written
