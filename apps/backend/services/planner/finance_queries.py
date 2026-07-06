"""Finance read queries — delegates to domain services and projections."""

from __future__ import annotations

from datetime import date
from typing import Optional

from domains.finance.cashback import CashbackRuleService
from domains.finance.cashback.projections import month_bounds
from domains.finance.rewards import RewardProgramService, RewardProjectionService
from domains.finance.services.account_service import AccountService
from domains.finance.services.category_service import CategoryService
from domains.finance.services.credit_card_service import CreditCardService
from domains.finance.services.merchant_service import MerchantService
from domains.finance.services.projection_service import ProjectionService
from domains.finance.services.statement_service import StatementService
from domains.finance.services.transaction_service import TransactionService
from domains.finance.value_objects import Classification

from .finance_serializers import (
    serialize_account,
    serialize_cashback_rule,
    serialize_credit_card,
    serialize_reward_balance,
    serialize_reward_event,
    serialize_reward_program,
    serialize_statement,
    serialize_transaction,
)

_accounts = AccountService()
_categories = CategoryService()
_merchants = MerchantService()
_cards = CreditCardService()
_statements = StatementService()
_transactions = TransactionService()
_projections = ProjectionService()
_reward_programs = RewardProgramService()
_reward_projections = RewardProjectionService()
_cashback_rules = CashbackRuleService()


def _account_names() -> dict[int, str]:
    return {account.id: account.name for account in _accounts.list_accounts()}


def _category_names() -> dict[int, str]:
    return {category.id: category.name for category in _categories.list_categories()}


def _merchant_names() -> dict[int, str]:
    return {merchant.id: merchant.name for merchant in _merchants.list_merchants()}


def _enrich_transaction(txn):
    accounts = _account_names()
    categories = _category_names()
    merchants = _merchant_names()
    return serialize_transaction(
        txn,
        account_name=accounts.get(txn.account_id),
        category_name=categories.get(txn.category_id) if txn.category_id else None,
        merchant_name=merchants.get(txn.merchant_id) if txn.merchant_id else None,
    )


def _build_upcoming_due(cards, today: date, created_statements: list[dict]) -> list[dict]:
    upcoming_due = []
    for card in cards:
        current, _previous, created = _statements.ensure_current_and_previous(card.id, today=today)
        for statement in created:
            created_statements.append(serialize_entity(statement))
        summary = _projections.compute_statement_summary(current.id, today)
        if summary.status.value in {"open", "due", "overdue", "partial"}:
            upcoming_due.append(
                {
                    "account_id": card.id,
                    "card_name": card.name,
                    "statement_id": current.id,
                    "due_date": current.due_date,
                    "remaining_due_minor": summary.remaining_due_minor,
                    "remaining_due": (
                        summary.remaining_due_minor / 100.0
                        if summary.remaining_due_minor is not None
                        else None
                    ),
                    "status": summary.status.value,
                },
            )
    upcoming_due.sort(key=lambda row: row["due_date"])
    return upcoming_due


def get_finance_dashboard(today: Optional[date] = None) -> tuple[dict, list[dict]]:
    today = today or date.today()
    month_start = today.replace(day=1).isoformat()
    month_end = today.isoformat()
    created_statements: list[dict] = []

    balances = _projections.list_account_balances()
    total_assets_minor = 0
    total_liabilities_minor = 0
    for row in balances:
        account = _accounts.get_account(row["account_id"])
        balance = row["balance_minor"]
        if account.classification == Classification.ASSET.value:
            total_assets_minor += balance
        else:
            total_liabilities_minor += abs(balance)

    cards = _projections.list_card_utilization()
    total_limit = sum(card["credit_limit_minor"] for card in cards)
    total_outstanding = sum(card["outstanding_minor"] for card in cards)
    utilization_ratio = total_outstanding / total_limit if total_limit else 0.0

    _, spent_month = _projections.compute_period_totals(month_start, month_end)
    reward_rows = _reward_projections.list_all_balances()
    total_reward_balance = sum(row["balance"] for row in reward_rows)

    cashback_month_minor = 0
    for program in _reward_programs.list_programs():
        if program.unit != "cashback_minor":
            continue
        month_start_bound, month_end_bound = month_bounds(today.isoformat())
        cashback_month_minor += _reward_projections.compute_yearly_earned(
            program.id,
            month_start_bound,
            month_end_bound,
        )

    upcoming_due = _build_upcoming_due(_cards.list_credit_cards(), today, created_statements)

    recent = [_enrich_transaction(txn) for txn in _transactions.list_transactions(limit=10)]

    return {
        "total_balance_minor": total_assets_minor - total_liabilities_minor,
        "total_balance": (total_assets_minor - total_liabilities_minor) / 100.0,
        "total_assets_minor": total_assets_minor,
        "total_assets": total_assets_minor / 100.0,
        "total_liabilities_minor": total_liabilities_minor,
        "total_liabilities": total_liabilities_minor / 100.0,
        "credit_utilization_ratio": utilization_ratio,
        "credit_utilization_percent": round(utilization_ratio * 100, 1),
        "spent_month": spent_month,
        "reward_balance": total_reward_balance,
        "cashback_earned_month_minor": cashback_month_minor,
        "cashback_earned_month": cashback_month_minor / 100.0,
        "upcoming_due_dates": upcoming_due,
        "recent_transactions": recent,
    }, created_statements


