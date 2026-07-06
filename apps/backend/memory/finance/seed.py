"""Idempotent finance bootstrap rows."""

from __future__ import annotations

from datetime import date

from .. import _connection


def ensure_default_cash_account() -> int:
    """Return the default Cash account id, creating it if absent."""
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT id FROM accounts WHERE type = 'cash' AND archived_at IS NULL LIMIT 1",
        ).fetchone()
        if row is not None:
            return int(row["id"])

        today = date.today().isoformat()
        now = _connection.now()
        cur = con.execute(
            """
            INSERT INTO accounts (
                name, type, classification, currency,
                opening_balance_minor, opening_balance_on,
                created_at, updated_at
            ) VALUES (?, 'cash', 'asset', 'INR', 0, ?, ?, ?)
            """,
            ("Cash", today, now, now),
        )
        return int(cur.lastrowid)
