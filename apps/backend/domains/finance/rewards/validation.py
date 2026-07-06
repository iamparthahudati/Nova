"""Reward validation — pure, no I/O."""

from __future__ import annotations

from datetime import date

from ..errors import FinanceValidationError
from ..value_objects import Direction
from .errors import RewardInvariantError
from .value_objects import KIND_DIRECTION, RewardEventKind, RewardUnit


def validate_program_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise FinanceValidationError("Reward program name is required")
    return cleaned


def validate_reward_unit(unit: str) -> str:
    try:
        return RewardUnit(unit).value
    except ValueError as exc:
        raise FinanceValidationError(f"Invalid reward unit: {unit}") from exc


def validate_reward_amount(amount: int) -> int:
    if amount <= 0:
        raise FinanceValidationError("Reward amount must be positive")
    return amount


def validate_reward_event_kind(kind: str) -> RewardEventKind:
    try:
        return RewardEventKind(kind)
    except ValueError as exc:
        raise FinanceValidationError(f"Invalid reward event kind: {kind}") from exc


def direction_for_kind(
    kind: RewardEventKind,
    explicit: str | None = None,
) -> str:
    if kind == RewardEventKind.ADJUSTED:
        if explicit not in {Direction.DEBIT.value, Direction.CREDIT.value}:
            raise FinanceValidationError("Adjustment requires explicit direction")
        return explicit
    return KIND_DIRECTION[kind].value


def validate_occurred_on(occurred_on: str, today: date) -> str:
    occurred = date.fromisoformat(occurred_on)
    if occurred > today:
        raise FinanceValidationError("Reward event occurred_on cannot be in the future")
    return occurred_on


def validate_sufficient_balance(
    current_balance: int,
    debit_amount: int,
) -> None:
    if debit_amount > current_balance:
        raise RewardInvariantError(
            f"Insufficient reward balance: {current_balance} available, "
            f"{debit_amount} requested",
        )