def list_accounts(include_archived: bool = False) -> list[dict]:
    accounts = _accounts.list_accounts()
    rows = []
    for account in accounts:
        if not include_archived and account.archived_at is not None:
            continue
        balance = _projections.compute_account_balance(account.id)
        rows.append(serialize_account(account, balance_minor=balance))
    return rows


def get_account(account_id: int) -> dict:
    account = _accounts.get_account(account_id)
    balance = _projections.compute_account_balance(account.id)
    return serialize_account(account, balance_minor=balance)


def _materialize_account_statements(account_id: int, today: Optional[date] = None) -> list[dict]:
    today = today or date.today()
    _current, _previous, created = _statements.ensure_current_and_previous(account_id, today=today)
    return [serialize_entity(statement) for statement in created]


def _statement_detail(statement_id: int, today: Optional[date] = None) -> dict:
    today = today or date.today()
    statement = _statements.get_statement(statement_id)
    summary = _projections.compute_statement_summary(statement_id, today)
    row = serialize_statement(statement, summary=summary)
    row["transactions"] = [
        _enrich_transaction(txn)
        for txn in _transactions.list_transactions(account_id=statement.account_id, limit=500)
        if txn.statement_id == statement_id
        or (
            txn.statement_id is None
            and statement.period_start <= txn.occurred_on <= statement.period_end
        )
    ]
    return row


def list_credit_cards() -> tuple[list[dict], list[dict]]:
    rows = []
    created_statements: list[dict] = []
    today = date.today()
    for card in _cards.list_credit_cards():
        _current, _previous, created = _statements.ensure_current_and_previous(card.id, today=today)
        for statement in created:
            created_statements.append(serialize_entity(statement))
        balance = _projections.compute_account_balance(card.id)
        utilization = _projections.compute_utilization(card.id)
        available = _projections.compute_available_limit(card.id)
        rows.append(
            serialize_credit_card(
                card,
                balance_minor=balance,
                utilization=utilization,
                available_limit_minor=available.minor,
            ),
        )
    return rows, created_statements


def get_credit_card(account_id: int) -> tuple[dict, list[dict]]:
    today = date.today()
    card = _cards.get_credit_card(account_id)
    balance = _projections.compute_account_balance(card.id)
    utilization = _projections.compute_utilization(card.id)
    available = _projections.compute_available_limit(card.id)
    current, previous, created = _statements.ensure_current_and_previous(card.id, today=today)
    created_rows = [serialize_entity(statement) for statement in created]
    row = serialize_credit_card(
        card,
        balance_minor=balance,
        utilization=utilization,
        available_limit_minor=available.minor,
    )
    row["current_statement"] = _statement_detail(current.id, today) if current else None
    row["previous_statement"] = _statement_detail(previous.id, today) if previous else None
    return row, created_rows


def list_statements(account_id: int, limit: int = 24) -> tuple[list[dict], list[dict]]:
    created_rows = _materialize_account_statements(account_id)
    summaries = _projections.list_statement_summaries(account_id, limit=limit)
    statement_map = {
        statement.id: statement for statement in _statements.list_statements(account_id, limit)
    }
    rows = []
    for summary in summaries:
        statement = statement_map.get(summary.statement_id)
        if statement is None:
            continue
        rows.append(serialize_statement(statement, summary=summary))
    return rows, created_rows


