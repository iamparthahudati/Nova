"""Derived finance projections — balances and cashflow, never stored."""

from __future__ import annotations

from datetime import date
from typing import Optional

from ..credit_card import AvailableLimit, Utilization
from ..errors import CreditCardNotFoundError, StatementNotFoundError
from ..payments.status import (
    StatementSummary,
    compute_remaining_due,
    compute_statement_status,
)
from ..repository_adapters import (
    SqliteAccountRepository,
    SqliteCreditCardRepository,
    SqliteStatementRepository,
    SqliteTransactionRepository,
)


class ProjectionService:
    def __init__(
        self,
        transactions: Optional[SqliteTransactionRepository] = None,
        accounts: Optional[SqliteAccountRepository] = None,
        cards: Optional[SqliteCreditCardRepository] = None,
        statements: Optional[SqliteStatementRepository] = None,
    ) -> None:
        self._transactions = transactions or SqliteTransactionRepository()
        self._accounts = accounts or SqliteAccountRepository()
        self._cards = cards or SqliteCreditCardRepository()
        self._statements = statements or SqliteStatementRepository()

    def compute_account_balance(self, account_id: int, as_of: Optional[str] = None) -> int:
        account = self._accounts.get_by_id(account_id)
        if account is None:
            return 0
        credit_total, debit_total = self._transactions.sum_by_direction(account_id, as_of)
        return account.opening_balance_minor + credit_total - debit_total

    def compute_utilization(self, account_id: int, as_of: Optional[str] = None) -> Utilization:
        card = self._cards.get_by_id(account_id)
        if card is None:
            raise CreditCardNotFoundError(account_id)
        balance = self.compute_account_balance(account_id, as_of)
        return Utilization.compute(card.profile.credit_limit_minor, balance)

    def compute_available_limit(
        self, account_id: int, as_of: Optional[str] = None
    ) -> AvailableLimit:
        card = self._cards.get_by_id(account_id)
        if card is None:
            raise CreditCardNotFoundError(account_id)
        balance = self.compute_account_balance(account_id, as_of)
        return AvailableLimit.compute(card.profile.credit_limit_minor, balance)

    def compute_statement_spend(self, statement_id: int) -> int:
        debit_total, credit_total = self._statements.sum_statement_spend(statement_id)
        return debit_total - credit_total

    def compute_statement_paid(self, statement_id: int) -> int:
        return self._statements.sum_statement_paid(statement_id)

    def compute_statement_status(self, statement_id: int, today: Optional[date] = None):
        today = today or date.today()
        statement = self._statements.get_by_id(statement_id)
        if statement is None:
            raise StatementNotFoundError(statement_id)
        paid_minor = self.compute_statement_paid(statement_id)
        return compute_statement_status(
            statement.total_due_minor,
            paid_minor,
            statement.due_date,
            today,
        )

    def compute_statement_summary(
        self,
        statement_id: int,
        today: Optional[date] = None,
    ) -> StatementSummary:
        today = today or date.today()
        statement = self._statements.get_by_id(statement_id)
        if statement is None:
            raise StatementNotFoundError(statement_id)
        paid_minor = self.compute_statement_paid(statement_id)
        spend_minor = self.compute_statement_spend(statement_id)
        status = compute_statement_status(
            statement.total_due_minor,
            paid_minor,
            statement.due_date,
            today,
        )
        return StatementSummary(
            statement_id=statement_id,
            spend_minor=spend_minor,
            paid_minor=paid_minor,
            total_due_minor=statement.total_due_minor,
            min_due_minor=statement.min_due_minor,
            remaining_due_minor=compute_remaining_due(
                statement.total_due_minor,
                paid_minor,
            ),
            status=status,
        )

    def list_statement_summaries(
        self,
        account_id: int,
        today: Optional[date] = None,
        limit: int = 24,
    ) -> list[StatementSummary]:
        today = today or date.today()
        statements = self._statements.list_for_account(account_id, limit)
        return [self.compute_statement_summary(statement.id, today) for statement in statements]

    def compute_period_totals(self, start_date: str, end_date: str) -> tuple[float, float]:
        income_minor, expense_minor = self._transactions.totals_between(start_date, end_date)
        return income_minor / 100.0, expense_minor / 100.0

    def list_account_balances(self) -> list[dict]:
        rows = []
        for account in self._accounts.list_live():
            balance_minor = self.compute_account_balance(account.id)
            rows.append(
                {
                    "account_id": account.id,
                    "name": account.name,
                    "type": account.type,
                    "balance_minor": balance_minor,
                    "balance": balance_minor / 100.0,
                },
            )
        return rows

    def list_card_utilization(self) -> list[dict]:
        rows = []
        for card in self._cards.list_live():
            utilization = self.compute_utilization(card.id)
            available = self.compute_available_limit(card.id)
            rows.append(
                {
                    "account_id": card.id,
                    "name": card.name,
                    "credit_limit_minor": card.profile.credit_limit_minor,
                    "outstanding_minor": utilization.outstanding_minor,
                    "available_limit_minor": available.minor,
                    "utilization_ratio": utilization.ratio,
                    "utilization_percent": utilization.percent,
                },
            )
        return rows
