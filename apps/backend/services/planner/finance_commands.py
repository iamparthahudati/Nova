"""Finance REST write commands — delegate to domain services."""

from __future__ import annotations

from datetime import date
from typing import Optional

from domains.finance.cashback import CashbackEngine, CashbackPolicy, CashbackRuleService
from domains.finance.errors import (
    AccountArchivedError,
    AccountNotFoundError,
    CategoryNotFoundError,
    CreditCardNotFoundError,
    FinanceValidationError,
    MerchantNotFoundError,
    PaymentConfirmationRequiredError,
    StatementNotFoundError,
    TransactionNotFoundError,
    TransferInvariantError,
)
from domains.finance.money import MoneyAmount
from domains.finance.payments.service import PaymentService
from domains.finance.rewards.services.program_service import RewardProgramService
from domains.finance.services.account_service import AccountService
from domains.finance.services.category_service import CategoryService
from domains.finance.services.credit_card_service import CreditCardService
from domains.finance.services.merchant_service import MerchantService
from domains.finance.services.statement_service import StatementService
from domains.finance.services.transaction_service import TransactionService
from domains.finance.services.transfer_service import TransferService

from .finance_serializers import (
    serialize_account,
    serialize_credit_card,
    serialize_entity,
    serialize_transaction,
    serialize_transfer_group,
)

_accounts = AccountService()
_categories = CategoryService()
_merchants = MerchantService()
_cards = CreditCardService()
_statements = StatementService()
_transactions = TransactionService()
_transfers = TransferService()
_payments = PaymentService()
_reward_programs = RewardProgramService()
_cashback_rules = CashbackRuleService()
_cashback_engine = CashbackEngine()


def create_account(
    name: str,
    account_type: str,
    opening_balance: float = 0.0,
    opening_balance_on: Optional[str] = None,
) -> tuple[dict, str]:
    opening_minor = int(round(opening_balance * 100))
    account = _accounts.create_account(
        name,
        account_type,
        opening_balance_minor=opening_minor,
        opening_balance_on=opening_balance_on,
    )
    return (
        serialize_account(account, balance_minor=opening_minor),
        f"Account {account.name} created.",
    )


def update_account(
    account_id: int,
    name: Optional[str] = None,
    opening_balance: Optional[float] = None,
    opening_balance_on: Optional[str] = None,
) -> tuple[dict, str]:
    opening_minor = int(round(opening_balance * 100)) if opening_balance is not None else None
    account = _accounts.update_account(
        account_id,
        name=name,
        opening_balance_minor=opening_minor,
        opening_balance_on=opening_balance_on,
    )
    return serialize_account(account), f"Account {account.name} updated."


def archive_account(account_id: int) -> tuple[dict, str]:
    account = _accounts.archive_account(account_id)
    return serialize_account(account), f"Account {account.name} archived."


def create_credit_card(
    name: str,
    credit_limit: float,
    statement_day: int,
    due_day_offset: int,
    opening_balance: float = 0.0,
    opening_balance_on: Optional[str] = None,
    network: Optional[str] = None,
    last4: Optional[str] = None,
    autopay: bool = False,
) -> tuple[dict, str]:
    card = _cards.create_credit_card(
        name,
        int(round(credit_limit * 100)),
        statement_day,
        due_day_offset,
        opening_balance_minor=int(round(opening_balance * 100)),
        opening_balance_on=opening_balance_on,
        network=network,
        last4=last4,
        autopay=autopay,
    )
    return serialize_credit_card(card), f"Credit card {card.name} created."


def update_credit_card(
    account_id: int,
    name: Optional[str] = None,
    credit_limit: Optional[float] = None,
    statement_day: Optional[int] = None,
    due_day_offset: Optional[int] = None,
    network: Optional[str] = None,
    last4: Optional[str] = None,
    autopay: Optional[bool] = None,
) -> tuple[dict, str]:
    card = _cards.update_credit_card(
        account_id,
        name=name,
        credit_limit_minor=int(round(credit_limit * 100)) if credit_limit is not None else None,
        statement_day=statement_day,
        due_day_offset=due_day_offset,
        network=network,
        last4=last4,
        autopay=autopay,
    )
    return serialize_credit_card(card), f"Credit card {card.name} updated."


def create_transaction(
    account_id: int,
    kind: str,
    amount: float,
    occurred_on: str,
    category_id: Optional[int] = None,
    merchant_id: Optional[int] = None,
    note: Optional[str] = None,
    direction: Optional[str] = None,
) -> tuple[dict, str, list[dict]]:
    txn = _transactions.create_transaction(
        account_id,
        kind,
        MoneyAmount.from_rupees(amount).minor,
        occurred_on,
        category_id=category_id,
        merchant_id=merchant_id,
        note=note,
        direction=direction,
        source="manual",
    )
    extras = _earn_cashback_for_transaction(txn)
    return serialize_transaction(txn), "Transaction logged.", extras


def update_transaction(
    transaction_id: int,
    amount: Optional[float] = None,
    category_id: Optional[int] = None,
    merchant_id: Optional[int] = None,
    note: Optional[str] = None,
    occurred_on: Optional[str] = None,
) -> tuple[dict, str]:
    txn = _transactions.update_transaction(
        transaction_id,
        amount_minor=MoneyAmount.from_rupees(amount).minor if amount is not None else None,
        category_id=category_id,
        merchant_id=merchant_id,
        note=note,
        occurred_on=occurred_on,
    )
    return serialize_transaction(txn), "Transaction updated."