def get_statement(statement_id: int, today: Optional[date] = None) -> tuple[dict, list[dict]]:
    today = today or date.today()
    statement = _statements.get_statement(statement_id)
    created_rows = _materialize_account_statements(statement.account_id, today)
    return _statement_detail(statement_id, today), created_rows


def list_transactions(
    account_id: Optional[int] = None,
    category_id: Optional[int] = None,
    merchant_id: Optional[int] = None,
    direction: Optional[str] = None,
    kind: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    txns = _transactions.list_transactions(account_id=account_id, limit=500, offset=0)
    filtered = []
    search_lower = search.lower() if search else None
    for txn in txns:
        if category_id is not None and txn.category_id != category_id:
            continue
        if merchant_id is not None and txn.merchant_id != merchant_id:
            continue
        if direction is not None and txn.direction != direction:
            continue
        if kind is not None and txn.kind != kind:
            continue
        if start_date is not None and txn.occurred_on < start_date:
            continue
        if end_date is not None and txn.occurred_on > end_date:
            continue
        if search_lower and search_lower not in (txn.note or "").lower():
            continue
        filtered.append(txn)
    total = len(filtered)
    page = filtered[offset : offset + limit]
    return [_enrich_transaction(txn) for txn in page], total


def list_categories() -> list[dict]:
    return [serialize_entity(c) for c in _categories.list_categories()]


def list_merchants() -> list[dict]:
    return [serialize_entity(m) for m in _merchants.list_merchants()]


def serialize_entity(entity) -> dict:
    from .finance_serializers import serialize_entity as _serialize

    return _serialize(entity)


def list_reward_programs(account_id: Optional[int] = None) -> list[dict]:
    programs = _reward_programs.list_programs(account_id)
    rows = []
    for program in programs:
        balance = _reward_projections.compute_program_balance(program.id)
        row = serialize_reward_program(program)
        row["balance"] = serialize_reward_balance(balance)
        rows.append(row)
    return rows


def get_reward_program(program_id: int) -> dict:
    program = _reward_programs.get_program(program_id)
    balance = _reward_projections.compute_program_balance(program.id)
    row = serialize_reward_program(program)
    row["balance"] = serialize_reward_balance(balance)
    return row


def get_reward_ledger(program_id: int, limit: int = 50, offset: int = 0) -> dict:
    ledger = _reward_projections.build_ledger(program_id, limit, offset)
    year_start = date.today().replace(month=1, day=1).isoformat()
    year_end = date.today().isoformat()
    yearly_earned = _reward_projections.compute_yearly_earned(program_id, year_start, year_end)
    return {
        "program": serialize_reward_program(ledger.program),
        "balance": serialize_reward_balance(ledger.balance),
        "events": [serialize_reward_event(event) for event in ledger.events],
        "yearly_earned": yearly_earned,
    }


def list_cashback_rules(program_id: Optional[int] = None) -> list[dict]:
    if program_id is not None:
        return [
            serialize_cashback_rule(rule)
            for rule in _cashback_rules.list_rules_for_program(program_id)
        ]
    rows = []
    for program in _reward_programs.list_programs():
        if program.unit != "cashback_minor":
            continue
        for rule in _cashback_rules.list_rules_for_program(program.id):
            row = serialize_cashback_rule(rule)
            row["program_name"] = program.name
            row["account_id"] = program.account_id
            rows.append(row)
    return rows


def get_cashback_summary(today: Optional[date] = None) -> dict:
    today = today or date.today()
    month_start, month_end = month_bounds(today.isoformat())
    rules = list_cashback_rules()
    monthly_earned_minor = 0
    for program in _reward_programs.list_programs():
        if program.unit != "cashback_minor":
            continue
        monthly_earned_minor += _reward_projections.compute_yearly_earned(
            program.id,
            month_start,
            month_end,
        )
    return {
        "monthly_earned_minor": monthly_earned_minor,
        "monthly_earned": monthly_earned_minor / 100.0,
        "rules": rules,
    }
