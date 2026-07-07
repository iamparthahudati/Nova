"""PriorityPolicy rows — persistence only. One active policy per owner."""

from __future__ import annotations

from typing import Any, Optional

from .. import _connection

DEFAULT_DEADLINE_WEIGHT = 1000
DEFAULT_DECAY_WEIGHT = 100


def ensure_default_policy_in(con, owner_id: int = 1) -> None:
    """Insert the default active policy for an owner using an open connection."""
    existing = con.execute(
        "SELECT 1 FROM work_priority_policies WHERE owner_id = ? AND is_active = 1",
        (owner_id,),
    ).fetchone()
    if existing is not None:
        return
    now = _connection.now()
    con.execute(
        """
        INSERT INTO work_priority_policies (
            owner_id, deadline_weight, decay_weight, is_active,
            source, created_at, updated_at
        ) VALUES (?, ?, ?, 1, 'manual', ?, ?)
        """,
        (owner_id, DEFAULT_DEADLINE_WEIGHT, DEFAULT_DECAY_WEIGHT, now, now),
    )


def ensure_default_policy(owner_id: int = 1) -> dict:
    """Idempotently guarantee an active policy row, returning it."""
    with _connection.connect() as con:
        ensure_default_policy_in(con, owner_id)
    row = get_active_policy(owner_id)
    assert row is not None
    return row


def get_active_policy(owner_id: int = 1) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM work_priority_policies WHERE owner_id = ? AND is_active = 1",
            (owner_id,),
        ).fetchone()
    return dict(row) if row else None


def update_policy_weights(fields: dict[str, Any]) -> Optional[dict]:
    """Update the active policy's weights under optimistic concurrency."""
    now = _connection.now()
    with _connection.connect() as con:
        cur = con.execute(
            """
            UPDATE work_priority_policies
               SET deadline_weight = ?, decay_weight = ?, updated_at = ?
             WHERE owner_id = ? AND is_active = 1 AND updated_at = ?
            """,
            (
                fields["deadline_weight"],
                fields["decay_weight"],
                now,
                fields["owner_id"],
                fields["expected_updated_at"],
            ),
        )
        if cur.rowcount == 0:
            return None
    return get_active_policy(fields["owner_id"])
