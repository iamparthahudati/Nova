"""Finance cashback read queries — overview, rules, activity, detail."""

from __future__ import annotations

import re
from datetime import date
from typing import Optional

from domains.finance.cashback import CashbackRuleService
from domains.finance.cashback.errors import CashbackRuleNotFoundError
from domains.finance.cashback.projections import month_bounds
from domains.finance.errors import CreditCardNotFoundError, TransactionNotFoundError
from domains.finance.rewards import RewardProgramService, RewardProjectionService
from domains.finance.rewards.aggregates import RewardEvent
from domains.finance.rewards.ledger import fold_monthly_activity
from domains.finance.services.account_service import AccountService
from domains.finance.services.category_service import CategoryService
from domains.finance.services.credit_card_service import CreditCardService
from domains.finance.services.merchant_service import MerchantService
from domains.finance.services.transaction_service import TransactionService

from .finance_queries import _enrich_transaction
from .finance_serializers import serialize_cashback_rule, serialize_reward_event

_accounts = AccountService()
_cards = CreditCardService()
_categories = CategoryService()
_merchants = MerchantService()
_transactions = TransactionService()
_reward_programs = RewardProgramService()
_reward_projections = RewardProjectionService()
_cashback_rules = CashbackRuleService()

_RULE_NOTE_PATTERN = re.compile(r"^cashback rule (\d+)")


def _rule_note_marker(rule_id: int) -> str:
    return f"cashback rule {rule_id}"


def _parse_rule_id_from_note(note: Optional[str]) -> Optional[int]:
    if not note:
        return None
    match = _RULE_NOTE_PATTERN.match(note.strip())
    return int(match.group(1)) if match else None


def _category_names() -> dict[int, str]:
    return {category.id: category.name for category in _categories.list_categories()}


def _merchant_names() -> dict[int, str]:
    return {merchant.id: merchant.name for merchant in _merchants.list_merchants()}


def _cashback_programs():
    return [
        program for program in _reward_programs.list_programs() if program.unit == "cashback_minor"
    ]


def _program_earned_month(program_id: int, month_start: str, month_end: str) -> int:
    return _reward_projections.compute_yearly_earned(program_id, month_start, month_end)


def _remaining_cap_minor(
    monthly_cap_minor: Optional[int], earned_month_minor: int
) -> Optional[int]:
    if monthly_cap_minor is None:
        return None
    return max(monthly_cap_minor - earned_month_minor, 0)


def _derive_rule_status(
    monthly_cap_minor: Optional[int], remaining_cap_minor: Optional[int]
) -> str:
    if monthly_cap_minor is None:
        return "active"
    if remaining_cap_minor is not None and remaining_cap_minor <= 0:
        return "capped"
    return "active"


def _enrich_rule_row(rule, program_name: str, account_id: int, today: date) -> dict:
    month_start, month_end = month_bounds(today.isoformat())
    earned_month_minor = _program_earned_month(rule.program_id, month_start, month_end)
    remaining = _remaining_cap_minor(rule.monthly_cap_minor, earned_month_minor)
    account = _accounts.get_account(account_id)
    try:
        card_name = _cards.get_credit_card(account_id).name
    except CreditCardNotFoundError:
        card_name = account.name

    categories = _category_names()
    merchants = _merchant_names()
    row = serialize_cashback_rule(rule)
    row["program_name"] = program_name
    row["account_id"] = account_id
    row["account_name"] = account.name
    row["card_name"] = card_name
    row["earned_month_minor"] = earned_month_minor
    row["earned_month"] = earned_month_minor / 100.0
    row["remaining_cap_minor"] = remaining
    if remaining is not None:
        row["remaining_cap"] = remaining / 100.0
    row["status"] = _derive_rule_status(rule.monthly_cap_minor, remaining)
    row["excluded_category_names"] = [
        categories.get(item, str(item)) for item in rule.excluded_category_ids
    ]
    row["excluded_merchant_names"] = [
        merchants.get(item, str(item)) for item in rule.excluded_merchant_ids
    ]
    return row


def list_cashback_rules(
    program_id: Optional[int] = None, today: Optional[date] = None
) -> list[dict]:
    today = today or date.today()
    if program_id is not None:
        program = _reward_programs.get_program(program_id)
        return [
            _enrich_rule_row(rule, program.name, program.account_id, today)
            for rule in _cashback_rules.list_rules_for_program(program_id)
        ]

    rows = []
    for program in _cashback_programs():
        for rule in _cashback_rules.list_rules_for_program(program.id):
            rows.append(_enrich_rule_row(rule, program.name, program.account_id, today))
    return rows


