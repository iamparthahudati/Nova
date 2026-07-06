"""Pure MutationEvent builders for reward operations."""

from __future__ import annotations

from runtime.mutation_event import MutationEvent


def _entity_metadata(row: dict) -> dict:
    entity_id = row.get("id")
    return {"entity_id": entity_id} if entity_id is not None else {}


def _row_dict(entity) -> dict:
    if hasattr(entity, "__dataclass_fields__"):
        from dataclasses import asdict

        return asdict(entity)
    return dict(entity)


def build_reward_program_created(program) -> MutationEvent:
    row = _row_dict(program)
    return MutationEvent(
        event_type="finance.reward_program.created",
        entity_type="reward_program",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_reward_program_updated(program) -> MutationEvent:
    row = _row_dict(program)
    return MutationEvent(
        event_type="finance.reward_program.updated",
        entity_type="reward_program",
        operation="update",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_reward_program_deleted(program) -> MutationEvent:
    row = _row_dict(program)
    return MutationEvent(
        event_type="finance.reward_program.deleted",
        entity_type="reward_program",
        operation="delete",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_reward_event_created(event) -> MutationEvent:
    row = _row_dict(event)
    return MutationEvent(
        event_type="finance.reward_event.created",
        entity_type="reward_event",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_reward_event_adjusted(event) -> MutationEvent:
    row = _row_dict(event)
    return MutationEvent(
        event_type="finance.reward_event.adjusted",
        entity_type="reward_event",
        operation="adjust",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_reward_event_deleted(event) -> MutationEvent:
    row = _row_dict(event)
    return MutationEvent(
        event_type="finance.reward_event.deleted",
        entity_type="reward_event",
        operation="delete",
        entity=row,
        metadata=_entity_metadata(row),
    )
