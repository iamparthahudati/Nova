"""Memory lifecycle — the state machine over `memories` rows (ARCHITECTURE_v2 §3).

This module owns *transitions*, not scoring. It reads a row, asks ranking.py what
tier that row has earned, and writes the change. It contains no weights, no decay
math, no thresholds — every such number lives in ranking.py. It also never
touches LanceDB: soft delete and archival are pure SQLite operations (§2 makes
`deleted_at` the correctness-critical half of deletion, a single UPDATE), and the
one operation that *does* reclaim vectors — the hard purge — hands its victims
back to service.py, which owns the vector store. That keeps the dependency edge
lifecycle → (ledger, ranking) only.

Manual transitions (promote/demote/archive/forget/restore) are explicit operator
overrides. The score-driven path — the one that runs unattended — is
recalculate_scores(), which is what the nightly maintenance job (§8) calls.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from . import ledger, ranking

# Ladder used by the manual promote/demote nudges. The score-driven path uses
# ranking.target_tier() instead; these are just one-rung operator overrides.
_ACTIVE_LADDER = (ranking.SHORT_TERM, ranking.MEDIUM_TERM, ranking.LONG_TERM)


def _now(now: Optional[datetime]) -> datetime:
    return now or datetime.now(timezone.utc)


def _reference_ts(row: dict) -> str:
    """Recency reference: the later of last_accessed_at and created_at.

    A recalled memory becomes 'recent' again — that's the reinforcement signal
    that lets access resist recency decay (§3). ISO-UTC strings sort correctly
    lexicographically, so max() is exact here.
    """
    candidates = [row.get("created_at"), row.get("last_accessed_at")]
    return max(ts for ts in candidates if ts)


def _score(row: dict, now: datetime, config: ranking.RankingConfig) -> float:
    return ranking.lifecycle_score(
        importance=row["importance"],
        reference_ts=_reference_ts(row),
        tier=row["tier"],
        access_count=row["access_count"],
        now=now,
        config=config,
    )


# ── Reinforcement signals ─────────────────────────────────────────────────────


def touch_memory(memory_id: str) -> None:
    """Refresh recency without counting a reinforcement ('seen', not 'used')."""
    ledger.touch(memory_id)


def record_access(ids: str | list[str]) -> None:
    """Reinforce: bump access_count + recency for memories that proved useful.

    This is the seam Brain integration (2.3) will call after a recalled memory
    survives into a response — recall() itself deliberately does NOT call this,
    so near-miss candidates that get discarded are never rewarded (§3).
    """
    if isinstance(ids, str):
        ids = [ids]
    ledger.record_access(ids)


# ── Manual transitions (explicit overrides) ───────────────────────────────────


def promote_memory(memory_id: str) -> Optional[str]:
    """Nudge one rung hotter. Archived → short_term (revive). Returns new tier."""
    row = _require_live(memory_id)
    if row is None:
        return None
    current = row["tier"]
    if current == ranking.ARCHIVED:
        new_tier = ranking.SHORT_TERM
    elif current in _ACTIVE_LADDER:
        idx = _ACTIVE_LADDER.index(current)
        new_tier = _ACTIVE_LADDER[min(idx + 1, len(_ACTIVE_LADDER) - 1)]
    else:
        return current
    ledger.set_tier(memory_id, new_tier)
    return new_tier


def demote_memory(memory_id: str) -> Optional[str]:
    """Nudge one rung colder. Floors at archived (forget_memory does soft-delete)."""
    row = _require_live(memory_id)
    if row is None:
        return None
    current = row["tier"]
    ladder = (*_ACTIVE_LADDER, ranking.ARCHIVED)  # long → medium → short → archived
    order = (ranking.LONG_TERM, ranking.MEDIUM_TERM, ranking.SHORT_TERM, ranking.ARCHIVED)
    if current not in order:
        return current
    idx = order.index(current)
    new_tier = order[min(idx + 1, len(order) - 1)]
    ledger.set_tier(memory_id, new_tier)
    return new_tier


def archive_memory(memory_id: str) -> None:
    """Move straight to cold storage. Kept for history/audit; excluded from recall."""
    if _require_live(memory_id) is not None:
        ledger.set_tier(memory_id, ranking.ARCHIVED)


def forget_memory(memory_id: str) -> None:
    """Soft delete: tombstone + forgotten tier. Invisible to recall immediately,
    recoverable via restore_memory until maintenance purges it (§2)."""
    ledger.soft_delete(memory_id)


def restore_memory(memory_id: str, tier: str = ranking.SHORT_TERM) -> None:
    """Undo a soft delete — clear the tombstone and re-enter the lifecycle."""
    ledger.restore(memory_id, tier)


# ── Score-driven evaluation (the unattended path) ─────────────────────────────


def evaluate_memory(memory_id: str, now: Optional[datetime] = None,
                    config: ranking.RankingConfig = ranking.DEFAULT_CONFIG) -> Optional[dict]:
    """Dry-run: what tier *should* this memory be in, and why? Applies nothing."""
    row = ledger.get(memory_id)
    if row is None or row["deleted_at"] is not None:
        return None
    now = _now(now)
    score = _score(row, now, config)
    recommended = ranking.target_tier(current_tier=row["tier"], score=score, config=config)
    delta = ranking.tier_rank(recommended) - ranking.tier_rank(row["tier"])
    action = "promote" if delta > 0 else "demote" if delta < 0 else "hold"
    return {
        "id": memory_id,
        "current_tier": row["tier"],
        "recommended_tier": recommended,
        "score": round(score, 4),
        "action": action,
    }


def recalculate_scores(now: Optional[datetime] = None,
                       config: ranking.RankingConfig = ranking.DEFAULT_CONFIG) -> dict:
    """Re-tier every active memory from its current score. The core of maintenance.

    Purely score-driven: no memory is promoted or demoted on a hardcoded rule,
    only because its composite lifecycle score crossed a threshold. A row that
    scores below the forget floor while already archived is soft-deleted here
    (deleted_at set) rather than merely relabelled, so it enters the purge queue.
    """
    now = _now(now)
    transitions = []
    for row in ledger.get_active():
        current = row["tier"]
        score = _score(row, now, config)
        target = ranking.target_tier(current_tier=current, score=score, config=config)
        if target == current:
            continue
        if target == ranking.FORGOTTEN:
            ledger.soft_delete(row["id"])
        else:
            ledger.set_tier(row["id"], target)
        transitions.append({
            "id": row["id"], "from": current, "to": target, "score": round(score, 4),
        })
    return {"evaluated": ledger.count(), "transitions": transitions}


def purge_forgotten(now: Optional[datetime] = None,
                    config: ranking.RankingConfig = ranking.DEFAULT_CONFIG) -> list[str]:
    """Hard-delete soft-deleted rows past the retention window. Returns purged ids.

    SQLite side only — the caller (service.maintenance) is responsible for
    dropping the matching vectors, because this module never imports the store.
    Retention is what makes soft delete 'recoverable until maintenance runs':
    nothing is purged until it has been forgotten for forget_retention_hours.
    """
    now = _now(now)
    cutoff = (now - timedelta(hours=config.forget_retention_hours)).isoformat()
    ids = ledger.get_purgeable(cutoff)
    ledger.hard_delete(ids)
    return ids


# ── helpers ───────────────────────────────────────────────────────────────────


def _require_live(memory_id: str) -> Optional[dict]:
    """Fetch a non-deleted row, or None. Manual transitions ignore tombstoned rows
    (restore them first) so an operator can't accidentally resurrect a memory that
    the purge queue is about to reclaim."""
    row = ledger.get(memory_id)
    if row is None or row["deleted_at"] is not None:
        return None
    return row
