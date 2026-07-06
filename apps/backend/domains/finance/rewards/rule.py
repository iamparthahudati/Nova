"""Reward rule notes — free-text policy, not a calculation engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RewardRule:
    """Earn-rate and expiry policy stored as notes on a program."""

    earn_rate_note: Optional[str]
    expiry_note: Optional[str]

    @classmethod
    def from_program(cls, program) -> RewardRule:
        return cls(
            earn_rate_note=program.earn_rate_note,
            expiry_note=program.expiry_note,
        )
