"""Deterministic PriorityQueue — pure, no I/O, injected clock (ADR 0023).

Phase 1 uses two terms only (schema §10): a deadline-urgency term and a
staleness-decay term, each scaled by the active PriorityPolicy weights. No
strategic, revenue, or blocking terms exist yet. Nothing here is persisted;
the queue is recomputed on every read.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from ..aggregates import PriorityPolicy, WorkItem

# Days out at which a deadline starts contributing urgency. A deadline further
# away than this adds nothing; an overdue one contributes more than the horizon.
DEADLINE_HORIZON_DAYS = 14
_HARDNESS_MULTIPLIER = {"hard": 2, "soft": 1}


@dataclass(frozen=True)
class PriorityQueueEntry:
    item: WorkItem
    score: int
    deadline_term: int
    decay_term: int
    days_to_deadline: Optional[int]
    idle_days: int


@dataclass(frozen=True)
class PriorityQueue:
    entries: list[PriorityQueueEntry]

    def top(self, limit: int) -> list[PriorityQueueEntry]:
        return self.entries[:limit]


def build_priority_queue(
    items: list[WorkItem],
    policy: PriorityPolicy,
    now: datetime,
) -> PriorityQueue:
    """Rank open commitments highest-first. Answers: what should I work on today?"""
    today = now.date()
    scored = [_score_item(item, policy, today) for item in items]
    scored.sort(key=_ordering_key)
    return PriorityQueue(entries=scored)


def _score_item(item: WorkItem, policy: PriorityPolicy, today: date) -> PriorityQueueEntry:
    days_to_deadline = _days_to_deadline(item, today)
    deadline_factor = _deadline_factor(days_to_deadline, item.deadline_hardness)
    idle_days = _idle_days(item.updated_at, today)
    deadline_term = policy.deadline_weight * deadline_factor
    decay_term = policy.decay_weight * idle_days
    return PriorityQueueEntry(
        item=item,
        score=deadline_term + decay_term,
        deadline_term=deadline_term,
        decay_term=decay_term,
        days_to_deadline=days_to_deadline,
        idle_days=idle_days,
    )


def _days_to_deadline(item: WorkItem, today: date) -> Optional[int]:
    if item.deadline_on is None:
        return None
    return (date.fromisoformat(item.deadline_on) - today).days


def _deadline_factor(days_to_deadline: Optional[int], hardness: Optional[str]) -> int:
    if days_to_deadline is None:
        return 0
    urgency = max(0, DEADLINE_HORIZON_DAYS - days_to_deadline)
    return urgency * _HARDNESS_MULTIPLIER.get(hardness or "soft", 1)


def _idle_days(updated_at: str, today: date) -> int:
    updated = datetime.fromisoformat(updated_at).date()
    return max(0, (today - updated).days)


def _ordering_key(entry: PriorityQueueEntry) -> tuple[int, int, int]:
    # Highest score first; break ties by soonest deadline, then stable by id.
    deadline_rank = entry.days_to_deadline if entry.days_to_deadline is not None else 10**6
    return (-entry.score, deadline_rank, entry.item.id)
