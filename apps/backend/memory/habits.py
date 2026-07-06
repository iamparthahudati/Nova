from datetime import datetime

from . import _connection


def log_habit(name: str) -> dict:
    date_str = datetime.now().strftime("%Y-%m-%d")
    with _connection.connect() as con:
        cur = con.execute(
            "INSERT INTO habits (name, logged_date, created_at) VALUES (?, ?, ?)",
            (name, date_str, _connection.now()),
        )
        row_id = cur.lastrowid
    row = get_habit_by_id(row_id)
    assert row is not None
    return row


def get_habit_by_id(habit_id: int) -> dict | None:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM habits WHERE id = ?", (habit_id,)).fetchone()
    return dict(row) if row else None


def get_latest_habit(name: str) -> dict | None:
    """Most recent habit log with matching name — chat translator only."""
    if not name:
        return None
    with _connection.connect(rows=True) as con:
        row = con.execute(
            "SELECT * FROM habits WHERE name LIKE ? ORDER BY created_at DESC LIMIT 1",
            (f"%{name}%",),
        ).fetchone()
    return dict(row) if row else None


def get_habits_today() -> list[dict]:
    date_str = datetime.now().strftime("%Y-%m-%d")
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM habits WHERE logged_date = ? ORDER BY created_at",
            (date_str,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_recent_habits(n: int = 5) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute("SELECT * FROM habits ORDER BY created_at DESC LIMIT ?", (n,)).fetchall()
    return [dict(r) for r in rows]
