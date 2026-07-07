"""WorkOS schema migrations — idempotent upgrades for memory/schema.py.

Phase 0 reserves governance constants and owner_id on every future work_* table.
Per-gate DDL blocks are added in later phases (WOS-1 onward).
"""

from __future__ import annotations

import re

# ADR 0022/0023 — must never appear as live authoritative columns.
FORBIDDEN_DERIVED_COLUMNS: frozenset[str] = frozenset(
    {
        "allocation_pct",
        "completion_pct",
        "follow_through_rate",
        "health_band",
        "health_score",
        "health_status",
        "momentum",
        "portfolio_verdict",
        "priority_rank",
        "priority_score",
        "roi_hour",
        "roi_value",
        "velocity",
    },
)

# Reserved on every work_* CREATE TABLE from WOS-1 onward (ADR 0021).
OWNER_ID_COLUMN = "owner_id INTEGER"

_CREATE_TABLE_RE = re.compile(
    r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<name>work_\w+)",
    re.IGNORECASE,
)


def migrate_work_schema(con) -> None:
    """WorkOS schema entry point — idempotent, safe on fresh and upgraded DBs."""
    verify_work_table_governance(con)


def verify_work_table_governance(con) -> None:
    """Assert owner_id and no forbidden columns on every live work_* table."""
    tables = {
        row[0]
        for row in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'work_%'",
        ).fetchall()
    }
    for table in sorted(tables):
        columns = {row[1] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
        missing = FORBIDDEN_DERIVED_COLUMNS & columns
        if missing:
            raise RuntimeError(f"{table} has forbidden derived columns: {sorted(missing)}")
        if "owner_id" not in columns:
            raise RuntimeError(f"{table} is missing required owner_id column")


def assert_migration_source_governance(source: str) -> None:
    """Static audit of migration DDL text before tables ship."""
    for match in _CREATE_TABLE_RE.finditer(source):
        table_name = match.group("name")
        start = match.start()
        end = source.find(");", start)
        if end == -1:
            raise RuntimeError(f"Unclosed CREATE TABLE for {table_name}")
        block = source[start:end]
        block_lower = block.lower()
        if "owner_id" not in block_lower:
            raise RuntimeError(f"{table_name} DDL must reserve owner_id")
        for column in FORBIDDEN_DERIVED_COLUMNS:
            if re.search(rf"\b{re.escape(column)}\b", block_lower):
                raise RuntimeError(f"{table_name} DDL must not define derived column {column}")
