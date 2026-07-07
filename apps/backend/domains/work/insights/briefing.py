"""Morning Brief shell — deterministic numbers, no Brain (schema §6.7, §10).

Phase 1 proves derivation works before time or clients exist: the brief is a
handful of counts and the top slice of the PriorityQueue. Narrative arrives in
WOS-9. Nothing here is persisted.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..planning.prioritization import PriorityQueue, PriorityQueueEntry

DEFAULT_TOP_N = 5


@dataclass(frozen=True)
class Briefing:
    generated_at: str
    top_items: list[PriorityQueueEntry]
    inbox_count: int
    open_commitment_count: int
    overdue_hard_deadline_count: int


def build_briefing_shell(
    queue: PriorityQueue,
    inbox_count: int,
    now: datetime,
    top_n: int = DEFAULT_TOP_N,
) -> Briefing:
    """Assemble Morning Brief v0. Answers: what matters first today?"""
    today = now.date()
    overdue = sum(
        1
        for entry in queue.entries
        if entry.item.deadline_hardness == "hard"
        and entry.item.deadline_on is not None
        and entry.item.deadline_on < today.isoformat()
    )
    return Briefing(
        generated_at=now.isoformat(),
        top_items=queue.top(top_n),
        inbox_count=inbox_count,
        open_commitment_count=len(queue.entries),
        overdue_hard_deadline_count=overdue,
    )