def delete_transaction(transaction_id: int) -> tuple[dict, str]:
    txn = _transactions.delete_transaction(transaction_id)
    return serialize_transaction(txn), "Transaction deleted."


def create_transfer(
    from_account_id: int,
    to_account_id: int,
    amount: float,
    occurred_on: str,
    note: Optional[str] = None,
) -> tuple[dict, str]:
    legs, group_id = _transfers.create_transfer(
        from_account_id,
        to_account_id,
        MoneyAmount.from_rupees(amount).minor,
        occurred_on,
        note=note,
    )
    return serialize_transfer_group(legs, group_id), "Transfer recorded."


def delete_transfer(transfer_group_id: str) -> tuple[list[dict], str]:
    legs = _transfers.delete_transfer(transfer_group_id)
    return [serialize_transaction(leg) for leg in legs], "Transfer deleted."


def create_card_payment(
    from_account_id: int,
    card_account_id: int,
    amount: float,
    occurred_on: str,
    statement_id: Optional[int] = None,
    note: Optional[str] = None,
    confirm_overpayment: bool = False,
) -> tuple[dict, str]:
    legs, group_id = _payments.create_card_payment(
        from_account_id,
        card_account_id,
        MoneyAmount.from_rupees(amount).minor,
        occurred_on,
        statement_id=statement_id,
        note=note,
        confirm_overpayment=confirm_overpayment,
    )
    return serialize_transfer_group(legs, group_id), "Card payment recorded."


def pay_statement(
    statement_id: int,
    from_account_id: int,
    payment_mode: str = "partial",
    amount: Optional[float] = None,
    note: Optional[str] = None,
    confirm_overpayment: bool = False,
) -> tuple[dict, str, int]:
    amount_minor = MoneyAmount.from_rupees(amount).minor if amount is not None else None
    legs, group_id = _payments.pay_statement(
        statement_id,
        from_account_id,
        payment_mode=payment_mode,
        amount_minor=amount_minor,
        note=note,
        confirm_overpayment=confirm_overpayment,
    )
    entity = serialize_transfer_group(legs, group_id)
    entity["statement_id"] = statement_id
    return entity, "Statement payment recorded.", statement_id


def delete_card_payment(transfer_group_id: str) -> tuple[list[dict], str]:
    legs = _payments.delete_card_payment(transfer_group_id)
    return [serialize_transaction(leg) for leg in legs], "Card payment deleted."


def update_statement(
    statement_id: int,
    total_due: Optional[float] = None,
    min_due: Optional[float] = None,
) -> tuple[dict, str]:
    statement = _statements.update_statement(
        statement_id,
        total_due_minor=int(round(total_due * 100)) if total_due is not None else None,
        min_due_minor=int(round(min_due * 100)) if min_due is not None else None,
    )
    return serialize_entity(statement), "Statement updated."


def create_category(name: str) -> tuple[dict, str]:
    category = _categories.create_category(name)
    return serialize_entity(category), f"Category {category.name} created."


def update_category(category_id: int, name: str) -> tuple[dict, str]:
    category = _categories.update_category(category_id, name)
    return serialize_entity(category), f"Category {category.name} updated."


def delete_category(category_id: int) -> tuple[dict, str]:
    category = _categories.delete_category(category_id)
    return serialize_entity(category), f"Category {category.name} deleted."


def create_merchant(name: str) -> tuple[dict, str]:
    merchant = _merchants.create_merchant(name)
    return serialize_entity(merchant), f"Merchant {merchant.name} created."


def update_merchant(merchant_id: int, name: str) -> tuple[dict, str]:
    merchant = _merchants.update_merchant(merchant_id, name)
    return serialize_entity(merchant), f"Merchant {merchant.name} updated."


def delete_merchant(merchant_id: int) -> tuple[dict, str]:
    merchant = _merchants.delete_merchant(merchant_id)
    return serialize_entity(merchant), f"Merchant {merchant.name} deleted."


def _earn_cashback_for_transaction(txn) -> list[dict]:
    try:
        card = _cards.get_credit_card(txn.account_id)
    except CreditCardNotFoundError:
        return []
    extras: list[dict] = []
    for program in _reward_programs.list_programs(account_id=card.id):
        if program.unit != "cashback_minor":
            continue
        rules = _cashback_rules.list_rules_for_program(program.id)
        rule = CashbackPolicy.select_rule(rules, card, program)
        if rule is None:
            continue
        result = _cashback_engine.earn_for_transaction(txn, card, program, rule, today=date.today())
        if result.reward_event is not None:
            extras.append(serialize_entity(result.reward_event))
    return extras


__all__ = [
    "AccountNotFoundError",
    "AccountArchivedError",
    "CreditCardNotFoundError",
    "CategoryNotFoundError",
    "MerchantNotFoundError",
    "StatementNotFoundError",
    "TransactionNotFoundError",
    "FinanceValidationError",
    "PaymentConfirmationRequiredError",
    "TransferInvariantError",
    "create_account",
    "update_account",
    "archive_account",
    "create_credit_card",
    "update_credit_card",
    "create_transaction",
    "update_transaction",
    "delete_transaction",
    "create_transfer",
    "delete_transfer",
    "create_card_payment",
    "pay_statement",
    "delete_card_payment",
    "update_statement",
    "create_category",
    "update_category",
    "delete_category",
    "create_merchant",
    "update_merchant",
    "delete_merchant",
]
