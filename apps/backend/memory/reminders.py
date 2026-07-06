from datetime import datetime
from typing import Optional

from . import _connection


def add_reminder(text: str, remind_date: datetime, remind_time: Optional[str] = None) -> dict:
    """`remind_time` is canonical zero-padded 24h 'HH:MM', or None for a
    day-level reminder (surfaces in the briefing/daily plan only)."""
    date_str = remind_date.strftime("%Y-%m-%d")
    with _connection.connect() as con:
        cur = con.execute(
            "INSERT INTO reminders (text, remind_date, remind_time, created_at) VALUES (?, ?, ?, ?)",
            (text, date_str, remind_time, _connection.now()),
        )
        row_id = cur.lastrowid
    row = get_reminder_by_id(row_id)
    assert row is not None
    return row


def get_reminder_by_id(reminder_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
    return dict(row) if row else None


def get_latest_reminder(text: str) -> Optional[dict]:
    """Most recent reminder with matching text — chat translator only."""
    if not text:
        return None
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM reminders WHERE text LIKE ? ORDER BY created_at DESC LIMIT 1",
            (f"%{text}%",),
        ).fetchone()
    return dict(row) if row else None


def get_due_reminders(date_obj: Optional[datetime] = None) -> list[dict]:
    """Return reminders whose remind_date matches the given local date (default today)."""
    if date_obj is None:
        date_obj = datetime.now()
    date_str = date_obj.strftime("%Y-%m-%d")
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM reminders WHERE remind_date = ? ORDER BY created_at",
            (date_str,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_upcoming_reminders(limit: int = 20) -> list[dict]:
    """Reminders due today or later, soonest first — for dashboard views."""
    today = datetime.now().strftime("%Y-%m-%d")
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM reminders WHERE remind_date >= ? ORDER BY remind_date LIMIT ?",
            (today, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def count_reminders() -> int:
    with _connection.connect() as con:
        return con.execute("SELECT COUNT(*) FROM reminders").fetchone()[0]


def get_recent_reminders(n: int = 5) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM reminders ORDER BY created_at DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(r) for r in rows]
