"""Cashback bounded context — deterministic earn rule evaluation."""

from .aggregates import CashbackCalculation, CashbackEarnResult, CashbackRule
from .calculator import CashbackCalculator
from .engine import CashbackEngine
from .errors import CashbackRuleNotFoundError
from .mutations import (
    build_cashback_calculated,
    build_cashback_earned,
    build_cashback_rule_created,
)
from .policy import CashbackPolicy
from .services import CashbackRuleService

__all__ = [
    "CashbackRule",
    "CashbackCalculation",
    "CashbackEarnResult",
    "CashbackCalculator",
    "CashbackPolicy",
    "CashbackEngine",
    "CashbackRuleService",
    "CashbackRuleNotFoundError",
    "build_cashback_rule_created",
    "build_cashback_calculated",
    "build_cashback_earned",
]
