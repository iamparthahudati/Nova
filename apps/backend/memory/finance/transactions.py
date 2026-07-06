"""Transaction rows — persistence only."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection


def create_transaction(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            INSERT INTO transactions (
                account_id, direction, kind, amount_minor,
                category_id, merchant_id, note, occurred_on,
                transfer_group_id, statement_id, source, legacy_money_id,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["account_id"],
                fields["direction"],
                fields["kind"],
                fields["amount_minor"],
                fields.get("category_id"),
                fields.get("merchant_id"),
                fields.get("note"),
                fields["occurred_on"],
                fields.get("transfer_group_id"),
                fields.get("statement_id"),
                fields.get("source", "manual"),
                fields.get("legacy_money_id"),
                now,
                now,
            ),
        )
        txn_id = int(cur.lastrowid)
    row = get_transaction_by_id(txn_id)
    assert row is not None
    return row


def get_transaction_by_id(txn_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM transactions WHERE id = ? AND deleted_at IS NULL",
            (txn_id,),
        ).fetchone()
    return dict(row) if row else None


def get_transaction_by_id_include_deleted(txn_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM transactions WHERE id = ?", (txn_id,)).fetchone()
    return dict(row) if row else None


def list_transactions(
    account_id: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    query = "SELECT * FROM transactions WHERE deleted_at IS NULL"
    params: list[Any] = []
    if account_id is not None:
        query += " AND account_id = ?"
        params.append(account_id)
    query += " ORDER BY occurred_on DESC, id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    with _connection.connect(rows=True) as con:
        rows = con.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def list_by_transfer_group(transfer_group_id: str) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """
            SELECT * FROM transactions
            WHERE transfer_group_id = ? AND deleted_at IS NULL
            ORDER BY id
            """,
            (transfer_group_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def update_transaction(txn_id: int, fields: dict[str, Any]) -> Optional[dict]:
    allowed = {
        "amount_minor",
        "category_id",
        "merchant_id",
        "note",
        "occurred_on",
        "statement_id",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return get_transaction_by_id(txn_id)
    updates["updated_at"] = _connection.now()
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [txn_id]
    with _connection.connect() as con:
        cur = con.execute(
            f"UPDATE transactions SET {set_clause} WHERE id = ? AND deleted_at IS NULL",
            values,
        )
        if cur.rowcount == 0:
            return None
    return get_transaction_by_id(txn_id)


def soft_delete_transaction(txn_id: int) -> bool:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE transactions
            SET deleted_at = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, txn_id),
        )
        return cur.rowcount > 0


def soft_delete_transfer_group(transfer_group_id: str) -> int:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE transactions
            SET deleted_at = ?, updated_at = ?
            WHERE transfer_group_id = ? AND deleted_at IS NULL
            """,
            (now, now, transfer_group_id),
        )
        return cur.rowcount


def sum_by_direction(
    account_id: int,
    as_of: Optional[str] = None,
) -> tuple[int, int]:
    """Return (total_credit_minor, total_debit_minor) for live rows."""
    query = """
        SELECT direction, COALESCE(SUM(amount_minor), 0)
        FROM transactions
        WHERE account_id = ? AND deleted_at IS NULL
    """
    params: list[Any] = [account_id]
    if as_of is not None:
        query += " AND occurred_on <= ?"
        params.append(as_of)
    query += " GROUP BY direction"
    totals = {"credit": 0, "debit": 0}
    with _connection.connect() as con:
        rows = con.execute(query, params).fetchall()
    for direction, total in rows:
        totals[direction] = int(total)
    return totals["credit"], totals["debit"]


def totals_between(start_date: str, end_date: str) -> tuple[int, int]:
    """Return (income_minor, expense_minor) for occurred_on in [start, end]."""
    with _connection.connect() as con:
        rows = con.execute(
            """
            SELECT kind, COALESCE(SUM(amount_minor), 0)
            FROM transactions
            WHERE deleted_at IS NULL
              AND occurred_on BETWEEN ? AND ?
              AND kind IN ('income', 'expense')
            GROUP BY kind
            """,
            (start_date, end_date),
        ).fetchall()
    totals = {"income": 0, "expense": 0}
    for kind, total in rows:
        totals[kind] = int(total)
    return totals["income"], totals["expense"]


def get_latest_income_expense(kind: str, amount_minor: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """
            SELECT * FROM transactions
            WHERE kind = ? AND amount_minor = ? AND deleted_at IS NULL
            ORDER BY created_at DESC LIMIT 1
            """,
            (kind, amount_minor),
        ).fetchone()
    return dict(row) if row else None
