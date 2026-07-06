"""Category rows — persistence only."""

from __future__ import annotations

from typing import Optional

from .. import _connection


def create_category(name: str) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            "INSERT INTO finance_categories (name, created_at, updated_at) VALUES (?, ?, ?)",
            (name, now, now),
        )
        category_id = int(cur.lastrowid)
    row = get_category_by_id(category_id)
    assert row is not None
    return row


def get_category_by_id(category_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM finance_categories WHERE id = ? AND deleted_at IS NULL",
            (category_id,),
        ).fetchone()
    return dict(row) if row else None


def get_category_by_name(name: str) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """
            SELECT * FROM finance_categories
            WHERE name = ? COLLATE NOCASE AND deleted_at IS NULL
            """,
            (name,),
        ).fetchone()
    return dict(row) if row else None


def list_categories() -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM finance_categories WHERE deleted_at IS NULL ORDER BY name COLLATE NOCASE",
        ).fetchall()
    return [dict(row) for row in rows]


def update_category(category_id: int, name: str) -> Optional[dict]:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE finance_categories
            SET name = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (name, now, category_id),
        )
        if cur.rowcount == 0:
            return None
    return get_category_by_id(category_id)


def soft_delete_category(category_id: int) -> bool:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE finance_categories
            SET deleted_at = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, category_id),
        )
        return cur.rowcount > 0
