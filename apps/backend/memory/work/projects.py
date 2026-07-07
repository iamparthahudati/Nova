"""Project rows — persistence only. Holding ledger (position anchor)."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection

_UPDATABLE = {"name", "objective", "status", "planned_start_on", "planned_end_on"}


def create_project(fields: dict[str, Any]) -> dict:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            INSERT INTO work_projects (
                owner_id, name, objective, status,
                planned_start_on, planned_end_on, source, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                fields["owner_id"],
                fields["name"],
                fields.get("objective"),
                fields.get("status", "idea"),
                fields.get("planned_start_on"),
                fields.get("planned_end_on"),
                fields.get("source", "manual"),
                now,
                now,
            ),
        )
        project_id = int(cur.lastrowid)
    row = get_project_by_id(project_id, fields["owner_id"])
    assert row is not None
    return row


def get_project_by_id(project_id: int, owner_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM work_projects WHERE id = ? AND owner_id = ?",
            (project_id, owner_id),
        ).fetchone()
    return dict(row) if row else None


def find_live_by_name(owner_id: int, name: str) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """
            SELECT * FROM work_projects
             WHERE owner_id = ? AND name = ? COLLATE NOCASE AND archived_at IS NULL
            """,
            (owner_id, name),
        ).fetchone()
    return dict(row) if row else None


def list_live_projects(owner_id: int) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """
            SELECT * FROM work_projects
             WHERE owner_id = ? AND archived_at IS NULL
             ORDER BY name COLLATE NOCASE
            """,
            (owner_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def update_project(fields: dict[str, Any]) -> Optional[dict]:
    """Patch live-project columns under optimistic concurrency."""
    patch = {key: value for key, value in fields.items() if key in _UPDATABLE}
    now = _connection.now()
    set_clause = ", ".join(f"{key} = ?" for key in patch)
    set_clause = f"{set_clause}, updated_at = ?" if set_clause else "updated_at = ?"
    values = [
        *patch.values(),
        now,
        fields["project_id"],
        fields["owner_id"],
        fields["expected_updated_at"],
    ]
    with _connection.connect() as con:
        cur = con.execute(
            f"""
            UPDATE work_projects SET {set_clause}
             WHERE id = ? AND owner_id = ? AND archived_at IS NULL AND updated_at = ?
            """,
            values,
        )
        if cur.rowcount == 0:
            return None
    return get_project_by_id(fields["project_id"], fields["owner_id"])


def complete_project(project_id: int, owner_id: int, expected_updated_at: str) -> Optional[dict]:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE work_projects
               SET status = 'completed', updated_at = ?
             WHERE id = ? AND owner_id = ? AND archived_at IS NULL AND updated_at = ?
            """,
            (now, project_id, owner_id, expected_updated_at),
        )
        if cur.rowcount == 0:
            return None
    return get_project_by_id(project_id, owner_id)


def archive_project(project_id: int, owner_id: int, expected_updated_at: str) -> Optional[dict]:
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE work_projects
               SET archived_at = ?, updated_at = ?
             WHERE id = ? AND owner_id = ? AND archived_at IS NULL AND updated_at = ?
            """,
            (now, now, project_id, owner_id, expected_updated_at),
        )
        if cur.rowcount == 0:
            return None
    return get_project_by_id(project_id, owner_id)
