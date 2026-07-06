from typing import Optional

from . import _connection


def add_money(type_: str, amount: float, note: str = "") -> dict:
    with _connection.connect() as con:
        cur = con.execute(
            "INSERT INTO money (type, amount, note, created_at) VALUES (?, ?, ?, ?)",
            (type_, amount, note, _connection.now()),
        )
        row_id = cur.lastrowid
    row = get_money_by_id(row_id)
    assert row is not None
    return row


def get_money_by_id(row_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM money WHERE id = ?", (row_id,)).fetchone()
    return dict(row) if row else None


def get_latest_money(type_: str, amount: float) -> Optional[dict]:
    """Most recent money row matching type and amount — chat translator only."""
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM money WHERE type = ? AND amount = ? ORDER BY created_at DESC LIMIT 1",
            (type_, amount),
        ).fetchone()
    return dict(row) if row else None


def get_recent_money(n: int = 10) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute("SELECT * FROM money ORDER BY created_at DESC LIMIT ?", (n,)).fetchall()
    return [dict(r) for r in rows]


def get_money_since(cutoff_iso: str, limit: int = 30) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM money WHERE created_at > ? ORDER BY created_at DESC LIMIT ?",
            (cutoff_iso, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_money_totals_between(start_date: str, end_date: str) -> tuple[float, float]:
    """Return (total_earned, total_spent) for dates in [start_date, end_date] (YYYY-MM-DD, inclusive)."""
    with _connection.connect() as con:
        rows = con.execute(
            "SELECT type, SUM(amount) FROM money WHERE date(created_at) BETWEEN ? AND ? GROUP BY type",
            (start_date, end_date),
        ).fetchall()
    totals = {"earned": 0.0, "spent": 0.0}
    for type_, total in rows:
        totals[type_] = total or 0.0
    return totals["earned"], totals["spent"]


def get_money_totals_for_date(date_obj) -> tuple[float, float]:
    """Return (total_earned, total_spent) for the given local calendar date.

    created_at is stored as UTC; this filters on the UTC date, same as
    the system prompt's "today" already treats local and UTC dates as equivalent.
    """
    date_str = date_obj.strftime("%Y-%m-%d")
    return get_money_totals_between(date_str, date_str)
