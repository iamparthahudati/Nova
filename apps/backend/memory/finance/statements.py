"""Statement rows — persistence only."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection


def create_statement(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            INSERT INTO statements (
                account_id, period_start, period_end,
                statement_date, due_date,
                total_due_minor, min_due_minor,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["account_id"],
                fields["period_start"],
                fields["period_end"],
                fields["statement_date"],
                fields["due_date"],
                fields.get("total_due_minor"),
                fields.get("min_due_minor"),
                now,
                now,
            ),
        )
        statement_id = int(cur.lastrowid)
    row = get_statement_by_id(statement_id)
    assert row is not None
    return row


def get_statement_by_id(statement_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM statements WHERE id = ? AND deleted_at IS NULL",
            (statement_id,),
        ).fetchone()
    return dict(row) if row else None


def get_statement_by_period(account_id: int, period_start: str) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """
            SELECT * FROM statements
            WHERE account_id = ? AND period_start = ? AND deleted_at IS NULL
            """,
            (account_id, period_start),
        ).fetchone()
    return dict(row) if row else None


def list_statements(account_id: int, limit: int = 24) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """
            SELECT * FROM statements
            WHERE account_id = ? AND deleted_at IS NULL
            ORDER BY period_end DESC
            LIMIT ?
            """,
            (account_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def count_overlapping_periods(
    account_id: int,
    period_start: str,
    period_end: str,
    exclude_id: Optional[int] = None,
) -> int:
    query = """
        SELECT COUNT(*) FROM statements
        WHERE account_id = ? AND deleted_at IS NULL
          AND period_start <= ? AND period_end >= ?
    """
    params: list[Any] = [account_id, period_end, period_start]
    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)
    with _connection.connect() as con:
        row = con.execute(query, params).fetchone()
    return int(row[0]) if row else 0


def update_statement(statement_id: int, fields: dict[str, Any]) -> Optional[dict]:
    allowed = {"total_due_minor", "min_due_minor"}
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return get_statement_by_id(statement_id)
    updates["updated_at"] = _connection.now()
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [statement_id]
    with _connection.connect() as con:
        cur = con.execute(
            f"UPDATE statements SET {set_clause} WHERE id = ? AND deleted_at IS NULL",
            values,
        )
        if cur.rowcount == 0:
            return None
    return get_statement_by_id(statement_id)


def count_linked_transactions(statement_id: int) -> int:
    with _connection.connect() as con:
        row = con.execute(
            """
            SELECT COUNT(*) FROM transactions
            WHERE statement_id = ? AND deleted_at IS NULL
            """,
            (statement_id,),
        ).fetchone()
    return int(row[0]) if row else 0


def soft_delete_statement(statement_id: int) -> bool:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE statements
            SET deleted_at = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, statement_id),
        )
        return cur.rowcount > 0


def sum_statement_spend(statement_id: int) -> tuple[int, int]:
    """Return (total_debit_minor, total_credit_minor) excluding card_payment legs."""
    with _connection.connect() as con:
        rows = con.execute(
            """
            SELECT direction, COALESCE(SUM(amount_minor), 0)
            FROM transactions
            WHERE statement_id = ? AND deleted_at IS NULL
              AND kind != 'card_payment'
            GROUP BY direction
            """,
            (statement_id,),
        ).fetchall()
    totals = {"debit": 0, "credit": 0}
    for direction, total in rows:
        totals[direction] = int(total)
    return totals["debit"], totals["credit"]


def sum_spend_in_period(account_id: int, period_start: str, period_end: str) -> tuple[int, int]:
    """Sum debits/credits on a card account within a date range."""
    with _connection.connect() as con:
        rows = con.execute(
            """
            SELECT direction, COALESCE(SUM(amount_minor), 0)
            FROM transactions
            WHERE account_id = ? AND deleted_at IS NULL
              AND occurred_on BETWEEN ? AND ?
            GROUP BY direction
            """,
            (account_id, period_start, period_end),
        ).fetchall()
    totals = {"debit": 0, "credit": 0}
    for direction, total in rows:
        totals[direction] = int(total)
    return totals["debit"], totals["credit"]


def sum_statement_paid(statement_id: int) -> int:
    """Sum card_payment credit legs allocated to a statement — never stored."""
    with _connection.connect() as con:
        row = con.execute(
            """
            SELECT COALESCE(SUM(amount_minor), 0)
            FROM transactions
            WHERE statement_id = ? AND deleted_at IS NULL
              AND kind = 'card_payment' AND direction = 'credit'
            """,
            (statement_id,),
        ).fetchone()
    return int(row[0]) if row else 0
