"""Public health probes — the only Memory surface for connectivity checks."""

from . import _connection


def ping_database() -> None:
    """Verify SQLite is reachable. Raises sqlite3.Error or OSError on failure."""
    with _connection.connect() as con:
        con.execute("SELECT 1").fetchone()


def semantic_index_exists() -> bool:
    """True when the LanceDB index directory exists on disk."""
    return _connection.LANCEDB_PATH.exists()
