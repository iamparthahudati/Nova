"""Finance domain → API dict serializers — no business logic."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any, Optional


def _minor_to_rupees(minor: int) -> float:
    return minor / 100.0


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return serialize_entity(value)
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    return value


def serialize_entity(entity: Any) -> dict:
    if hasattr(entity, "__dataclass_fields__"):
        return _serialize_value(asdict(entity))
    if isinstance(entity, dict):
        return _serialize_value(dict(entity))
    raise TypeError(f"Cannot serialize {type(entity)!r}")


def serialize_account(account, *, balance_minor: Optional[int] = None) -> dict:
    row = serialize_entity(account)
    if balance_minor is not None:
        row["balance_minor"] = balance_minor
        row["balance"] = _minor_to_rupees(balance_minor)
    return row


def serialize_credit_card(
    card,
    *,
    balance_minor: Optional[int] = None,
    utilization: Optional[Any] = None,
    available_limit_minor: Optional[int] = None,
) -> dict:
    row = {
        "account_id": card.id,
        "name": card.name,
        "type": card.account.type,
        "network": card.profile.network,
        "last4": card.profile.last4,
        "credit_limit_minor": card.profile.credit_limit_minor,
        "credit_limit": _minor_to_rupees(card.profile.credit_limit_minor),
        "statement_day": card.profile.statement_day,
        "due_day_offset": card.profile.due_day_offset,
        "autopay": card.profile.autopay,
        "opening_balance_minor": card.account.opening_balance_minor,
        "opening_balance_on": card.account.opening_balance_on,
        "archived_at": card.account.archived_at,
        "created_at": card.account.created_at,
        "updated_at": card.account.updated_at,
    }
    if balance_minor is not None:
        row["balance_minor"] = balance_minor
        row["balance"] = _minor_to_rupees(balance_minor)
    if utilization is not None:
        row["outstanding_minor"] = utilization.outstanding_minor
        row["outstanding"] = _minor_to_rupees(utilization.outstanding_minor)
        row["utilization_ratio"] = utilization.ratio
        row["utilization_percent"] = utilization.percent
    if available_limit_minor is not None:
        row["available_limit_minor"] = available_limit_minor
        row["available_limit"] = _minor_to_rupees(available_limit_minor)
    return row


def serialize_transfer_group(legs: list, transfer_group_id: str) -> dict:
    return {
        "legs": [serialize_transaction(leg) for leg in legs],
        "transfer_group_id": transfer_group_id,
    }


def serialize_statement(statement, summary: Optional[Any] = None) -> dict:
    row = serialize_entity(statement)
    if summary is not None:
        row["spend_minor"] = summary.spend_minor
        row["spend"] = _minor_to_rupees(summary.spend_minor)
        row["paid_minor"] = summary.paid_minor
        row["paid"] = _minor_to_rupees(summary.paid_minor)
        row["remaining_due_minor"] = summary.remaining_due_minor
        if summary.remaining_due_minor is not None:
            row["remaining_due"] = _minor_to_rupees(summary.remaining_due_minor)
        row["status"] = summary.status.value
    return row


def serialize_transaction(
    txn,
    *,
    account_name: Optional[str] = None,
    category_name: Optional[str] = None,
    merchant_name: Optional[str] = None,
) -> dict:
    row = serialize_entity(txn)
    row["amount"] = _minor_to_rupees(txn.amount_minor)
    if account_name is not None:
        row["account_name"] = account_name
    if category_name is not None:
        row["category_name"] = category_name
    if merchant_name is not None:
        row["merchant_name"] = merchant_name
    return row


def serialize_reward_program(program) -> dict:
    return serialize_entity(program)


def serialize_reward_balance(balance) -> dict:
    return serialize_entity(balance)


def serialize_reward_event(event) -> dict:
    return serialize_entity(event)


def serialize_cashback_rule(rule) -> dict:
    row = serialize_entity(rule)
    row["flat_rate_percent"] = rule.flat_rate_bps / 100.0
    if rule.monthly_cap_minor is not None:
        row["monthly_cap"] = _minor_to_rupees(rule.monthly_cap_minor)
    row["minimum_spend"] = _minor_to_rupees(rule.minimum_spend_minor)
    return row
