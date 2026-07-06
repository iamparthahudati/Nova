"""Credit card aggregate service."""

from __future__ import annotations

from datetime import date
from typing import Optional

from ..aggregates import CreditCard
from ..errors import AccountArchivedError, CreditCardNotFoundError
from ..money import classification_for_type
from ..repository_adapters import SqliteAccountRepository, SqliteCreditCardRepository
from ..validation import (
    validate_account_name,
    validate_credit_limit,
    validate_due_day_offset,
    validate_statement_day,
)
from ..value_objects import AccountType


class CreditCardService:
    def __init__(
        self,
        cards: Optional[SqliteCreditCardRepository] = None,
        accounts: Optional[SqliteAccountRepository] = None,
    ) -> None:
        self._cards = cards or SqliteCreditCardRepository()
        self._accounts = accounts or SqliteAccountRepository()

    def create_credit_card(
        self,
        name: str,
        credit_limit_minor: int,
        statement_day: int,
        due_day_offset: int,
        opening_balance_minor: int = 0,
        opening_balance_on: Optional[str] = None,
        network: Optional[str] = None,
        last4: Optional[str] = None,
        autopay: bool = False,
        today: Optional[date] = None,
    ) -> CreditCard:
        today = today or date.today()
        clean_name = validate_account_name(name)
        limit = validate_credit_limit(credit_limit_minor)
        day = validate_statement_day(statement_day)
        offset = validate_due_day_offset(due_day_offset)
        balance_on = opening_balance_on or today.isoformat()
        account_fields = {
            "name": clean_name,
            "type": AccountType.CREDIT_CARD.value,
            "classification": classification_for_type(AccountType.CREDIT_CARD.value),
            "opening_balance_minor": opening_balance_minor,
            "opening_balance_on": balance_on,
        }
        profile_fields = {
            "credit_limit_minor": limit,
            "statement_day": day,
            "due_day_offset": offset,
            "network": network,
            "last4": last4,
            "autopay": autopay,
        }
        return self._cards.create(account_fields, profile_fields)

    def get_credit_card(self, account_id: int) -> CreditCard:
        card = self._cards.get_by_id(account_id)
        if card is None:
            raise CreditCardNotFoundError(account_id)
        return card

    def list_credit_cards(self) -> list[CreditCard]:
        return self._cards.list_live()

    def update_credit_card(
        self,
        account_id: int,
        name: Optional[str] = None,
        credit_limit_minor: Optional[int] = None,
        statement_day: Optional[int] = None,
        due_day_offset: Optional[int] = None,
        network: Optional[str] = None,
        last4: Optional[str] = None,
        autopay: Optional[bool] = None,
    ) -> CreditCard:
        card = self.get_credit_card(account_id)
        if card.account.archived_at is not None:
            raise AccountArchivedError(account_id)
        if name is not None:
            updated_account = self._accounts.update(
                account_id,
                {"name": validate_account_name(name)},
            )
            if updated_account is None:
                raise CreditCardNotFoundError(account_id)
        profile_fields: dict = {}
        if credit_limit_minor is not None:
            profile_fields["credit_limit_minor"] = validate_credit_limit(credit_limit_minor)
        if statement_day is not None:
            profile_fields["statement_day"] = validate_statement_day(statement_day)
        if due_day_offset is not None:
            profile_fields["due_day_offset"] = validate_due_day_offset(due_day_offset)
        if network is not None:
            profile_fields["network"] = network
        if last4 is not None:
            profile_fields["last4"] = last4
        if autopay is not None:
            profile_fields["autopay"] = autopay
        if profile_fields:
            updated_profile = self._cards.update_profile(account_id, profile_fields)
            if updated_profile is None:
                raise CreditCardNotFoundError(account_id)
        return self.get_credit_card(account_id)

    def archive_credit_card(self, account_id: int) -> CreditCard:
        card = self.get_credit_card(account_id)
        if card.account.archived_at is not None:
            raise AccountArchivedError(account_id)
        archived = self._accounts.archive(account_id)
        if archived is None:
            raise CreditCardNotFoundError(account_id)
        return self.get_credit_card(account_id)
