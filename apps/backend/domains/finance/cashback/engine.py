"""Cashback engine — evaluate rules and emit earned reward events only."""

from __future__ import annotations

from datetime import date
from typing import Optional

from ..aggregates import CreditCard, Transaction
from ..rewards.aggregates import RewardProgram
from ..rewards.repository_adapters import SqliteRewardEventRepository
from ..rewards.services.event_service import RewardEventService
from ..rewards.services.program_service import RewardProgramService
from .aggregates import CashbackCalculation, CashbackEarnResult, CashbackRule
from .calculator import CashbackCalculator
from .projections import month_bounds
from .validation import validate_cashback_program_unit


class CashbackEngine:
    """Orchestrate deterministic cashback evaluation — never stores balances."""

    def __init__(
        self,
        events: Optional[SqliteRewardEventRepository] = None,
        programs: Optional[RewardProgramService] = None,
    ) -> None:
        self._events = events or SqliteRewardEventRepository()
        self._programs = programs or RewardProgramService()
        self._reward_events = RewardEventService(events=self._events, programs=self._programs)

    def calculate(
        self,
        transaction: Transaction,
        card: CreditCard,
        program: RewardProgram,
        rule: CashbackRule,
        transaction_mcc: Optional[str] = None,
    ) -> CashbackCalculation:
        validate_cashback_program_unit(program.unit)
        monthly_earned = self._monthly_earned_before(program.id, transaction.occurred_on)
        return CashbackCalculator.calculate(
            transaction,
            card,
            program,
            rule,
            monthly_earned_before=monthly_earned,
            transaction_mcc=transaction_mcc,
        )

    def earn_for_transaction(
        self,
        transaction: Transaction,
        card: CreditCard,
        program: RewardProgram,
        rule: CashbackRule,
        transaction_mcc: Optional[str] = None,
        note: Optional[str] = None,
        today: Optional[date] = None,
    ) -> CashbackEarnResult:
        """Evaluate cashback and emit a single earned RewardEvent when due."""
        calculation = self.calculate(
            transaction,
            card,
            program,
            rule,
            transaction_mcc=transaction_mcc,
        )
        if calculation.capped_reward_minor <= 0:
            return CashbackEarnResult(calculation=calculation, reward_event=None)

        reward_event = self._reward_events.create_earned_event(
            program_id=program.id,
            amount=calculation.capped_reward_minor,
            occurred_on=transaction.occurred_on,
            transaction_id=transaction.id,
            note=note or f"cashback rule {rule.id}",
            today=today,
        )
        return CashbackEarnResult(calculation=calculation, reward_event=reward_event)

    def _monthly_earned_before(self, program_id: int, occurred_on: str) -> int:
        start, end = month_bounds(occurred_on)
        return self._events.sum_earned_in_period(program_id, start, end)
