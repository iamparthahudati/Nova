"""ActionItem rows — persistence only. Commitment ledger (pre-promotion)."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection
from . import items


def promote_action_item(fields: dict[str, Any]) -> Optional[tuple[dict, dict]]:
    """Create the work item and mark the action item promoted in one transaction.

    Returns (action_item_row, work_item_row) or None when the optimistic-
    concurrency guard matches no open row (schema §9 composite promotion).
    """
    item_id = fields["item_id"]
    owner_id = fields["owner_id"]
    now = _connection.now()
    work_fields = {**fields["work_item_fields"], "action_item_id": item_id}
    with _connection.connect() as con:
        work_item_id = items.insert_work_item_in(con, work_fields)
        cur = con.execute(
            """
            UPDATE work_action_items
               SET status = 'promoted', promoted_work_item_id = ?, updated_at = ?
             WHERE id = ? AND owner_id = ? AND status = 'open'
               AND deleted_at IS NULL AND updated_at = ?
            """,
            (work_item_id, now, item_id, owner_id, fields["expected_updated_at"]),
        )
        if cur.rowcount == 0:
            con.rollback()
            return None
    action_row = get_action_item_by_id(item_id, owner_id)
    work_row = items.get_work_item_by_id(work_item_id, owner_id)
    assert action_row is not None and work_row is not None
    return action_row, work_row


def create_action_item(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            INSERT INTO work_action_items (
                owner_id, title, status, note_id, source, created_at, updated_at
            ) VALUES (?, ?, 'open', ?, ?, ?, ?)
            """,
            (
                fields["owner_id"],
                fields["title"],
                fields.get("note_id"),
                fields.get("source", "manual"),
                now,
                now,
            ),
        )
        item_id = int(cur.lastrowid)
    row = get_action_item_by_id(item_id, fields["owner_id"])
    assert row is not None
    return row


def get_action_item_by_id(item_id: int, owner_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM work_action_items WHERE id = ? AND owner_id = ?",
            (item_id, owner_id),
        ).fetchone()
    return dict(row) if row else None


def list_open_action_items(owner_id: int, limit: int = 50) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """
            SELECT * FROM work_action_items
             WHERE owner_id = ? AND status = 'open' AND deleted_at IS NULL
             ORDER BY created_at DESC, id DESC
             LIMIT ?
            """,
            (owner_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def mark_promoted(fields: dict[str, Any]) -> Optional[dict]:
    """Link an open action item to its new work item under optimistic concurrency."""
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE work_action_items
               SET status = 'promoted', promoted_work_item_id = ?, updated_at = ?
             WHERE id = ? AND owner_id = ? AND status = 'open'
               AND deleted_at IS NULL AND updated_at = ?
            """,
            (
                fields["work_item_id"],
                now,
                fields["item_id"],
                fields["owner_id"],
                fields["expected_updated_at"],
            ),
        )
        if cur.rowcount == 0:
            return None
    return get_action_item_by_id(fields["item_id"], fields["owner_id"])


def mark_dismissed(item_id: int, owner_id: int, expected_updated_at: str) -> Optional[dict]:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE work_action_items
               SET status = 'dismissed', updated_at = ?
             WHERE id = ? AND owner_id = ? AND status = 'open'
               AND deleted_at IS NULL AND updated_at = ?
            """,
            (now, item_id, owner_id, expected_updated_at),
        )
        if cur.rowcount == 0:
            return None
    return get_action_item_by_id(item_id, owner_id)
