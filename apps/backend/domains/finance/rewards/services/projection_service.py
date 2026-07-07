"""Derived reward projections — balances and ledger, never stored."""

from __future__ import annotations

from typing import Optional

from ..ledger import RewardBalance, RewardLedger, compute_balance, fold_event_totals
from ..repository_adapters import SqliteRewardEventRepository, SqliteRewardProgramRepository
from .event_service import RewardEventService
from .program_service import RewardProgramService


class RewardProjectionService:
    def __init__(
        self,
        programs: Optional[SqliteRewardProgramRepository] = None,
        events: Optional[SqliteRewardEventRepository] = None,
        program_service: Optional[RewardProgramService] = None,
        event_service: Optional[RewardEventService] = None,
    ) -> None:
        self._programs = programs or SqliteRewardProgramRepository()
        self._events = events or SqliteRewardEventRepository()
        self._program_service = program_service or RewardProgramService(self._programs)
        self._event_service = event_service or RewardEventService(
            self._events, self._program_service
        )

    def compute_program_balance(
        self,
        program_id: int,
        as_of: Optional[str] = None,
    ) -> RewardBalance:
        program = self._program_service.get_program(program_id)
        credit, debit = self._events.sum_by_direction(program_id, as_of)
        event_rows = self._events.list_for_program(program_id, limit=10_000)
        if as_of is not None:
            event_rows = [event for event in event_rows if event.occurred_on <= as_of]
        _, _, earned, redeemed, expired = fold_event_totals(event_rows)
        return compute_balance(
            program_id,
            program.unit,
            credit,
            debit,
            earned_total=earned,
            redeemed_total=redeemed,
            expired_total=expired,
        )

    def compute_yearly_earned(
        self,
        program_id: int,
        start_date: str,
        end_date: str,
    ) -> int:
        self._program_service.get_program(program_id)
        return self._events.sum_earned_in_period(program_id, start_date, end_date)

    def build_ledger(
        self,
        program_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> RewardLedger:
        program = self._program_service.get_program(program_id)
        balance = self.compute_program_balance(program_id)
        events = tuple(self._events.list_for_program(program_id, limit, offset))
        return RewardLedger(program=program, balance=balance, events=events)

    def list_account_balances(self, account_id: int) -> list[RewardBalance]:
        programs = self._programs.list_live(account_id)
        return [self.compute_program_balance(program.id) for program in programs]

    def list_recent_events(self, limit: int = 5) -> list[dict]:
        return self._events.list_recent(limit)

    def list_all_balances(self) -> list[dict]:
        rows = []
        for program in self._programs.list_live():
            balance = self.compute_program_balance(program.id)
            rows.append(
                {
                    "program_id": program.id,
                    "account_id": program.account_id,
                    "name": program.name,
                    "unit": program.unit,
                    "balance": balance.balance,
                    "total_earned": balance.total_earned,
                    "total_redeemed": balance.total_redeemed,
                    "total_expired": balance.total_expired,
                },
            )
        return rows
