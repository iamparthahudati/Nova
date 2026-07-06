"""Legacy money API adapter over the transactions ledger."""

from __future__ import annotations

from datetime import date
from typing import Optional

from .finance import seed
from .finance import transactions as txn_store


def _transaction_to_money_row(row: dict) -> dict:
    kind = row["kind"]
    return {
        "id": row["id"],
        "type": "earned" if kind == "income" else "spent",
        "amount": row["amount_minor"] / 100.0,
        "note": row.get("note") or "",
        "created_at": row["created_at"],
    }


def add_money(type_: str, amount: float, note: str = "") -> dict:
    if type_ not in {"earned", "spent"}:
        raise ValueError(f"Invalid money type: {type_}")
    if amount <= 0:
        raise ValueError("Amount must be positive")
    amount_minor = int(round(amount * 100))
    if amount_minor <= 0:
        raise ValueError("Amount must be positive")
    account_id = seed.ensure_default_cash_account()
    kind = "income" if type_ == "earned" else "expense"
    direction = "credit" if type_ == "earned" else "debit"
    row = txn_store.create_transaction(
        {
            "account_id": account_id,
            "direction": direction,
            "kind": kind,
            "amount_minor": amount_minor,
            "note": note,
            "occurred_on": date.today().isoformat(),
            "source": "chat",
        },
    )
    return _transaction_to_money_row(row)


def get_money_by_id(row_id: int) -> Optional[dict]:
    row = txn_store.get_transaction_by_id(row_id)
    if row is None or row["kind"] not in {"income", "expense"}:
        return None
    return _transaction_to_money_row(row)


def get_latest_money(type_: str, amount: float) -> Optional[dict]:
    kind = "income" if type_ == "earned" else "expense"
    amount_minor = int(round(amount * 100))
    row = txn_store.get_latest_income_expense(kind, amount_minor)
    if row is None:
        return None
    return _transaction_to_money_row(row)


def get_recent_money(n: int = 10) -> list[dict]:
    rows = txn_store.list_transactions(limit=n)
    return [_transaction_to_money_row(row) for row in rows if row["kind"] in {"income", "expense"}]


def get_money_since(cutoff_iso: str, limit: int = 30) -> list[dict]:
    rows = txn_store.list_transactions(limit=limit)
    filtered = [row for row in rows if row["created_at"] > cutoff_iso]
    return [
        _transaction_to_money_row(row) for row in filtered if row["kind"] in {"income", "expense"}
    ]


def get_money_totals_between(start_date: str, end_date: str) -> tuple[float, float]:
    income_minor, expense_minor = txn_store.totals_between(start_date, end_date)
    return income_minor / 100.0, expense_minor / 100.0


def get_money_totals_for_date(date_obj) -> tuple[float, float]:
    date_str = date_obj.strftime("%Y-%m-%d")
    return get_money_totals_between(date_str, date_str)
