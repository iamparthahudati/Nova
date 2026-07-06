"""REST-side translators — domain rows to MutationEvent. No I/O, no side effects."""

from __future__ import annotations

from .mutation_event import MutationEvent


def _entity_metadata(row: dict) -> dict:
    entity_id = row.get("id")
    return {"entity_id": entity_id} if entity_id is not None else {}


def build_task_created(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="task.created",
        entity_type="task",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_task_completed(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="task.updated",
        entity_type="task",
        operation="complete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_reminder_created(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="reminder.created",
        entity_type="reminder",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_spending_logged(row: dict) -> MutationEvent:
    return MutationEvent(
        event_type="spending.logged",
        entity_type="money",
        operation="log",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_pomodoro_completed(minutes: int) -> MutationEvent:
    entity = {"minutes": minutes}
    return MutationEvent(
        event_type="pomodoro.completed",
        entity_type="automation",
        operation="complete",
        entity=entity,
        metadata={"minutes": minutes},
    )
