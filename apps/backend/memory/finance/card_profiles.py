"""Credit card profile rows — persistence only."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection


def create_card_profile(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        con.execute(
            """
            INSERT INTO card_profiles (
                account_id, network, last4, credit_limit_minor,
                statement_day, due_day_offset, autopay,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["account_id"],
                fields.get("network"),
                fields.get("last4"),
                fields["credit_limit_minor"],
                fields["statement_day"],
                fields["due_day_offset"],
                1 if fields.get("autopay") else 0,
                now,
                now,
            ),
        )
    row = get_card_profile(fields["account_id"])
    assert row is not None
    return row


def get_card_profile(account_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM card_profiles WHERE account_id = ?",
            (account_id,),
        ).fetchone()
    return dict(row) if row else None


def list_card_profiles() -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """
            SELECT cp.* FROM card_profiles cp
            JOIN accounts a ON a.id = cp.account_id
            WHERE a.archived_at IS NULL
            ORDER BY a.name COLLATE NOCASE
            """,
        ).fetchall()
    return [dict(row) for row in rows]


def update_card_profile(account_id: int, fields: dict[str, Any]) -> Optional[dict]:
    allowed = {
        "network",
        "last4",
        "credit_limit_minor",
        "statement_day",
        "due_day_offset",
        "autopay",
    }
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return get_card_profile(account_id)
    if "autopay" in updates:
        updates["autopay"] = 1 if updates["autopay"] else 0
    updates["updated_at"] = _connection.now()
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [account_id]
    with _connection.connect() as con:
        cur = con.execute(
            f"UPDATE card_profiles SET {set_clause} WHERE account_id = ?",
            values,
        )
        if cur.rowcount == 0:
            return None
    return get_card_profile(account_id)


def create_credit_card_account(
    account_fields: dict[str, Any], profile_fields: dict[str, Any]
) -> tuple[dict, dict]:
    """Atomically create account + card profile."""
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
                account_fields["name"],
                account_fields["type"],
                account_fields["classification"],
                account_fields.get("currency", "INR"),
                account_fields.get("opening_balance_minor", 0),
                account_fields["opening_balance_on"],
                now,
                now,
            ),
        )
        account_id = int(cur.lastrowid)
        con.execute(
            """
            INSERT INTO card_profiles (
                account_id, network, last4, credit_limit_minor,
                statement_day, due_day_offset, autopay,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                account_id,
                profile_fields.get("network"),
                profile_fields.get("last4"),
                profile_fields["credit_limit_minor"],
                profile_fields["statement_day"],
                profile_fields["due_day_offset"],
                1 if profile_fields.get("autopay") else 0,
                now,
                now,
            ),
        )
    from .accounts import get_account_by_id

    account_row = get_account_by_id(account_id)
    profile_row = get_card_profile(account_id)
    assert account_row is not None and profile_row is not None
    return account_row, profile_row
