"""Account rows — persistence only."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection


def create_account(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            INSERT INTO accounts (
                name, type, classification, currency,
                opening_balance_minor, opening_balance_on,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["name"],
                fields["type"],
                fields["classification"],
                fields.get("currency", "INR"),
                fields.get("opening_balance_minor", 0),
                fields["opening_balance_on"],
                now,
                now,
            ),
        )
        account_id = int(cur.lastrowid)
    row = get_account_by_id(account_id)
    assert row is not None
    return row


def get_account_by_id(account_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return dict(row) if row else None


def list_accounts(include_archived: bool = False) -> list[dict]:
    query = "SELECT * FROM accounts"
    if not include_archived:
        query += " WHERE archived_at IS NULL"
    query += " ORDER BY name COLLATE NOCASE"
    with _connection.connect(rows=True) as con:
        rows = con.execute(query).fetchall()
    return [dict(row) for row in rows]


def update_account(account_id: int, fields: dict[str, Any]) -> Optional[dict]:
    allowed = {"name", "opening_balance_minor", "opening_balance_on"}
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return get_account_by_id(account_id)
    updates["updated_at"] = _connection.now()
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [account_id]
    with _connection.connect() as con:
        cur = con.execute(
            f"UPDATE accounts SET {set_clause} WHERE id = ? AND archived_at IS NULL",
            values,
        )
        if cur.rowcount == 0:
            return None
    return get_account_by_id(account_id)


def archive_account(account_id: int) -> Optional[dict]:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            "UPDATE accounts SET archived_at = ?, updated_at = ? WHERE id = ? AND archived_at IS NULL",
            (now, now, account_id),
        )
        if cur.rowcount == 0:
            return None
    return get_account_by_id(account_id)


def count_live_transactions(account_id: int) -> int:
    with _connection.connect() as con:
        row = con.execute(
            "SELECT COUNT(*) FROM transactions WHERE account_id = ? AND deleted_at IS NULL",
            (account_id,),
        ).fetchone()
    return int(row[0]) if row else 0
