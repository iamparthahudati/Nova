"""Rewards foundation tests — real SQLite, no mocks."""

from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from domains.finance.errors import FinanceValidationError
from domains.finance.rewards import (
    RewardEventService,
    RewardInvariantError,
    RewardProgramService,
    RewardProjectionService,
    build_reward_event_adjusted,
    build_reward_event_created,
    build_reward_program_created,
    build_reward_program_deleted,
    build_reward_program_updated,
)
from domains.finance.rewards.repository_adapters import (
    SqliteRewardEventRepository,
    SqliteRewardProgramRepository,
)
from domains.finance.rewards.rule import RewardRule
from domains.finance.services.credit_card_service import CreditCardService
from memory import _connection
from memory.schema import init_db


class RewardsFoundationTestCase(unittest.TestCase):
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
        self.events = RewardEventService()
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

    def test_reward_program_crud(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(
            card.id,
            "Reward Points",
            "points",
            earn_rate_note="5x on dining",
            expiry_note="Points expire after 2 years",
        )
        event = build_reward_program_created(program)
        self.assertEqual(event.event_type, "finance.reward_program.created")
        self.assertEqual(event.entity_type, "reward_program")
        self.assertEqual(program.account_id, card.id)
        self.assertEqual(program.unit, "points")

        rule = RewardRule.from_program(program)
        self.assertEqual(rule.earn_rate_note, "5x on dining")
        self.assertEqual(rule.expiry_note, "Points expire after 2 years")

        updated = self.programs.update_program(
            program.id,
            name="CashPoints",
            earn_rate_note="1% on all spends",
        )
        update_event = build_reward_program_updated(updated)
        self.assertEqual(update_event.event_type, "finance.reward_program.updated")
        self.assertEqual(updated.name, "CashPoints")

        listed = self.programs.list_programs(card.id)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].id, program.id)

    def test_program_requires_credit_card_account(self) -> None:
        with self.assertRaises(FinanceValidationError):
            self.programs.create_program(1, "Points", "points")

    def test_reward_events_and_computed_balance(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(card.id, "Points", "points")

        earned = self.events.create_earned_event(
            program.id,
            5000,
            "2026-06-01",
            note="June spend",
            today=self.today,
        )
        earn_event = build_reward_event_created(earned)
        self.assertEqual(earn_event.event_type, "finance.reward_event.created")
        self.assertEqual(earned.kind, "earned")
        self.assertEqual(earned.direction, "credit")

        self.events.create_earned_event(program.id, 3000, "2026-07-01", today=self.today)
        balance = self.projections.compute_program_balance(program.id)
        self.assertEqual(balance.balance, 8000)
        self.assertEqual(balance.total_earned, 8000)
        self.assertEqual(balance.available, 8000)

        redeemed = self.events.create_redeemed_event(
            program.id,
            2000,
            "2026-07-05",
            note="Amazon voucher",
            today=self.today,
        )
        self.assertEqual(redeemed.kind, "redeemed")
        self.assertEqual(redeemed.direction, "debit")

        balance = self.projections.compute_program_balance(program.id)
        self.assertEqual(balance.balance, 6000)
        self.assertEqual(balance.total_redeemed, 2000)

    def test_expiry_handling(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(card.id, "Points", "points")
        self.events.create_earned_event(program.id, 10000, "2026-01-01", today=self.today)

        expired = self.events.create_expired_event(
            program.id,
            3000,
            "2026-07-01",
            note="Annual expiry sweep",
            today=self.today,
        )
        self.assertEqual(expired.kind, "expired")
        self.assertEqual(expired.direction, "debit")

        balance = self.projections.compute_program_balance(program.id)
        self.assertEqual(balance.balance, 7000)
        self.assertEqual(balance.total_expired, 3000)

    def test_manual_adjustment(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(card.id, "Cashback", "cashback_minor")
        self.events.create_earned_event(program.id, 50000, "2026-06-01", today=self.today)

        credit_adj = self.events.create_adjustment(
            program.id,
            1000,
            "credit",
            "2026-06-15",
            note="Issuer goodwill credit",
            today=self.today,
        )
        adj_event = build_reward_event_adjusted(credit_adj)
        self.assertEqual(adj_event.event_type, "finance.reward_event.adjusted")
        self.assertEqual(credit_adj.kind, "adjusted")

        debit_adj = self.events.create_adjustment(
            program.id,
            500,
            "debit",
            "2026-06-20",
            note="Correction",
            today=self.today,
        )
        self.assertEqual(debit_adj.direction, "debit")

        balance = self.projections.compute_program_balance(program.id)
        self.assertEqual(balance.balance, 50500)

    def test_insufficient_balance_rejected(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(card.id, "Points", "points")
        self.events.create_earned_event(program.id, 1000, "2026-06-01", today=self.today)

        with self.assertRaises(RewardInvariantError):
            self.events.create_redeemed_event(program.id, 2000, "2026-07-01", today=self.today)

        with self.assertRaises(RewardInvariantError):
            self.events.create_expired_event(program.id, 2000, "2026-07-01", today=self.today)

    def test_future_occurred_on_rejected(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(card.id, "Points", "points")
        with self.assertRaises(FinanceValidationError):
            self.events.create_earned_event(program.id, 100, "2026-12-31", today=self.today)

    def test_program_delete_requires_empty_ledger(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(card.id, "Points", "points")
        self.events.create_earned_event(program.id, 100, "2026-06-01", today=self.today)

        with self.assertRaises(RewardInvariantError):
            self.programs.delete_program(program.id)

        self.events.delete_event(
            self.events.list_events(program.id)[0].id,
        )
        deleted = self.programs.delete_program(program.id)
        delete_event = build_reward_program_deleted(deleted)
        self.assertEqual(delete_event.event_type, "finance.reward_program.deleted")
        self.assertIsNone(self.programs._programs.get_by_id(program.id))

    def test_yearly_earned_projection(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(card.id, "Points", "points")
        self.events.create_earned_event(program.id, 1000, "2026-01-15", today=self.today)
        self.events.create_earned_event(program.id, 2000, "2026-06-15", today=self.today)
        self.events.create_earned_event(program.id, 500, "2025-12-31", today=self.today)

        yearly = self.projections.compute_yearly_earned(
            program.id,
            "2026-01-01",
            "2026-12-31",
        )
        self.assertEqual(yearly, 3000)

    def test_ledger_projection(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(card.id, "Points", "points")
        self.events.create_earned_event(program.id, 1000, "2026-06-01", today=self.today)
        self.events.create_redeemed_event(program.id, 400, "2026-07-01", today=self.today)

        ledger = self.projections.build_ledger(program.id)
        self.assertEqual(ledger.program.id, program.id)
        self.assertEqual(ledger.balance.balance, 600)
        self.assertEqual(len(ledger.events), 2)

    def test_repository_behaviour(self) -> None:
        card = self._create_card()
        program_repo = SqliteRewardProgramRepository()
        event_repo = SqliteRewardEventRepository()

        program = program_repo.create(
            {
                "account_id": card.id,
                "name": "Repo Points",
                "unit": "points",
            },
        )
        self.assertIsNotNone(program_repo.get_by_id(program.id))

        event = event_repo.create(
            {
                "program_id": program.id,
                "kind": "earned",
                "direction": "credit",
                "amount": 750,
                "occurred_on": "2026-06-01",
            },
        )
        credit, debit = event_repo.sum_by_direction(program.id)
        self.assertEqual(credit, 750)
        self.assertEqual(debit, 0)
        self.assertEqual(
            event_repo.sum_earned_in_period(program.id, "2026-01-01", "2026-12-31"), 750
        )

        listed = event_repo.list_for_program(program.id)
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0].id, event.id)

        self.assertTrue(event_repo.soft_delete(event.id))
        self.assertIsNone(event_repo.get_by_id(event.id))
        credit, debit = event_repo.sum_by_direction(program.id)
        self.assertEqual(credit, 0)

    def test_list_all_balances(self) -> None:
        card = self._create_card()
        program = self.programs.create_program(card.id, "Points", "points")
        self.events.create_earned_event(program.id, 2500, "2026-06-01", today=self.today)

        summaries = self.projections.list_all_balances()
        self.assertEqual(len(summaries), 1)
        self.assertEqual(summaries[0]["balance"], 2500)
        self.assertEqual(summaries[0]["program_id"], program.id)
