from typing import Optional

from . import _connection


def get_profile_observations() -> list[dict]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT * FROM profile ORDER BY confidence DESC, updated_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def get_last_profile_update() -> Optional[str]:
    with _connection.connect() as con:
        row = con.execute("SELECT MAX(updated_at) FROM profile").fetchone()
    return row[0] if row else None


def replace_profile_observations(observations: list[dict]) -> None:
    """Clear all existing observations and insert the new set.

    Each item: {"text": str, "category": str, "confidence": float}.
    """
    now = _connection.now()
    with _connection.connect() as con:
        con.execute("DELETE FROM profile")
        for obs in observations:
            text = obs.get("text", "").strip()
            category = obs.get("category", "general").strip().lower()
            confidence = float(obs.get("confidence", 0.7))
            if text:
                con.execute(
                    "INSERT INTO profile (observation, category, confidence, updated_at) VALUES (?, ?, ?, ?)",
                    (text, category, confidence, now),
                )
