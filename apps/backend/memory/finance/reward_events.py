"""Reward event rows — persistence only."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection


def create_reward_event(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            INSERT INTO reward_events (
                program_id, kind, direction, amount,
                transaction_id, note, occurred_on,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["program_id"],
                fields["kind"],
                fields["direction"],
                fields["amount"],
                fields.get("transaction_id"),
                fields.get("note"),
                fields["occurred_on"],
                now,
                now,
            ),
        )
        event_id = int(cur.lastrowid)
    row = get_reward_event_by_id(event_id)
    assert row is not None
    return row


def get_reward_event_by_id(event_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM reward_events WHERE id = ? AND deleted_at IS NULL",
            (event_id,),
        ).fetchone()
    return dict(row) if row else None


def list_reward_events(
    program_id: int,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """
            SELECT * FROM reward_events
            WHERE program_id = ? AND deleted_at IS NULL
            ORDER BY occurred_on DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (program_id, limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


def sum_by_direction(
    program_id: int,
    as_of: Optional[str] = None,
) -> tuple[int, int]:
    """Return (total_credit, total_debit) for balance fold."""
    query = """
        SELECT direction, COALESCE(SUM(amount), 0)
        FROM reward_events
        WHERE program_id = ? AND deleted_at IS NULL
    """
    params: list[Any] = [program_id]
    if as_of is not None:
        query += " AND occurred_on <= ?"
        params.append(as_of)
    query += " GROUP BY direction"
    with _connection.connect() as con:
        rows = con.execute(query, params).fetchall()
    totals = {"credit": 0, "debit": 0}
    for direction, total in rows:
        totals[direction] = int(total)
    return totals["credit"], totals["debit"]


def sum_earned_in_period(
    program_id: int,
    start_date: str,
    end_date: str,
) -> int:
    """Sum credit events with kind=earned in a date range."""
    with _connection.connect() as con:
        row = con.execute(
            """
            SELECT COALESCE(SUM(amount), 0)
            FROM reward_events
            WHERE program_id = ? AND deleted_at IS NULL
              AND kind = 'earned' AND direction = 'credit'
              AND occurred_on BETWEEN ? AND ?
            """,
            (program_id, start_date, end_date),
        ).fetchone()
    return int(row[0]) if row else 0


def soft_delete_reward_event(event_id: int) -> bool:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE reward_events
            SET deleted_at = ?, updated_at = ?
            WHERE id = ? AND deleted_at IS NULL
            """,
            (now, now, event_id),
        )
        return cur.rowcount > 0
