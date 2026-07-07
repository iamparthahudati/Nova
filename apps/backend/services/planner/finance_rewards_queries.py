"""Finance rewards read queries — overview, programs, ledger, detail."""

from __future__ import annotations

from datetime import date
from typing import Optional

from domains.finance.cashback.projections import month_bounds
from domains.finance.errors import TransactionNotFoundError
from domains.finance.rewards import RewardProgramService, RewardProjectionService
from domains.finance.rewards.ledger import derive_program_status
from domains.finance.services.account_service import AccountService
from domains.finance.services.transaction_service import TransactionService

from .finance_queries import _enrich_transaction
from .finance_serializers import (
    serialize_reward_balance,
    serialize_reward_event,
    serialize_reward_program,
)

_accounts = AccountService()
_transactions = TransactionService()
_reward_programs = RewardProgramService()
_reward_projections = RewardProjectionService()


def _enrich_reward_program(program, balance) -> dict:
    account = _accounts.get_account(program.account_id)
    row = serialize_reward_program(program)
    row["balance"] = serialize_reward_balance(balance)
    row["account_name"] = account.name
    row["bank_name"] = account.name
    row["status"] = derive_program_status(
        balance.balance,
        balance.total_earned,
        program.expiry_note,
    )
    return row


def get_rewards_overview() -> dict:
    today = date.today()
    overview = _reward_projections.build_overview(today)
    overview["earned_month_cashback"] = overview["earned_month_cashback_minor"] / 100.0
    overview["earned_year_cashback"] = overview["earned_year_cashback_minor"] / 100.0
    overview["earned_lifetime_cashback"] = overview["earned_lifetime_cashback_minor"] / 100.0
    overview["total_balance_cashback"] = overview["total_balance_cashback_minor"] / 100.0
    return overview


def list_reward_programs(account_id: Optional[int] = None) -> list[dict]:
    programs = _reward_programs.list_programs(account_id)
    rows = []
    for program in programs:
        balance = _reward_projections.compute_program_balance(program.id)
        rows.append(_enrich_reward_program(program, balance))
    return rows


def get_reward_program(program_id: int) -> dict:
    program = _reward_programs.get_program(program_id)
    balance = _reward_projections.compute_program_balance(program.id)
    return _enrich_reward_program(program, balance)


def get_reward_program_detail(program_id: int) -> dict:
    today = date.today()
    detail = _reward_projections.build_program_detail(program_id, today)
    program = detail["program"]
    balance = detail["balance"]
    account = _accounts.get_account(program.account_id)

    related_transactions = []
    for txn_id in detail["related_transaction_ids"]:
        try:
            txn = _transactions.get_transaction(txn_id)
            related_transactions.append(_enrich_transaction(txn))
        except TransactionNotFoundError:
            continue

    return {
        "program": _enrich_reward_program(program, balance),
        "balance": serialize_reward_balance(balance),
        "status": detail["status"],
        "account_name": account.name,
        "bank_name": account.name,
        "earned_month": detail["earned_month"],
        "earned_year": detail["earned_year"],
        "earned_lifetime": detail["earned_lifetime"],
        "monthly_history": detail["monthly_history"],
        "recent_events": [serialize_reward_event(event) for event in detail["recent_events"]],
        "related_transactions": related_transactions,
    }


def get_reward_ledger(program_id: int, limit: int = 50, offset: int = 0) -> dict:
    ledger = _reward_projections.build_ledger(program_id, limit, offset)
    today = date.today()
    year_start = today.replace(month=1, day=1).isoformat()
    year_end = today.isoformat()
    month_start, month_end = month_bounds(today.isoformat())
    yearly_earned = _reward_projections.compute_yearly_earned(program_id, year_start, year_end)
    monthly_earned = _reward_projections.compute_yearly_earned(program_id, month_start, month_end)
    balance = ledger.balance
    return {
        "program": _enrich_reward_program(ledger.program, balance),
        "balance": serialize_reward_balance(balance),
        "events": [serialize_reward_event(event) for event in ledger.events],
        "yearly_earned": yearly_earned,
        "monthly_earned": monthly_earned,
        "lifetime_earned": balance.total_earned,
    }
