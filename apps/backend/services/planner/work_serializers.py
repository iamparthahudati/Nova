"""WorkOS domain → API dict serializers — no business logic."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any

from domains.work.aggregates import ActionItem, Note, PriorityPolicy, Project, WorkItem
from domains.work.insights import Briefing
from domains.work.planning import PriorityQueue, PriorityQueueEntry


def serialize_entity(entity: Any) -> dict:
    if is_dataclass(entity) and not isinstance(entity, type):
        return asdict(entity)
    if isinstance(entity, dict):
        return dict(entity)
    raise TypeError(f"Cannot serialize {type(entity)!r}")


def serialize_note(note: Note) -> dict:
    return asdict(note)


def serialize_action_item(item: ActionItem) -> dict:
    return asdict(item)


def serialize_project(project: Project) -> dict:
    return asdict(project)


def serialize_work_item(item: WorkItem) -> dict:
    return asdict(item)


def serialize_priority_policy(policy: PriorityPolicy) -> dict:
    return asdict(policy)


def serialize_queue_entry(entry: PriorityQueueEntry) -> dict:
    return {
        "item": asdict(entry.item),
        "score": entry.score,
        "deadline_term": entry.deadline_term,
        "decay_term": entry.decay_term,
        "days_to_deadline": entry.days_to_deadline,
        "idle_days": entry.idle_days,
    }


def serialize_priority_queue(queue: PriorityQueue, limit: int) -> dict:
    entries = queue.top(limit) if limit else queue.entries
    return {"entries": [serialize_queue_entry(entry) for entry in entries]}


def serialize_briefing(briefing: Briefing) -> dict:
    return {
        "generated_at": briefing.generated_at,
        "top_items": [serialize_queue_entry(entry) for entry in briefing.top_items],
        "inbox_count": briefing.inbox_count,
        "open_commitment_count": briefing.open_commitment_count,
        "overdue_hard_deadline_count": briefing.overdue_hard_deadline_count,
    }
