"""Memory ranking — the *only* place scoring math lives (ARCHITECTURE_v2 §3).

This module is deliberately pure: it imports no database, no LanceDB, no
embedding provider. It turns numbers (importance, age, access count, optional
similarity) into other numbers (scores) and into a single categorical decision
(which tier a memory belongs in). Everything with an opinion about *how good* a
memory is lives here and nowhere else — `lifecycle.py` and `service.py` only
ever *call* these functions, they never re-derive a score. That is what keeps
"do not scatter ranking logic across multiple files" true in practice.

Two scoring surfaces, sharing one set of components:

  * composite_query_score(...)  — used at recall() time. Blends semantic
    similarity with the durable signals below to re-rank ANN candidates.
  * lifecycle_score(...)        — used at maintenance time, when there is no
    query and therefore no similarity term. Drives tier transitions.

The weights/half-lives/thresholds are a *tuning* problem, not an architecture
problem (§3), so they live in a RankingConfig dataclass. Milestone 2.8's
Learning Engine is explicitly allowed to hand a tuned config in later without
any code change here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

# ── Tiers ────────────────────────────────────────────────────────────────────
# Stored verbatim in memories.tier. String constants (not an enum) to stay
# consistent with the rest of memory/, which uses plain TEXT status columns
# ('open'/'done', 'building'/'shipped'). One canonical spelling, referenced
# everywhere instead of bare literals.

SHORT_TERM = "short_term"
MEDIUM_TERM = "medium_term"
LONG_TERM = "long_term"
ARCHIVED = "archived"
FORGOTTEN = "forgotten"

# Tiers a memory can be recalled from. Archived (cold history) and forgotten
# (soft-deleted) are excluded from recall() but never dropped from SQLite.
ACTIVE_TIERS = (SHORT_TERM, MEDIUM_TERM, LONG_TERM)

# The ladder maintenance moves memories along, hottest → coldest. Used to order
# transitions and to describe an evaluate_memory() result as promote/demote/hold.
TIER_ORDER = (FORGOTTEN, ARCHIVED, SHORT_TERM, MEDIUM_TERM, LONG_TERM)


def tier_rank(tier: str) -> int:
    """Position on the cold→hot ladder; higher = more durable. Unknown → -1."""
    return TIER_ORDER.index(tier) if tier in TIER_ORDER else -1


# ── Config ───────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class RankingConfig:
    """All tunable knobs. Frozen so a shared default can't be mutated in place;
    Learning (§7) swaps in a *new* instance rather than editing the live one."""

    # Recency half-life per tier, in hours. Short-term memories are "recent"
    # only for hours; long-term memories decay over months. A memory aging past
    # its tier's half-life is a demotion candidate; one still fresh is safe.
    half_life_hours: dict[str, float] = field(default_factory=lambda: {
        SHORT_TERM: 12.0,        # half a day
        MEDIUM_TERM: 24.0 * 7,   # one week
        LONG_TERM: 24.0 * 90,    # ~three months
        ARCHIVED: 24.0 * 365,    # a year (barely decays; it's already cold)
        FORGOTTEN: 24.0 * 365,
    })

    # access_count is compressed with log1p and saturated at this many hits, so
    # the 2nd recall matters far more than the 200th (diminishing reinforcement).
    access_saturation: float = 20.0

    # Query-time weights (must sum to 1). Similarity dominates — recall is still
    # fundamentally "what's relevant to this query" — but the durable signals
    # break ties and lift proven memories over one-off near-matches.
    w_query_similarity: float = 0.55
    w_query_importance: float = 0.15
    w_query_recency: float = 0.15
    w_query_access: float = 0.15

    # Lifecycle weights (must sum to 1) — no similarity term at maintenance time.
    # Tuned so importance ALONE cannot reach long_term (see promote_threshold):
    # max importance contribution is w_life_importance = 0.35 < 0.66. A memory
    # only earns long_term by also being recent and/or repeatedly accessed —
    # this is §3's "reaches long-term by earning it, not by being born important".
    w_life_importance: float = 0.35
    w_life_recency: float = 0.30
    w_life_access: float = 0.35

    # Tier thresholds on lifecycle_score ∈ [0, 1].
    promote_threshold: float = 0.66   # ≥ → long_term
    medium_threshold: float = 0.33    # ≥ → medium_term
    archive_floor: float = 0.12       # ≥ → short_term; below → archived
    forget_floor: float = 0.05        # archived & below → forgotten (soft delete)

    # Soft-deleted memories survive at least this long before maintenance may
    # hard-purge them — the "recoverable until maintenance runs" guarantee.
    forget_retention_hours: float = 24.0 * 30  # 30 days

    def __post_init__(self) -> None:
        q = self.w_query_similarity + self.w_query_importance + self.w_query_recency + self.w_query_access
        l = self.w_life_importance + self.w_life_recency + self.w_life_access
        if abs(q - 1.0) > 1e-9:
            raise ValueError(f"query weights must sum to 1, got {q}")
        if abs(l - 1.0) > 1e-9:
            raise ValueError(f"lifecycle weights must sum to 1, got {l}")


DEFAULT_CONFIG = RankingConfig()


# ── Component scores (each returns a value in [0, 1]) ─────────────────────────


def _parse_ts(ts: str | None) -> datetime | None:
    if not ts:
        return None
    dt = datetime.fromisoformat(ts)
    # Stored timestamps are UTC ISO strings; tolerate a naive one just in case.
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def recency_decay(reference_ts: str | None, tier: str, now: datetime,
                  config: RankingConfig = DEFAULT_CONFIG) -> float:
    """Exponential decay 0.5**(age / half_life). 1.0 = just now, →0 = ancient.

    `reference_ts` is the more recent of last_accessed_at / created_at (chosen by
    the caller): being recalled makes a memory 'recent' again, which is the
    spaced-repetition signal that lets a re-accessed memory resist demotion.
    """
    ref = _parse_ts(reference_ts)
    if ref is None:
        return 0.0
    half_life = config.half_life_hours.get(tier, config.half_life_hours[SHORT_TERM])
    age_hours = max(0.0, (now - ref).total_seconds() / 3600.0)
    return 0.5 ** (age_hours / half_life)


def access_boost(access_count: int, config: RankingConfig = DEFAULT_CONFIG) -> float:
    """log1p(count) saturated at config.access_saturation, clamped to [0, 1]."""
    if access_count <= 0:
        return 0.0
    return min(1.0, math.log1p(access_count) / math.log1p(config.access_saturation))


def similarity_from_distance(distance: float) -> float:
    """Map an ANN distance (lower = closer) to a similarity in (0, 1].

    Deliberately a metric-agnostic monotone transform (1/(1+d)) rather than a
    cosine reconstruction: it preserves the ANN ordering regardless of whether
    LanceDB is configured for L2 or cosine, and exact calibration of the number
    is a tuning concern (§3), not a correctness one. distance 0 → 1.0.
    """
    return 1.0 / (1.0 + max(0.0, distance))


def initial_importance(source_type: str, metadata: dict | None = None) -> float:
    """The write-time prior (§3): a cheap heuristic from source, not a judgment.

    An explicit profile/goal statement outranks a passing conversational remark.
    This is only a starting point — recency and access decide the memory's fate
    from here. Callers may override by passing importance explicitly to
    remember(); this is just the default when they don't.
    """
    base = {
        "profile": 0.80,
        "goal": 0.80,
        "insight": 0.75,
        "journal": 0.65,
        "reflection": 0.65,
        "conversation": 0.45,
        "task": 0.40,
        "screen": 0.35,   # Vision OCR (§6) — high volume, low per-item signal
    }.get(source_type, 0.50)

    # A caller can nudge the prior via metadata without teaching this function
    # about every future source type.
    if metadata:
        try:
            override = float(metadata.get("importance_hint"))
            base = override
        except (TypeError, ValueError):
            pass
    return max(0.0, min(1.0, base))


# ── Composite scores ─────────────────────────────────────────────────────────


def composite_query_score(*, similarity: float, importance: float,
                          reference_ts: str | None, tier: str,
                          access_count: int, now: datetime,
                          config: RankingConfig = DEFAULT_CONFIG) -> float:
    """Recall-time rank. Blends similarity with the durable lifecycle signals."""
    return (
        config.w_query_similarity * _clamp01(similarity)
        + config.w_query_importance * _clamp01(importance)
        + config.w_query_recency * recency_decay(reference_ts, tier, now, config)
        + config.w_query_access * access_boost(access_count, config)
    )


def lifecycle_score(*, importance: float, reference_ts: str | None, tier: str,
                    access_count: int, now: datetime,
                    config: RankingConfig = DEFAULT_CONFIG) -> float:
    """Maintenance-time score (no query, no similarity). Drives tier transitions."""
    return (
        config.w_life_importance * _clamp01(importance)
        + config.w_life_recency * recency_decay(reference_ts, tier, now, config)
        + config.w_life_access * access_boost(access_count, config)
    )


def target_tier(*, current_tier: str, score: float,
                config: RankingConfig = DEFAULT_CONFIG) -> str:
    """Map a lifecycle score to the tier the memory *should* be in.

    Fully score-driven: there is no "after N accesses, promote" rule anywhere.
    Tier is a monotonic function of the composite score, and the weights above
    guarantee importance alone can't cross promote_threshold. Forgotten memories
    are terminal here (only restore_memory revives them, only maintenance purges
    them), so we never auto-resurrect a soft-deleted row.
    """
    if current_tier == FORGOTTEN:
        return FORGOTTEN
    if score >= config.promote_threshold:
        return LONG_TERM
    if score >= config.medium_threshold:
        return MEDIUM_TERM
    if score >= config.archive_floor:
        return SHORT_TERM
    # Below the archive floor: cold. An already-archived memory that keeps
    # sinking (below forget_floor) becomes a soft-delete candidate.
    if current_tier == ARCHIVED and score < config.forget_floor:
        return FORGOTTEN
    return ARCHIVED


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))
