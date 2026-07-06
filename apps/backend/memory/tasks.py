from typing import Optional

from . import _connection


def add_task(text: str, due: Optional[str] = None) -> dict:
    with _connection.connect() as con:
        cur = con.execute(
            "INSERT INTO tasks (text, status, created_at, due) VALUES (?, 'open', ?, ?)",
            (text, _connection.now(), due),
        )
        task_id = cur.lastrowid
    row = get_task_by_id(task_id)
    assert row is not None
    return row


def complete_task(text: str) -> bool:
    with _connection.connect() as con:
        cur = con.execute(
            "SELECT id FROM tasks WHERE status='open' AND text LIKE ? LIMIT 1",
            (f"%{text}%",),
        )
        row = cur.fetchone()
        if row is None:
            return False
        con.execute("UPDATE tasks SET status='done' WHERE id=?", (row[0],))
    return True


def complete_task_by_id(task_id: int) -> Optional[dict]:
    """Mark task done by primary key. Returns updated row, or None if not found or not open."""
    with _connection.connect() as con:
        cur = con.execute(
            "SELECT id, status FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = cur.fetchone()
        if row is None or row[1] != "open":
            return None
        con.execute("UPDATE tasks SET status='done' WHERE id=?", (task_id,))
    return get_task_by_id(task_id)


def get_task_by_id(task_id: int) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return dict(row) if row else None


def find_task_by_text(text: str, status: Optional[str] = None) -> Optional[dict]:
    """Match task text substring — chat translator only."""
    if not text:
        return None
    query = "SELECT * FROM tasks WHERE text LIKE ?"
    params: list = [f"%{text}%"]
    if status is not None:
        query += " AND status = ?"
        params.append(status)
    query += " ORDER BY created_at DESC LIMIT 1"
    with _connection.connect(rows=True) as con:
        row = con.execute(query, params).fetchone()
    return dict(row) if row else None


def get_all_tasks(limit: Optional[int] = None) -> list[dict]:
    """Open and completed tasks — open first, newest first within each group."""
    query = (
        "SELECT * FROM tasks ORDER BY " "CASE status WHEN 'open' THEN 0 ELSE 1 END, created_at DESC"
    )
    params: tuple = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    with _connection.connect(rows=True) as con:
        rows = con.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def get_open_tasks(limit: Optional[int] = None) -> list[dict]:
    query = "SELECT * FROM tasks WHERE status='open' ORDER BY created_at"
    params: tuple = ()
    if limit is not None:
        query += " LIMIT ?"
        params = (limit,)
    with _connection.connect(rows=True) as con:
        rows = con.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def count_open_tasks() -> int:
    with _connection.connect() as con:
        return con.execute("SELECT COUNT(*) FROM tasks WHERE status='open'").fetchone()[0]


def get_recent_tasks(n: int = 5) -> list[dict]:
    """Most recent tasks regardless of status, newest first — for activity feeds."""
    with _connection.connect(rows=True) as con:
        rows = con.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (n,)).fetchall()
    return [dict(r) for r in rows]


def get_recent_open_tasks(n: int = 20) -> list[dict]:
    """Open tasks newest first — for the reflection job's recency window."""
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM tasks WHERE status='open' ORDER BY created_at DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_done_tasks_since(cutoff_iso: str, limit: int = 20) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM tasks WHERE status='done' AND created_at > ? ORDER BY created_at DESC LIMIT ?",
            (cutoff_iso, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_done_task_texts_for_date(date_str: str) -> list[str]:
    with _connection.connect() as con:
        rows = con.execute(
            "SELECT text FROM tasks WHERE status='done' AND date(created_at) = ?",
            (date_str,),
        ).fetchall()
    return [r[0] for r in rows]
