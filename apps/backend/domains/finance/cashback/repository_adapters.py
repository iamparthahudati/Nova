"""SQLite repository adapters — call memory.finance only."""

from __future__ import annotations

from typing import Optional

from memory.finance import cashback_rules as rule_store

from .aggregates import CashbackRule


class SqliteCashbackRuleRepository:
    def create(self, fields: dict) -> CashbackRule:
        return CashbackRule.from_row(rule_store.create_cashback_rule(fields))

    def get_by_id(self, rule_id: int) -> Optional[CashbackRule]:
        row = rule_store.get_cashback_rule_by_id(rule_id)
        return CashbackRule.from_row(row) if row else None

    def list_for_program(self, program_id: int) -> list[CashbackRule]:
        rows = rule_store.list_cashback_rules(program_id=program_id)
        return [CashbackRule.from_row(row) for row in rows]

    def list_for_account(self, account_id: int) -> list[CashbackRule]:
        rows = rule_store.list_cashback_rules(account_id=account_id)
        return [CashbackRule.from_row(row) for row in rows]
