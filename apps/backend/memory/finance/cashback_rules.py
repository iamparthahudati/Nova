"""Cashback rule rows — persistence only."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection


def create_cashback_rule(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            INSERT INTO cashback_rules (
                program_id, account_id, name, flat_rate_bps,
                category_multipliers, merchant_multipliers,
                excluded_category_ids, excluded_merchant_ids,
                excluded_mcc_codes, excluded_transaction_kinds,
                monthly_cap_minor, minimum_spend_minor,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["program_id"],
                fields.get("account_id"),
                fields["name"],
                fields["flat_rate_bps"],
                fields.get("category_multipliers", "{}"),
                fields.get("merchant_multipliers", "{}"),
                fields.get("excluded_category_ids", "[]"),
                fields.get("excluded_merchant_ids", "[]"),
                fields.get("excluded_mcc_codes", "[]"),
                fields.get("excluded_transaction_kinds", "[]"),
                fields.get("monthly_cap_minor"),
                fields.get("minimum_spend_minor", 0),
                now,
                now,
            ),
        )
        rule_id = int(cur.lastrowid)
    row = get_cashback_rule_by_id(rule_id)
    assert row is not None
    return row


def get_cashback_rule_by_id(rule_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM cashback_rules WHERE id = ? AND deleted_at IS NULL",
            (rule_id,),
        ).fetchone()
    return dict(row) if row else None


def list_cashback_rules(
    program_id: Optional[int] = None,
    account_id: Optional[int] = None,
) -> list[dict]:
    query = "SELECT * FROM cashback_rules WHERE deleted_at IS NULL"
    params: list[Any] = []
    if program_id is not None:
        query += " AND program_id = ?"
        params.append(program_id)
    if account_id is not None:
        query += " AND account_id = ?"
        params.append(account_id)
    query += " ORDER BY id"
    with _connection.connect(rows=True) as con:
        rows = con.execute(query, params).fetchall()
    return [dict(row) for row in rows]
