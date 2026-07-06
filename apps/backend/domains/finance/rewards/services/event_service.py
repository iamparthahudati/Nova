"""Reward event service — earn, redeem, expire, and manual adjustments."""

from __future__ import annotations

from datetime import date
from typing import Optional

from ..aggregates import RewardEvent
from ..errors import RewardEventNotFoundError
from ..repository_adapters import SqliteRewardEventRepository
from ..validation import (
    direction_for_kind,
    validate_occurred_on,
    validate_reward_amount,
    validate_reward_event_kind,
    validate_sufficient_balance,
)
from ..value_objects import RewardEventKind
from .program_service import RewardProgramService


class RewardEventService:
    def __init__(
        self,
        events: Optional[SqliteRewardEventRepository] = None,
        programs: Optional[RewardProgramService] = None,
    ) -> None:
        self._events = events or SqliteRewardEventRepository()
        self._programs = programs or RewardProgramService()

    def _current_balance(self, program_id: int, as_of: Optional[str] = None) -> int:
        credit, debit = self._events.sum_by_direction(program_id, as_of)
        return credit - debit

    def _write_event(
        self,
        program_id: int,
        kind: RewardEventKind,
        amount: int,
        occurred_on: str,
        direction: Optional[str] = None,
        transaction_id: Optional[int] = None,
        note: Optional[str] = None,
    ) -> RewardEvent:
        resolved_direction = direction_for_kind(kind, direction)
        if resolved_direction == "debit":
            balance = self._current_balance(program_id, as_of=occurred_on)
            validate_sufficient_balance(balance, amount)
        fields = {
            "program_id": program_id,
            "kind": kind.value,
            "direction": resolved_direction,
            "amount": amount,
            "transaction_id": transaction_id,
            "note": note,
            "occurred_on": occurred_on,
        }
        return self._events.create(fields)

    def create_earned_event(
        self,
        program_id: int,
        amount: int,
        occurred_on: str,
        transaction_id: Optional[int] = None,
        note: Optional[str] = None,
        today: Optional[date] = None,
    ) -> RewardEvent:
        today = today or date.today()
        self._programs.get_program(program_id)
        amount = validate_reward_amount(amount)
        occurred = validate_occurred_on(occurred_on, today)
        return self._write_event(
            program_id,
            RewardEventKind.EARNED,
            amount,
            occurred,
            transaction_id=transaction_id,
            note=note,
        )

    def create_redeemed_event(
        self,
        program_id: int,
        amount: int,
        occurred_on: str,
        note: Optional[str] = None,
        today: Optional[date] = None,
    ) -> RewardEvent:
        today = today or date.today()
        self._programs.get_program(program_id)
        amount = validate_reward_amount(amount)
        occurred = validate_occurred_on(occurred_on, today)
        return self._write_event(
            program_id,
            RewardEventKind.REDEEMED,
            amount,
            occurred,
            note=note,
        )

    def create_expired_event(
        self,
        program_id: int,
        amount: int,
        occurred_on: str,
        note: Optional[str] = None,
        today: Optional[date] = None,
    ) -> RewardEvent:
        today = today or date.today()
        self._programs.get_program(program_id)
        amount = validate_reward_amount(amount)
        occurred = validate_occurred_on(occurred_on, today)
        return self._write_event(
            program_id,
            RewardEventKind.EXPIRED,
            amount,
            occurred,
            note=note,
        )

    def create_adjustment(
        self,
        program_id: int,
        amount: int,
        direction: str,
        occurred_on: str,
        note: Optional[str] = None,
        today: Optional[date] = None,
    ) -> RewardEvent:
        """Manual reward adjustment — credit or debit."""
        today = today or date.today()
        self._programs.get_program(program_id)
        amount = validate_reward_amount(amount)
        occurred = validate_occurred_on(occurred_on, today)
        kind = validate_reward_event_kind(RewardEventKind.ADJUSTED.value)
        return self._write_event(
            program_id,
            kind,
            amount,
            occurred,
            direction=direction,
            note=note,
        )

    def get_event(self, event_id: int) -> RewardEvent:
        event = self._events.get_by_id(event_id)
        if event is None:
            raise RewardEventNotFoundError(event_id)
        return event

    def list_events(
        self,
        program_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RewardEvent]:
        self._programs.get_program(program_id)
        return self._events.list_for_program(program_id, limit, offset)

    def delete_event(self, event_id: int) -> RewardEvent:
        event = self.get_event(event_id)
        if not self._events.soft_delete(event_id):
            raise RewardEventNotFoundError(event_id)
        return event

    def compute_balance(self, program_id: int, as_of: Optional[str] = None) -> int:
        self._programs.get_program(program_id)
        return self._current_balance(program_id, as_of)
