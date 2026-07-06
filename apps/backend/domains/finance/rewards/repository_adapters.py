"""SQLite repository adapters — call memory.finance only."""

from __future__ import annotations

from typing import Optional

from memory.finance import reward_events as event_store
from memory.finance import reward_programs as program_store

from .aggregates import RewardEvent, RewardProgram


class SqliteRewardProgramRepository:
    def create(self, fields: dict) -> RewardProgram:
        return RewardProgram.from_row(program_store.create_reward_program(fields))

    def get_by_id(self, program_id: int) -> Optional[RewardProgram]:
        row = program_store.get_reward_program_by_id(program_id)
        return RewardProgram.from_row(row) if row else None

    def list_live(self, account_id: Optional[int] = None) -> list[RewardProgram]:
        rows = program_store.list_reward_programs(account_id)
        return [RewardProgram.from_row(row) for row in rows]

    def update(self, program_id: int, fields: dict) -> Optional[RewardProgram]:
        row = program_store.update_reward_program(program_id, fields)
        return RewardProgram.from_row(row) if row else None

    def soft_delete(self, program_id: int) -> bool:
        return program_store.soft_delete_reward_program(program_id)

    def count_live_events(self, program_id: int) -> int:
        return program_store.count_live_reward_events(program_id)


class SqliteRewardEventRepository:
    def create(self, fields: dict) -> RewardEvent:
        return RewardEvent.from_row(event_store.create_reward_event(fields))

    def get_by_id(self, event_id: int) -> Optional[RewardEvent]:
        row = event_store.get_reward_event_by_id(event_id)
        return RewardEvent.from_row(row) if row else None

    def list_for_program(
        self,
        program_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RewardEvent]:
        rows = event_store.list_reward_events(program_id, limit, offset)
        return [RewardEvent.from_row(row) for row in rows]

    def sum_by_direction(
        self,
        program_id: int,
        as_of: Optional[str] = None,
    ) -> tuple[int, int]:
        return event_store.sum_by_direction(program_id, as_of)

    def sum_earned_in_period(
        self,
        program_id: int,
        start_date: str,
        end_date: str,
    ) -> int:
        return event_store.sum_earned_in_period(program_id, start_date, end_date)

    def soft_delete(self, event_id: int) -> bool:
        return event_store.soft_delete_reward_event(event_id)
