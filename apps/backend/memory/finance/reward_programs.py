"""Reward program rows — persistence only."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection


def create_reward_program(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            INSERT INTO reward_programs (
                account_id, name, unit,
                earn_rate_note, expiry_note,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["account_id"],
                fields["name"],
                fields["unit"],
                fields.get("earn_rate_note"),
                fields.get("expiry_note"),
                now,
                now,
            ),
        )
        program_id = int(cur.lastrowid)
    row = get_reward_program_by_id(program_id)
    assert row is not None
    return row


def get_reward_program_by_id(program_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM reward_programs WHERE id = ? AND deleted_at IS NULL",
            (program_id,),
        ).fetchone()
    return dict(row) if row else None


def list_reward_programs(account_id: Optional[int] = None) -> list[dict]:
    query = "SELECT * FROM reward_programs WHERE deleted_at IS NULL"
    params: list[Any] = []
    if account_id is not None:
        query += " AND account_id = ?"
        params.append(account_id)
    query += " ORDER BY name COLLATE NOCASE"
    with _connection.connect(rows=True) as con:
        rows = con.execute(query, params).fetchall()
    return [dict(row) for row in rows]


def update_reward_program(program_id: int, fields: dict[str, Any]) -> Optional[dict]:
    allowed = {"name", "earn_rate_note", "expiry_note"}
    updates = {key: value for key, value in fields.items() if key in allowed}
    if not updates:
        return get_reward_program_by_id(program_id)
    updates["updated_at"] = _connection.now()
    set_clause = ", ".join(f"{key} = ?" for key in updates)
    values = list(updates.values()) + [program_id]
    with _connection.connect() as con:
        cur = con.execute(
            f"UPDATE reward_programs SET {set_clause} WHERE id = ? AND deleted_at IS NULL",
            values,
        )
        if cur.rowcount == 0:
            return None
    return get_reward_program_by_id(program_id)


def soft_delete_reward_program(program_id: int) -> bool:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE reward_programs
            SET deleted_at = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, program_id),
        )
        return cur.rowcount > 0


def count_live_reward_events(program_id: int) -> int:
    with _connection.connect() as con:
        row = con.execute(
            """
            SELECT COUNT(*) FROM reward_events
            WHERE program_id = ? AND deleted_at IS NULL
            """,
            (program_id,),
        ).fetchone()
    return int(row[0]) if row else 0
