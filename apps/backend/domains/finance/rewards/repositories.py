"""Repository interfaces — rewards defines contracts, adapters implement them."""

from __future__ import annotations

from typing import Optional, Protocol

from .aggregates import RewardEvent, RewardProgram


class RewardProgramRepository(Protocol):
    def create(self, fields: dict) -> RewardProgram: ...

    def get_by_id(self, program_id: int) -> Optional[RewardProgram]: ...

    def list_live(self, account_id: Optional[int] = None) -> list[RewardProgram]: ...

    def update(self, program_id: int, fields: dict) -> Optional[RewardProgram]: ...

    def soft_delete(self, program_id: int) -> bool: ...

    def count_live_events(self, program_id: int) -> int: ...


class RewardEventRepository(Protocol):
    def create(self, fields: dict) -> RewardEvent: ...

    def get_by_id(self, event_id: int) -> Optional[RewardEvent]: ...

    def list_for_program(
        self,
        program_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[RewardEvent]: ...

    def sum_by_direction(
        self,
        program_id: int,
        as_of: Optional[str] = None,
    ) -> tuple[int, int]: ...

    def sum_earned_in_period(
        self,
        program_id: int,
        start_date: str,
        end_date: str,
    ) -> int: ...

    def soft_delete(self, event_id: int) -> bool: ...
