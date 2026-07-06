"""Pure MutationEvent builders for cashback operations."""

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


def build_cashback_rule_created(rule) -> MutationEvent:
    row = _row_dict(rule)
    return MutationEvent(
        event_type="finance.cashback.rule.created",
        entity_type="cashback_rule",
        operation="create",
        entity=row,
        metadata=_entity_metadata(row),
    )


def build_cashback_calculated(calculation) -> MutationEvent:
    row = _row_dict(calculation)
    return MutationEvent(
        event_type="finance.cashback.calculated",
        entity_type="cashback_calculation",
        operation="calculate",
        entity=row,
        metadata={
            "program_id": row.get("program_id"),
            "rule_id": row.get("rule_id"),
            "transaction_id": row.get("transaction_id"),
        },
    )


def build_cashback_earned(reward_event) -> MutationEvent:
    row = _row_dict(reward_event)
    return MutationEvent(
        event_type="finance.cashback.earned",
        entity_type="reward_event",
        operation="earn",
        entity=row,
        metadata=_entity_metadata(row),
    )
