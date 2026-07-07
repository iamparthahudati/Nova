"""Capture note rows — persistence only. Artifact ledger (intake)."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection
from . import items


def triage_note_to_task(fields: dict[str, Any]) -> Optional[tuple[dict, dict]]:
    """Create a task and mark the source note triaged in one transaction.

    Returns (note_row, work_item_row) or None when the note is no longer a live
    captured row matching the concurrency token (schema §9 triage → task).
    """
    note_id = fields["note_id"]
    owner_id = fields["owner_id"]
    now = _connection.now()
    with _connection.connect() as con:
        work_item_id = items.insert_work_item_in(con, fields["work_item_fields"])
        cur = con.execute(
            """
            UPDATE work_notes
               SET status = 'triaged', outcome_kind = 'work_item', outcome_id = ?,
                   updated_at = ?
             WHERE id = ? AND owner_id = ? AND status = 'captured'
               AND deleted_at IS NULL AND updated_at = ?
            """,
            (work_item_id, now, note_id, owner_id, fields["expected_updated_at"]),
        )
        if cur.rowcount == 0:
            con.rollback()
            return None
    note_row = get_note_by_id(note_id, owner_id)
    work_row = items.get_work_item_by_id(work_item_id, owner_id)
    assert note_row is not None and work_row is not None
    return note_row, work_row


def create_note(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            INSERT INTO work_notes (
                owner_id, body, capture_source, captured_on, status,
                capture_idempotency_key, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'captured', ?, ?, ?, ?)
            """,
            (
                fields["owner_id"],
                fields["body"],
                fields["capture_source"],
                fields["captured_on"],
                fields.get("capture_idempotency_key"),
                fields.get("source", "manual"),
                now,
                now,
            ),
        )
        note_id = int(cur.lastrowid)
    row = get_note_by_id(note_id, fields["owner_id"])
    assert row is not None
    return row


def get_note_by_id(note_id: int, owner_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM work_notes WHERE id = ? AND owner_id = ?",
            (note_id, owner_id),
        ).fetchone()
    return dict(row) if row else None


def find_by_idempotency_key(owner_id: int, key: str) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """
            SELECT * FROM work_notes
             WHERE owner_id = ? AND capture_idempotency_key = ? AND deleted_at IS NULL
            """,
            (owner_id, key),
        ).fetchone()
    return dict(row) if row else None


def list_capture_inbox(owner_id: int, limit: int = 50) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """
            SELECT * FROM work_notes
             WHERE owner_id = ? AND status = 'captured' AND deleted_at IS NULL
             ORDER BY captured_on DESC, id DESC
             LIMIT ?
            """,
            (owner_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def triage_note(fields: dict[str, Any]) -> Optional[dict]:
    """Resolve an inbox note to a terminal status under optimistic concurrency."""
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE work_notes
               SET status = ?, outcome_kind = ?, outcome_id = ?, updated_at = ?
             WHERE id = ? AND owner_id = ? AND status = 'captured'
               AND deleted_at IS NULL AND updated_at = ?
            """,
            (
                fields["status"],
                fields.get("outcome_kind"),
                fields.get("outcome_id"),
                now,
                fields["note_id"],
                fields["owner_id"],
                fields["expected_updated_at"],
            ),
        )
        if cur.rowcount == 0:
            return None
    return get_note_by_id(fields["note_id"], fields["owner_id"])


def soft_delete_note(note_id: int, owner_id: int, expected_updated_at: str) -> Optional[dict]:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE work_notes
               SET deleted_at = ?, updated_at = ?
             WHERE id = ? AND owner_id = ? AND deleted_at IS NULL AND updated_at = ?
            """,
            (now, now, note_id, owner_id, expected_updated_at),
        )
        if cur.rowcount == 0:
            return None
    return get_note_by_id(note_id, owner_id)
