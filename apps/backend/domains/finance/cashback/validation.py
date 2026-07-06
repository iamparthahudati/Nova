"""Cashback validation — pure, no I/O."""

from __future__ import annotations

from ..errors import FinanceValidationError
from ..rewards.value_objects import RewardUnit


def validate_rule_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise FinanceValidationError("Cashback rule name is required")
    return cleaned


def validate_flat_rate_bps(flat_rate_bps: int) -> int:
    if flat_rate_bps < 0:
        raise FinanceValidationError("Flat rate basis points cannot be negative")
    return flat_rate_bps


def validate_minimum_spend_minor(minimum_spend_minor: int) -> int:
    if minimum_spend_minor < 0:
        raise FinanceValidationError("Minimum spend cannot be negative")
    return minimum_spend_minor


def validate_monthly_cap_minor(monthly_cap_minor: int | None) -> int | None:
    if monthly_cap_minor is not None and monthly_cap_minor <= 0:
        raise FinanceValidationError("Monthly cap must be positive when set")
    return monthly_cap_minor


def validate_cashback_program_unit(unit: str) -> None:
    if unit != RewardUnit.CASHBACK_MINOR.value:
        raise FinanceValidationError(
            "Cashback engine requires a reward program with unit cashback_minor",
        )


def validate_multiplier_map(multipliers: dict[int, int]) -> dict[int, int]:
    for key, value in multipliers.items():
        if key <= 0:
            raise FinanceValidationError("Multiplier keys must be positive identifiers")
        if value <= 0:
            raise FinanceValidationError("Multipliers must be positive")
    return multipliers
