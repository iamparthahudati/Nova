"""Closed enums for the rewards bounded context."""

from __future__ import annotations

from enum import Enum


class RewardUnit(str, Enum):
    POINTS = "points"
    CASHBACK_MINOR = "cashback_minor"


class RewardEventKind(str, Enum):
    EARNED = "earned"
    REDEEMED = "redeemed"
    EXPIRED = "expired"
    ADJUSTED = "adjusted"


class RewardDirection(str, Enum):
    DEBIT = "debit"
    CREDIT = "credit"


KIND_DIRECTION: dict[RewardEventKind, RewardDirection] = {
    RewardEventKind.EARNED: RewardDirection.CREDIT,
    RewardEventKind.REDEEMED: RewardDirection.DEBIT,
    RewardEventKind.EXPIRED: RewardDirection.DEBIT,
}
