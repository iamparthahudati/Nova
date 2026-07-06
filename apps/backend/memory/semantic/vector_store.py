"""LanceDB wrapper — the only file in Memory that imports lancedb.

LanceDB is a derived index, not a source of truth: everything stored here
(text, source_type, created_at) is a denormalized copy of columns that also
live in the `memories` SQLite table (see ledger.py). If this table is lost
or dropped, `service.rebuild_index()` recreates it byte-for-equivalent from
SQLite. Nothing outside this file ever imports `lancedb` directly.
"""

from pathlib import Path

import pyarrow as pa

from .. import _connection

_TABLE_NAME = "memories"
LANCEDB_PATH = _connection.LANCEDB_PATH


def _schema(dimensions: int) -> pa.Schema:
    return pa.schema([
        pa.field("id", pa.string()),
        pa.field("vector", pa.list_(pa.float32(), dimensions)),
        pa.field("text", pa.string()),
        pa.field("source_type", pa.string()),
        pa.field("created_at", pa.string()),
    ])


class VectorStore:
    """One LanceDB table, keyed by the same memory id used in SQLite."""

    def __init__(self, dimensions: int, path: Path | None = None) -> None:
        self._dimensions = dimensions
        # Resolved at call time, not import time, so tests can point this at
        # an isolated directory by monkeypatching the module-level constant.
        self._path = path if path is not None else LANCEDB_PATH
        self._db = None
        self._table = None

    def _connect(self):
        if self._db is None:
            import lancedb

            self._path.mkdir(parents=True, exist_ok=True)
            self._db = lancedb.connect(str(self._path))
        return self._db

    def _ensure_table(self):
        if self._table is not None:
            return self._table
        db = self._connect()
        # exist_ok makes create-or-open a single atomic call. Never gate this on
        # list_tables(): its return type has changed across lancedb releases
        # (list[str] → ListTablesResponse), which made `name in db.list_tables()`
        # silently False and every recall/remember die on "already exists".
        self._table = db.create_table(
            _TABLE_NAME, schema=_schema(self._dimensions), exist_ok=True
        )
        return self._table

    def add(self, rows: list[dict]) -> None:
        """Each row: {id, vector, text, source_type, created_at}."""
        if not rows:
            return
        self._ensure_table().add(rows)

    def search(self, vector: list[float], k: int, source_type: str | None = None) -> list[dict]:
        table = self._ensure_table()
        query = table.search(vector).limit(k)
        if source_type is not None:
            escaped = source_type.replace("'", "''")
            query = query.where(f"source_type = '{escaped}'", prefilter=True)
        hits = query.to_list()
        return [
            {
                "id": h["id"],
                "text": h["text"],
                "source_type": h["source_type"],
                "created_at": h["created_at"],
                "score": h["_distance"],
            }
            for h in hits
        ]

    def delete(self, ids: list[str]) -> None:
        """Remove specific vectors by id — the compaction half of a hard purge.

        Soft delete never calls this (the vector stays orphaned-but-unreachable
        until then, per §2); only maintenance, after SQLite rows are gone, drops
        the matching vectors here so the index doesn't accrete dead rows.
        """
        if not ids:
            return
        table = self._ensure_table()
        quoted = ",".join("'" + i.replace("'", "''") + "'" for i in ids)
        table.delete(f"id IN ({quoted})")

    def drop(self) -> None:
        db = self._connect()
        db.drop_table(_TABLE_NAME, ignore_missing=True)
        self._table = None

    def rebuild(self, rows: list[dict]) -> int:
        """Recreate the table from scratch, then bulk-insert. Returns rows written.

        Uses create_table(mode="overwrite") rather than drop()+create(): overwrite
        is atomic, whereas a separate drop then create can race into a spurious
        "table already exists" on some LanceDB builds. This is the reindex path,
        so a clean single-step replace is exactly what we want.
        """
        db = self._connect()
        self._table = db.create_table(
            _TABLE_NAME, schema=_schema(self._dimensions), mode="overwrite"
        )
        if rows:
            self._table.add(rows)
        return len(rows)