def _compute_overview_totals(today: date) -> dict:
    month_start, month_end = month_bounds(today.isoformat())
    year_start = today.replace(month=1, day=1).isoformat()
    year_end = today.isoformat()

    total_balance_minor = 0
    earned_month_minor = 0
    earned_year_minor = 0
    earned_lifetime_minor = 0
    for program in _cashback_programs():
        balance = _reward_projections.compute_program_balance(program.id)
        total_balance_minor += balance.balance
        earned_month_minor += _program_earned_month(program.id, month_start, month_end)
        earned_year_minor += _program_earned_month(program.id, year_start, year_end)
        earned_lifetime_minor += balance.total_earned

    return {
        "total_balance_minor": total_balance_minor,
        "total_balance": total_balance_minor / 100.0,
        "monthly_earned_minor": earned_month_minor,
        "monthly_earned": earned_month_minor / 100.0,
        "earned_year_minor": earned_year_minor,
        "earned_year": earned_year_minor / 100.0,
        "earned_lifetime_minor": earned_lifetime_minor,
        "earned_lifetime": earned_lifetime_minor / 100.0,
    }


def _aggregate_remaining_cap(rules: list[dict]) -> tuple[Optional[int], Optional[float]]:
    capped_rules = [rule for rule in rules if rule.get("remaining_cap_minor") is not None]
    if not capped_rules:
        return None, None
    remaining = sum(rule["remaining_cap_minor"] for rule in capped_rules)
    return remaining, remaining / 100.0


def get_cashback_summary(today: Optional[date] = None) -> dict:
    today = today or date.today()
    rules = list_cashback_rules(today=today)
    overview = _compute_overview_totals(today)
    remaining_minor, remaining = _aggregate_remaining_cap(rules)
    overview["remaining_monthly_cap_minor"] = remaining_minor
    overview["remaining_monthly_cap"] = remaining
    overview["active_rules_count"] = len(rules)
    overview["rules"] = rules
    return overview


def _collect_cashback_events(limit: int, offset: int) -> list[RewardEvent]:
    events: list[RewardEvent] = []
    for program in _cashback_programs():
        events.extend(_reward_projections.build_ledger(program.id, limit=500, offset=0).events)
    events.sort(key=lambda event: (event.occurred_on, event.id), reverse=True)
    return events[offset : offset + limit]


def get_cashback_activity(limit: int = 50, offset: int = 0) -> dict:
    rule_names = {rule.id: rule.name for rule in _iter_all_rules()}
    rows = []
    for event in _collect_cashback_events(limit, offset):
        if event.kind != "earned" or event.direction != "credit":
            continue
        rule_id = _parse_rule_id_from_note(event.note)
        program = _reward_programs.get_program(event.program_id)
        txn_note = None
        if event.transaction_id is not None:
            try:
                txn_note = _transactions.get_transaction(event.transaction_id).note
            except TransactionNotFoundError:
                txn_note = None
        rows.append(
            {
                "id": event.id,
                "program_id": event.program_id,
                "program_name": program.name,
                "rule_id": rule_id,
                "rule_name": rule_names.get(rule_id) if rule_id is not None else None,
                "transaction_id": event.transaction_id,
                "transaction_note": txn_note,
                "amount_minor": event.amount,
                "amount": event.amount / 100.0,
                "occurred_on": event.occurred_on,
                "note": event.note,
            },
        )
    return {"events": rows}


def _iter_all_rules():
    for program in _cashback_programs():
        yield from _cashback_rules.list_rules_for_program(program.id)


def _filter_rule_events(program_id: int, rule_id: int):
    marker = _rule_note_marker(rule_id)
    events = _reward_projections.build_ledger(program_id, limit=10_000, offset=0).events
    return [event for event in events if event.note and marker in event.note]


def get_cashback_rule_detail(rule_id: int, today: Optional[date] = None) -> dict:
    today = today or date.today()
    rule = _cashback_rules.get_rule(rule_id)
    program = _reward_programs.get_program(rule.program_id)
    if program.unit != "cashback_minor":
        raise CashbackRuleNotFoundError(rule_id)

    enriched = _enrich_rule_row(rule, program.name, program.account_id, today)
    month_start, month_end = month_bounds(today.isoformat())
    year_start = today.replace(month=1, day=1).isoformat()
    year_end = today.isoformat()
    balance = _reward_projections.compute_program_balance(program.id)
    rule_events = _filter_rule_events(program.id, rule.id)
    monthly_history = fold_monthly_activity(rule_events, 6, today)

    related_transactions = []
    for event in rule_events[:10]:
        if event.transaction_id is None:
            continue
        try:
            related_transactions.append(
                _enrich_transaction(_transactions.get_transaction(event.transaction_id))
            )
        except TransactionNotFoundError:
            continue

    return {
        "rule": enriched,
        "program_name": program.name,
        "account_name": enriched["account_name"],
        "card_name": enriched["card_name"],
        "earned_month": _program_earned_month(program.id, month_start, month_end),
        "earned_year": _program_earned_month(program.id, year_start, year_end),
        "earned_lifetime": balance.total_earned,
        "monthly_history": monthly_history,
        "recent_events": [serialize_reward_event(event) for event in rule_events[:50]],
        "related_transactions": related_transactions,
        "remaining_cap_minor": enriched.get("remaining_cap_minor"),
        "remaining_cap": enriched.get("remaining_cap"),
    }
