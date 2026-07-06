from typing import Optional

from . import _connection


def add_progress(note: str, area: str = "") -> None:
    with _connection.connect() as con:
        con.execute(
            "INSERT INTO progress (area, note, created_at) VALUES (?, ?, ?)",
            (area, note, _connection.now()),
        )


def get_recent_progress(n: int = 10) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM progress ORDER BY created_at DESC LIMIT ?", (n,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_progress_since(cutoff_iso: str, limit: int = 20) -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM progress WHERE created_at > ? ORDER BY created_at DESC LIMIT ?",
            (cutoff_iso, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_progress_notes_for_date(
    date_str: str, exclude_area: Optional[str] = None, limit: int = 3
) -> list[str]:
    query = "SELECT note FROM progress WHERE date(created_at) = ?"
    params: list = [date_str]
    if exclude_area is not None:
        query += " AND (area IS NULL OR area != ?)"
        params.append(exclude_area)
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    with _connection.connect() as con:
        rows = con.execute(query, tuple(params)).fetchall()
    return [r[0] for r in rows]
