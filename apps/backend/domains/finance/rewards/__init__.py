"""Rewards bounded context — reward programs, events, and derived balances."""

from .aggregates import RewardEvent, RewardProgram
from .errors import RewardEventNotFoundError, RewardInvariantError, RewardProgramNotFoundError
from .ledger import RewardBalance, RewardLedger
from .mutations import (
    build_reward_event_adjusted,
    build_reward_event_created,
    build_reward_event_deleted,
    build_reward_program_created,
    build_reward_program_deleted,
    build_reward_program_updated,
)
from .rule import RewardRule as RewardRuleNotes
from .services import RewardEventService, RewardProgramService, RewardProjectionService

__all__ = [
    "RewardProgram",
    "RewardEvent",
    "RewardBalance",
    "RewardLedger",
    "RewardRuleNotes",
    "RewardProgramService",
    "RewardEventService",
    "RewardProjectionService",
    "RewardProgramNotFoundError",
    "RewardEventNotFoundError",
    "RewardInvariantError",
    "build_reward_program_created",
    "build_reward_program_updated",
    "build_reward_program_deleted",
    "build_reward_event_created",
    "build_reward_event_adjusted",
    "build_reward_event_deleted",
]
