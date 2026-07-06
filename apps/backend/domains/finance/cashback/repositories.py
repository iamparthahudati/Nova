"""Repository interfaces — cashback defines contracts, adapters implement them."""

from __future__ import annotations

from typing import Optional, Protocol

from .aggregates import CashbackRule


class CashbackRuleRepository(Protocol):
    def create(self, fields: dict) -> CashbackRule: ...

    def get_by_id(self, rule_id: int) -> Optional[CashbackRule]: ...

    def list_for_program(self, program_id: int) -> list[CashbackRule]: ...

    def list_for_account(self, account_id: int) -> list[CashbackRule]: ...
