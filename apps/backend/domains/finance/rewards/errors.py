"""Rewards bounded context errors."""

from __future__ import annotations

from ..errors import FinanceValidationError


class RewardProgramNotFoundError(LookupError):
    def __init__(self, program_id: int) -> None:
        super().__init__(f"Reward program {program_id} not found")
        self.program_id = program_id


class RewardEventNotFoundError(LookupError):
    def __init__(self, event_id: int) -> None:
        super().__init__(f"Reward event {event_id} not found")
        self.event_id = event_id


class RewardInvariantError(FinanceValidationError):
    """Reward program or event invariant violated."""
