"""Cashback engine tests — real SQLite, no mocks."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from domains.finance.cashback import (
    CashbackCalculator,
    CashbackEngine,
    CashbackPolicy,
    CashbackRuleService,
    build_cashback_calculated,
    build_cashback_earned,
    build_cashback_rule_created,
)
from domains.finance.rewards import RewardProgramService, RewardProjectionService
from domains.finance.services.category_service import CategoryService
from domains.finance.services.credit_card_service import CreditCardService
from domains.finance.services.merchant_service import MerchantService
from domains.finance.services.transaction_service import TransactionService
from domains.finance.value_objects import TransactionKind
from memory import _connection
from memory.schema import init_db


class CashbackEngineTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self._tmpdir.name) / "test.db"
        self.lance_path = Path(self._tmpdir.name) / "lancedb"
        self._patches = [
            patch.object(_connection, "DB_PATH", self.db_path),
            patch.object(_connection, "LANCEDB_PATH", self.lance_path),
        ]
        for patcher in self._patches:
            patcher.start()
        _connection.ensure_storage_paths()
        init_db()
        self.today = date(2026, 7, 7)
        self.cards = CreditCardService()
        self.programs = RewardProgramService()
        self.rules = CashbackRuleService()
        self.transactions = TransactionService()
        self.categories = CategoryService()
        self.merchants = MerchantService()
        self.engine = CashbackEngine()
        self.projections = RewardProjectionService()

    def tearDown(self) -> None:
        for patcher in self._patches:
            patcher.stop()
        self._tmpdir.cleanup()

    def _create_card(self):
        return self.cards.create_credit_card(
            name="HDFC Millennia",
            credit_limit_minor=500_000_00,
            statement_day=15,
            due_day_offset=20,
            opening_balance_on="2026-01-01",
            today=self.today,
        )

    def _create_cashback_program(self, card):
        return self.programs.create_program(
            card.id,
            "Cashback",
            "cashback_minor",
            earn_rate_note="1% base",
        )

    def _expense(self, card, amount_minor: int, **kwargs):
        return self.transactions.create_transaction(
            account_id=card.id,
            kind=TransactionKind.EXPENSE.value,
            amount_minor=amount_minor,
            occurred_on=kwargs.pop("occurred_on", "2026-06-15"),
            today=self.today,
            **kwargs,
        )

    def test_flat_cashback(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        rule = self.rules.create_rule(program.id, "Flat 1%", flat_rate_bps=100)
        rule_event = build_cashback_rule_created(rule)
        self.assertEqual(rule_event.event_type, "finance.cashback.rule.created")

        txn = self._expense(card, 10_000_00)
        calc = self.engine.calculate(txn, card, program, rule)
        calc_event = build_cashback_calculated(calc)
        self.assertEqual(calc_event.event_type, "finance.cashback.calculated")
        self.assertEqual(calc.gross_reward_minor, 100_00)
        self.assertEqual(calc.capped_reward_minor, 100_00)
        self.assertTrue(calc.qualified)

    def test_category_cashback_multiplier(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        dining = self.categories.create_category("Dining")
        rule = self.rules.create_rule(
            program.id,
            "Dining 5%",
            flat_rate_bps=100,
            category_multipliers={dining.id: 500},
        )
        txn = self._expense(card, 10_000_00, category_id=dining.id)
        calc = self.engine.calculate(txn, card, program, rule)
        self.assertEqual(calc.effective_bps, 500)
        self.assertEqual(calc.gross_reward_minor, 500_00)

    def test_merchant_cashback_multiplier(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        merchant = self.merchants.create_merchant("Amazon")
        rule = self.rules.create_rule(
            program.id,
            "Amazon 3%",
            flat_rate_bps=100,
            merchant_multipliers={merchant.id: 300},
        )
        txn = self._expense(card, 10_000_00, merchant_id=merchant.id)
        calc = self.engine.calculate(txn, card, program, rule)
        self.assertEqual(calc.effective_bps, 300)
        self.assertEqual(calc.gross_reward_minor, 300_00)

    def test_capped_cashback(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        rule = self.rules.create_rule(
            program.id,
            "Capped",
            flat_rate_bps=100,
            monthly_cap_minor=150_00,
        )
        first = self._expense(card, 10_000_00, occurred_on="2026-06-01")
        first_result = self.engine.earn_for_transaction(
            first, card, program, rule, today=self.today
        )
        self.assertIsNotNone(first_result.reward_event)
        assert first_result.reward_event is not None
        self.assertEqual(first_result.reward_event.amount, 100_00)

        second = self._expense(card, 10_000_00, occurred_on="2026-06-20")
        second_calc = self.engine.calculate(second, card, program, rule)
        self.assertEqual(second_calc.gross_reward_minor, 100_00)
        self.assertEqual(second_calc.capped_reward_minor, 50_00)

        second_result = self.engine.earn_for_transaction(
            second,
            card,
            program,
            rule,
            today=self.today,
        )
        assert second_result.reward_event is not None
        self.assertEqual(second_result.reward_event.amount, 50_00)

        balance = self.projections.compute_program_balance(program.id)
        self.assertEqual(balance.balance, 150_00)

    def test_excluded_transaction_kind(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        rule = self.rules.create_rule(
            program.id,
            "Expense only",
            flat_rate_bps=100,
            excluded_transaction_kinds=["expense"],
        )
        txn = self._expense(card, 5_000_00)
        calc = self.engine.calculate(txn, card, program, rule)
        self.assertFalse(calc.qualified)
        self.assertEqual(calc.exclusion_reason, "excluded_transaction_kind")

        income = self.transactions.create_transaction(
            account_id=card.id,
            kind=TransactionKind.INCOME.value,
            amount_minor=5_000_00,
            occurred_on="2026-06-15",
            today=self.today,
        )
        income_calc = self.engine.calculate(income, card, program, rule)
        self.assertFalse(income_calc.qualified)
        self.assertEqual(income_calc.exclusion_reason, "non_debit_transaction")

    def test_minimum_spend(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        rule = self.rules.create_rule(
            program.id,
            "Min spend",
            flat_rate_bps=100,
            minimum_spend_minor=1_000_00,
        )
        txn = self._expense(card, 500_00)
        calc = self.engine.calculate(txn, card, program, rule)
        self.assertFalse(calc.qualified)
        self.assertEqual(calc.exclusion_reason, "below_minimum_spend")

    def test_reward_event_generation(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        rule = self.rules.create_rule(program.id, "Earn", flat_rate_bps=100)
        txn = self._expense(card, 2_000_00)
        result = self.engine.earn_for_transaction(txn, card, program, rule, today=self.today)

        assert result.reward_event is not None
        earned_event = build_cashback_earned(result.reward_event)
        self.assertEqual(earned_event.event_type, "finance.cashback.earned")
        self.assertEqual(earned_event.entity_type, "reward_event")
        self.assertEqual(result.reward_event.kind, "earned")
        self.assertEqual(result.reward_event.direction, "credit")
        self.assertEqual(result.reward_event.transaction_id, txn.id)
        self.assertEqual(result.reward_event.amount, 20_00)

        balance = self.projections.compute_program_balance(program.id)
        self.assertEqual(balance.balance, 20_00)

    def test_deterministic_calculations(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        dining = self.categories.create_category("Dining")
        merchant = self.merchants.create_merchant("Swiggy")
        rule = self.rules.create_rule(
            program.id,
            "Stacked",
            flat_rate_bps=100,
            category_multipliers={dining.id: 200},
            merchant_multipliers={merchant.id: 150},
        )
        txn = self._expense(
            card,
            12_345_67,
            category_id=dining.id,
            merchant_id=merchant.id,
        )
        first = CashbackCalculator.calculate(txn, card, program, rule)
        second = CashbackCalculator.calculate(txn, card, program, rule)
        self.assertEqual(first, second)
        self.assertEqual(first.effective_bps, 300)
        self.assertEqual(first.gross_reward_minor, 370_37)

    def test_excluded_category(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        fuel = self.categories.create_category("Fuel")
        rule = self.rules.create_rule(
            program.id,
            "No fuel",
            flat_rate_bps=100,
            excluded_category_ids=[fuel.id],
        )
        txn = self._expense(card, 3_000_00, category_id=fuel.id)
        calc = self.engine.calculate(txn, card, program, rule)
        self.assertFalse(calc.qualified)
        self.assertEqual(calc.exclusion_reason, "excluded_category")

    def test_card_specific_rule(self) -> None:
        card_a = self._create_card()
        card_b = self.cards.create_credit_card(
            name="ICICI Amazon",
            credit_limit_minor=300_000_00,
            statement_day=10,
            due_day_offset=18,
            opening_balance_on="2026-01-01",
            today=self.today,
        )
        program = self._create_cashback_program(card_a)
        rule = self.rules.create_rule(
            program.id,
            "Card A only",
            flat_rate_bps=100,
            account_id=card_a.id,
        )
        txn_a = self._expense(card_a, 1_000_00)
        txn_b = self._expense(card_b, 1_000_00)
        self.assertTrue(CashbackPolicy.qualifies(txn_a, card_a, program, rule)[0])
        self.assertFalse(CashbackPolicy.qualifies(txn_b, card_b, program, rule)[0])

    def test_excluded_mcc(self) -> None:
        card = self._create_card()
        program = self._create_cashback_program(card)
        rule = self.rules.create_rule(
            program.id,
            "No MCC",
            flat_rate_bps=100,
            excluded_mcc_codes=["6011"],
        )
        txn = self._expense(card, 4_000_00)
        calc = self.engine.calculate(txn, card, program, rule, transaction_mcc="6011")
        self.assertFalse(calc.qualified)
        self.assertEqual(calc.exclusion_reason, "excluded_mcc")

        allowed = self.engine.calculate(txn, card, program, rule, transaction_mcc="5411")
        self.assertTrue(allowed.qualified)
        self.assertEqual(allowed.gross_reward_minor, 40_00)


if __name__ == "__main__":
    unittest.main()
