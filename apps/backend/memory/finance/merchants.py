"""Merchant rows — persistence only."""

from __future__ import annotations

from typing import Optional

from .. import _connection


def create_merchant(name: str) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            "INSERT INTO finance_merchants (name, created_at, updated_at) VALUES (?, ?, ?)",
            (name, now, now),
        )
        merchant_id = int(cur.lastrowid)
    row = get_merchant_by_id(merchant_id)
    assert row is not None
    return row


def get_merchant_by_id(merchant_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM finance_merchants WHERE id = ? AND deleted_at IS NULL",
            (merchant_id,),
        ).fetchone()
    return dict(row) if row else None


def get_merchant_by_name(name: str) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """
            SELECT * FROM finance_merchants
            WHERE name = ? COLLATE NOCASE AND deleted_at IS NULL
            """,
            (name,),
        ).fetchone()
    return dict(row) if row else None


def list_merchants() -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM finance_merchants WHERE deleted_at IS NULL ORDER BY name COLLATE NOCASE",
        ).fetchall()
    return [dict(row) for row in rows]


def update_merchant(merchant_id: int, name: str) -> Optional[dict]:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE finance_merchants
            SET name = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (name, now, merchant_id),
        )
        if cur.rowcount == 0:
            return None
    return get_merchant_by_id(merchant_id)


def soft_delete_merchant(merchant_id: int) -> bool:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE finance_merchants
            SET deleted_at = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, merchant_id),
        )
        return cur.rowcount > 0
