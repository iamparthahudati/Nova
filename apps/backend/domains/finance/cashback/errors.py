"""Cashback bounded context errors."""

from __future__ import annotations


class CashbackRuleNotFoundError(LookupError):
    def __init__(self, rule_id: int) -> None:
        super().__init__(f"Cashback rule {rule_id} not found")
        self.rule_id = rule_id
