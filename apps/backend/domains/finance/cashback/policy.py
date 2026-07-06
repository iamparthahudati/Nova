"""Cashback qualification policy — spend eligibility and rule selection."""

from __future__ import annotations

from typing import Optional

from ..aggregates import CreditCard, Transaction
from ..rewards.aggregates import RewardProgram
from ..value_objects import Direction
from .aggregates import CashbackRule
from .value_objects import DEFAULT_QUALIFYING_KINDS


class CashbackPolicy:
    """Deterministic spend qualification — no balance or projection I/O."""

    @staticmethod
    def rule_applies_to_card(rule: CashbackRule, card: CreditCard) -> bool:
        if rule.account_id is None:
            return True
        return rule.account_id == card.id

    @staticmethod
    def rule_applies_to_program(rule: CashbackRule, program: RewardProgram) -> bool:
        return rule.program_id == program.id

    @classmethod
    def select_rule(
        cls,
        rules: list[CashbackRule],
        card: CreditCard,
        program: RewardProgram,
    ) -> Optional[CashbackRule]:
        matching = [
            rule
            for rule in rules
            if cls.rule_applies_to_program(rule, program) and cls.rule_applies_to_card(rule, card)
        ]
        if not matching:
            return None
        return matching[0]

    @classmethod
    def qualifies(
        cls,
        transaction: Transaction,
        card: CreditCard,
        program: RewardProgram,
        rule: CashbackRule,
        transaction_mcc: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        if transaction.account_id != card.id:
            return False, "transaction_not_on_card"
        if transaction.account_id != program.account_id:
            return False, "transaction_not_on_program_card"
        if transaction.direction != Direction.DEBIT.value:
            return False, "non_debit_transaction"
        if not cls.rule_applies_to_card(rule, card):
            return False, "card_rule_mismatch"
        if not cls.rule_applies_to_program(rule, program):
            return False, "program_rule_mismatch"

        excluded_kinds = set(rule.excluded_transaction_kinds)
        allowed_kinds = DEFAULT_QUALIFYING_KINDS - excluded_kinds
        if transaction.kind not in allowed_kinds:
            return False, "excluded_transaction_kind"

        if transaction.amount_minor < rule.minimum_spend_minor:
            return False, "below_minimum_spend"

        if (
            transaction.category_id is not None
            and transaction.category_id in rule.excluded_category_ids
        ):
            return False, "excluded_category"

        if (
            transaction.merchant_id is not None
            and transaction.merchant_id in rule.excluded_merchant_ids
        ):
            return False, "excluded_merchant"

        if transaction_mcc is not None and transaction_mcc in rule.excluded_mcc_codes:
            return False, "excluded_mcc"

        return True, None
