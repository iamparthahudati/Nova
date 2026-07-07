"""WorkItem rows — persistence only. Commitment ledger."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection

_UPDATABLE = {
    "title",
    "estimate_minutes",
    "estimate_confidence",
    "deadline_on",
    "deadline_hardness",
}

_OPEN_STATUSES = ("backlog", "todo", "in_progress", "in_review")


def insert_work_item_in(con, fields: dict[str, Any]) -> int:
    """Insert one task row on an open connection; caller owns the transaction.

    Shared by the standalone create and the composite triage/promote writers so
    the two-table orchestrations stay in a single transaction (schema §9).
    """
    now = _connection.now()
    cur = con.execute(
        """
        INSERT INTO work_items (
            owner_id, project_id, type, title, status,
            estimate_minutes, estimate_confidence, deadline_on, deadline_hardness,
            action_item_id, source, created_at, updated_at
        ) VALUES (?, ?, 'task', ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            fields["owner_id"],
            fields["project_id"],
            fields["title"],
            fields.get("status", "backlog"),
            fields.get("estimate_minutes"),
            fields.get("estimate_confidence"),
            fields.get("deadline_on"),
            fields.get("deadline_hardness"),
            fields.get("action_item_id"),
            fields.get("source", "manual"),
            now,
            now,
        ),
    )
    return int(cur.lastrowid)


def create_work_item(fields: dict[str, Any]) -> dict:
    with _connection.connect() as con:
        item_id = insert_work_item_in(con, fields)
    row = get_work_item_by_id(item_id, fields["owner_id"])
    assert row is not None
    return row


def get_work_item_by_id(item_id: int, owner_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM work_items WHERE id = ? AND owner_id = ?",
            (item_id, owner_id),
        ).fetchone()
    return dict(row) if row else None


def find_by_action_item_id(action_item_id: int, owner_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """
            SELECT * FROM work_items
             WHERE action_item_id = ? AND owner_id = ? AND deleted_at IS NULL
            """,
            (action_item_id, owner_id),
        ).fetchone()
    return dict(row) if row else None


def list_live_items_for_project(project_id: int, owner_id: int) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """
            SELECT * FROM work_items
             WHERE project_id = ? AND owner_id = ? AND deleted_at IS NULL
             ORDER BY id
            """,
            (project_id, owner_id),
        ).fetchall()
    return [dict(row) for row in rows]


def list_open_commitments(owner_id: int) -> list[dict]:
    placeholders = ", ".join("?" for _ in _OPEN_STATUSES)
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            f"""
            SELECT * FROM work_items
             WHERE owner_id = ? AND deleted_at IS NULL AND status IN ({placeholders})
             ORDER BY id
            """,
            (owner_id, *_OPEN_STATUSES),
        ).fetchall()
    return [dict(row) for row in rows]


def update_work_item(fields: dict[str, Any]) -> Optional[dict]:
    """Patch a live work item's facets under optimistic concurrency."""
    patch = {key: value for key, value in fields.items() if key in _UPDATABLE}
    now = _connection.now()
    set_clause = ", ".join(f"{key} = ?" for key in patch)
    set_clause = f"{set_clause}, updated_at = ?" if set_clause else "updated_at = ?"
    values = [
        *patch.values(),
        now,
        fields["item_id"],
        fields["owner_id"],
        fields["expected_updated_at"],
    ]
    with _connection.connect() as con:
        cur = con.execute(
            f"""
            UPDATE work_items SET {set_clause}
             WHERE id = ? AND owner_id = ? AND deleted_at IS NULL AND updated_at = ?
            """,
            values,
        )
        if cur.rowcount == 0:
            return None
    return get_work_item_by_id(fields["item_id"], fields["owner_id"])


def transition_work_item(fields: dict[str, Any]) -> Optional[dict]:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE work_items
               SET status = ?, updated_at = ?
             WHERE id = ? AND owner_id = ? AND deleted_at IS NULL AND updated_at = ?
            """,
            (
                fields["to_status"],
                now,
                fields["item_id"],
                fields["owner_id"],
                fields["expected_updated_at"],
            ),
        )
        if cur.rowcount == 0:
            return None
    return get_work_item_by_id(fields["item_id"], fields["owner_id"])


def soft_delete_work_item(item_id: int, owner_id: int, expected_updated_at: str) -> Optional[dict]:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE work_items
               SET deleted_at = ?, updated_at = ?
             WHERE id = ? AND owner_id = ? AND deleted_at IS NULL AND updated_at = ?
            """,
            (now, now, item_id, owner_id, expected_updated_at),
        )
        if cur.rowcount == 0:
            return None
    return get_work_item_by_id(item_id, owner_id)
