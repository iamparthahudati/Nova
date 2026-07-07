"""WorkOS memory scaffold — real SQLite, no mocks."""

from __future__ import annotations

from memory import _connection
from memory.schema import init_db
from memory.work.migrations import migrate_work_schema, verify_work_table_governance


def test_migrate_work_schema_is_idempotent(tmp_path, monkeypatch):
    db_path = tmp_path / "nova.db"
    monkeypatch.setattr(_connection, "DB_PATH", db_path)
    init_db()
    with _connection.connect() as con:
        migrate_work_schema(con)
        migrate_work_schema(con)
        verify_work_table_governance(con)
