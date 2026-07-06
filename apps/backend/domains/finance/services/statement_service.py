"""Statement aggregate service — cycle generation and CRUD."""

from __future__ import annotations

from datetime import date
from typing import Optional

from ..aggregates import Statement
from ..cycle import BillingCycle, compute_billing_cycle, compute_previous_billing_cycle
from ..errors import (
    CreditCardNotFoundError,
    StatementInvariantError,
    StatementNotFoundError,
)
from ..repository_adapters import SqliteCreditCardRepository, SqliteStatementRepository
from ..validation import validate_statement_dates, validate_statement_totals


class StatementService:
    def __init__(
        self,
        statements: Optional[SqliteStatementRepository] = None,
        cards: Optional[SqliteCreditCardRepository] = None,
    ) -> None:
        self._statements = statements or SqliteStatementRepository()
        self._cards = cards or SqliteCreditCardRepository()

    def _require_card(self, account_id: int):
        card = self._cards.get_by_id(account_id)
        if card is None:
            raise CreditCardNotFoundError(account_id)
        return card

    def _billing_cycle_for(self, account_id: int, reference: date) -> BillingCycle:
        card = self._require_card(account_id)
        return compute_billing_cycle(
            card.profile.statement_day,
            card.profile.due_day_offset,
            reference,
        )

    def generate_statement(
        self,
        account_id: int,
        reference: Optional[date] = None,
    ) -> Statement:
        """Create the billing-cycle statement row for reference if absent."""
        statement, _created = self.generate_statement_with_status(account_id, reference)
        return statement

    def generate_statement_with_status(
        self,
        account_id: int,
        reference: Optional[date] = None,
    ) -> tuple[Statement, bool]:
        """Return statement and whether a new row was created."""
        reference = reference or date.today()
        billing = self._billing_cycle_for(account_id, reference)
        existing = self._statements.get_by_period(account_id, billing.period_start)
        if existing is not None:
            return existing, False
        return self._create_from_billing(account_id, billing), True

    def generate_previous_statement(
        self,
        account_id: int,
        reference: Optional[date] = None,
    ) -> Statement:
        """Ensure the cycle before the current one exists."""
        statement, _created = self.generate_previous_statement_with_status(account_id, reference)
        return statement

    def generate_previous_statement_with_status(
        self,
        account_id: int,
        reference: Optional[date] = None,
    ) -> tuple[Statement, bool]:
        """Return previous-cycle statement and whether a new row was created."""
        reference = reference or date.today()
        current = self._billing_cycle_for(account_id, reference)
        card = self._require_card(account_id)
        previous = compute_previous_billing_cycle(
            card.profile.statement_day,
            card.profile.due_day_offset,
            current,
        )
        existing = self._statements.get_by_period(account_id, previous.period_start)
        if existing is not None:
            return existing, False
        return self._create_from_billing(account_id, previous), True

    def ensure_current_and_previous(
        self,
        account_id: int,
        today: Optional[date] = None,
    ) -> tuple[Statement, Optional[Statement], list[Statement]]:
        """Lazy sweep: current statement plus previous when available."""
        today = today or date.today()
        created: list[Statement] = []
        current, was_created = self.generate_statement_with_status(account_id, today)
        if was_created:
            created.append(current)
        previous, was_created = self.generate_previous_statement_with_status(account_id, today)
        if was_created and previous.id != current.id:
            created.append(previous)
        if previous.id == current.id:
            return current, None, created
        return current, previous, created

    def get_current_statement(self, account_id: int, today: Optional[date] = None) -> Statement:
        today = today or date.today()
        return self.generate_statement(account_id, today)

    def get_previous_statement(
        self, account_id: int, today: Optional[date] = None
    ) -> Optional[Statement]:
        today = today or date.today()
        current = self.get_current_statement(account_id, today)
        statements = self._statements.list_for_account(account_id, limit=2)
        for statement in statements:
            if statement.id != current.id:
                return statement
        return None

    def get_statement(self, statement_id: int) -> Statement:
        statement = self._statements.get_by_id(statement_id)
        if statement is None:
            raise StatementNotFoundError(statement_id)
        return statement

    def list_statements(self, account_id: int, limit: int = 24) -> list[Statement]:
        self._require_card(account_id)
        return self._statements.list_for_account(account_id, limit)

    def update_statement(
        self,
        statement_id: int,
        total_due_minor: Optional[int] = None,
        min_due_minor: Optional[int] = None,
    ) -> Statement:
        self.get_statement(statement_id)
        validate_statement_totals(total_due_minor, min_due_minor)
        fields: dict = {}
        if total_due_minor is not None:
            fields["total_due_minor"] = total_due_minor
        if min_due_minor is not None:
            fields["min_due_minor"] = min_due_minor
        updated = self._statements.update(statement_id, fields)
        if updated is None:
            raise StatementNotFoundError(statement_id)
        return updated

    def delete_statement(self, statement_id: int) -> Statement:
        statement = self.get_statement(statement_id)
        if self._statements.count_linked_transactions(statement_id) > 0:
            raise StatementInvariantError(
                "Cannot delete a statement with linked transactions",
            )
        if not self._statements.soft_delete(statement_id):
            raise StatementNotFoundError(statement_id)
        return statement

    def compute_spend_minor(self, statement_id: int) -> int:
        """Derived spend total from linked transactions — never stored."""
        debit_total, credit_total = self._statements.sum_statement_spend(statement_id)
        return debit_total - credit_total

    def compute_period_spend_minor(
        self,
        account_id: int,
        period_start: str,
        period_end: str,
    ) -> int:
        """Derived spend for a date range when statement_id is not yet linked."""
        debit_total, credit_total = self._statements.sum_spend_in_period(
            account_id,
            period_start,
            period_end,
        )
        return debit_total - credit_total

    def _create_from_billing(self, account_id: int, billing: BillingCycle) -> Statement:
        validate_statement_dates(billing.period_start, billing.period_end, billing.due_date)
        if self._statements.count_overlapping(
            account_id,
            billing.period_start,
            billing.period_end,
        ):
            raise StatementInvariantError("Statement period overlaps an existing cycle")
        fields = {
            "account_id": account_id,
            "period_start": billing.period_start,
            "period_end": billing.period_end,
            "statement_date": billing.statement_date,
            "due_date": billing.due_date,
        }
        return self._statements.create(fields)
