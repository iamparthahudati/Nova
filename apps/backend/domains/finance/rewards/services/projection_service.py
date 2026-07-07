"""Derived reward projections — balances and ledger, never stored."""

from __future__ import annotations

from datetime import date
from typing import Optional

from ..ledger import (
    RewardBalance,
    RewardLedger,
    compute_balance,
    derive_program_status,
    fold_event_totals,
    fold_monthly_activity,
)
from ..repository_adapters import SqliteRewardEventRepository, SqliteRewardProgramRepository
from .event_service import RewardEventService
from .program_service import RewardProgramService


def _month_bounds(occurred_on: str) -> tuple[str, str]:
    occurred = date.fromisoformat(occurred_on)
    start = occurred.replace(day=1).isoformat()
    if occurred.month == 12:
        end = occurred.replace(year=occurred.year + 1, month=1, day=1)
    else:
        end = occurred.replace(month=occurred.month + 1, day=1)
    last_day = end.fromordinal(end.toordinal() - 1)
    return start, last_day.isoformat()


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

    def build_overview(self, today: date) -> dict:
        month_start, month_end = _month_bounds(today.isoformat())
        year_start = today.replace(month=1, day=1).isoformat()
        year_end = today.isoformat()

        total_balance = 0
        total_balance_cashback_minor = 0
        earned_month = 0
        earned_year = 0
        earned_lifetime = 0
        earned_month_cashback_minor = 0
        earned_year_cashback_minor = 0
        earned_lifetime_cashback_minor = 0

        for program in self._programs.list_live():
            balance = self.compute_program_balance(program.id)
            if program.unit == "cashback_minor":
                total_balance_cashback_minor += balance.balance
                earned_month_cashback_minor += self.compute_yearly_earned(
                    program.id,
                    month_start,
                    month_end,
                )
                earned_year_cashback_minor += self.compute_yearly_earned(
                    program.id,
                    year_start,
                    year_end,
                )
                earned_lifetime_cashback_minor += balance.total_earned
            else:
                total_balance += balance.balance
                earned_month += self.compute_yearly_earned(program.id, month_start, month_end)
                earned_year += self.compute_yearly_earned(program.id, year_start, year_end)
                earned_lifetime += balance.total_earned

        return {
            "total_balance": total_balance,
            "total_balance_cashback_minor": total_balance_cashback_minor,
            "earned_month": earned_month,
            "earned_year": earned_year,
            "earned_lifetime": earned_lifetime,
            "earned_month_cashback_minor": earned_month_cashback_minor,
            "earned_year_cashback_minor": earned_year_cashback_minor,
            "earned_lifetime_cashback_minor": earned_lifetime_cashback_minor,
        }

    def build_program_detail(
        self,
        program_id: int,
        today: date,
        history_months: int = 6,
        event_limit: int = 50,
    ) -> dict:
        program = self._program_service.get_program(program_id)
        balance = self.compute_program_balance(program_id)
        month_start, month_end = _month_bounds(today.isoformat())
        year_start = today.replace(month=1, day=1).isoformat()
        year_end = today.isoformat()
        all_events = self._events.list_for_program(program_id, limit=10_000)
        recent_events = tuple(all_events[:event_limit])
        monthly_history = fold_monthly_activity(all_events, history_months, today)
        transaction_ids = [
            event.transaction_id for event in recent_events if event.transaction_id is not None
        ]
        unique_txn_ids = list(dict.fromkeys(transaction_ids))[:10]
        return {
            "program": program,
            "balance": balance,
            "status": derive_program_status(
                balance.balance,
                balance.total_earned,
                program.expiry_note,
            ),
            "earned_month": self.compute_yearly_earned(program_id, month_start, month_end),
            "earned_year": self.compute_yearly_earned(program_id, year_start, year_end),
            "earned_lifetime": balance.total_earned,
            "monthly_history": monthly_history,
            "recent_events": recent_events,
            "related_transaction_ids": unique_txn_ids,
        }
