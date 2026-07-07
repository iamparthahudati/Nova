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

# WOS-1 Commitment ledger + Capture (WORKOS_PHASE1_SCHEMA §3). Tables are created
# in FK dependency order inside one executescript block so sqlite validates every
# REFERENCES clause once all five tables exist. No derived columns, owner_id on
# every table (ADR 0021/0023).
_PHASE1_DDL = """
CREATE TABLE IF NOT EXISTS work_notes (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id                INTEGER NOT NULL DEFAULT 1,
    body                    TEXT    NOT NULL,
    capture_source          TEXT    NOT NULL
                            CHECK (capture_source IN ('manual','chat','voice')),
    captured_on             TEXT    NOT NULL,
    status                  TEXT    NOT NULL DEFAULT 'captured'
                            CHECK (status IN ('captured','triaged','archived')),
    outcome_kind            TEXT
                            CHECK (outcome_kind IS NULL OR outcome_kind IN ('work_item','note','dismissed')),
    outcome_id              INTEGER,
    capture_idempotency_key TEXT,
    source                  TEXT    NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at              TEXT    NOT NULL,
    updated_at              TEXT    NOT NULL,
    deleted_at              TEXT
);

CREATE TABLE IF NOT EXISTS work_projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id            INTEGER NOT NULL DEFAULT 1,
    name                TEXT    NOT NULL,
    objective           TEXT,
    status              TEXT    NOT NULL DEFAULT 'idea'
                        CHECK (status IN ('idea','planned','active','paused','completed')),
    planned_start_on    TEXT,
    planned_end_on      TEXT,
    release_id          INTEGER,
    engagement_id       INTEGER,
    source              TEXT    NOT NULL DEFAULT 'manual'
                        CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL,
    archived_at         TEXT
);

CREATE TABLE IF NOT EXISTS work_items (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id                INTEGER NOT NULL DEFAULT 1,
    project_id              INTEGER NOT NULL REFERENCES work_projects(id),
    parent_id               INTEGER REFERENCES work_items(id),
    type                    TEXT    NOT NULL DEFAULT 'task'
                            CHECK (type IN ('epic','story','task','subtask')),
    title                   TEXT    NOT NULL,
    status                  TEXT    NOT NULL DEFAULT 'backlog'
                            CHECK (status IN ('backlog','todo','in_progress','in_review','done','cancelled')),
    estimate_minutes        INTEGER CHECK (estimate_minutes IS NULL OR estimate_minutes > 0),
    estimate_confidence     TEXT    CHECK (estimate_confidence IS NULL OR estimate_confidence IN ('low','medium','high')),
    deadline_on             TEXT,
    deadline_hardness       TEXT    CHECK (deadline_hardness IS NULL OR deadline_hardness IN ('hard','soft')),
    action_item_id          INTEGER REFERENCES work_action_items(id),
    source                  TEXT    NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at              TEXT    NOT NULL,
    updated_at              TEXT    NOT NULL,
    deleted_at              TEXT
);

CREATE TABLE IF NOT EXISTS work_action_items (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id                INTEGER NOT NULL DEFAULT 1,
    title                   TEXT    NOT NULL,
    status                  TEXT    NOT NULL DEFAULT 'open'
                            CHECK (status IN ('open','promoted','dismissed')),
    note_id                 INTEGER REFERENCES work_notes(id),
    promoted_work_item_id   INTEGER REFERENCES work_items(id),
    source                  TEXT    NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at              TEXT    NOT NULL,
    updated_at              TEXT    NOT NULL,
    deleted_at              TEXT
);

CREATE TABLE IF NOT EXISTS work_priority_policies (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id            INTEGER NOT NULL DEFAULT 1,
    deadline_weight     INTEGER NOT NULL DEFAULT 1000 CHECK (deadline_weight >= 0),
    decay_weight        INTEGER NOT NULL DEFAULT 100  CHECK (decay_weight >= 0),
    is_active           INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    source              TEXT    NOT NULL DEFAULT 'manual'
                        CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL
);
"""

_PHASE1_INDEXES = """
CREATE INDEX IF NOT EXISTS idx_work_notes_inbox
    ON work_notes(owner_id, captured_on DESC, id DESC)
    WHERE status = 'captured' AND deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_notes_idempotency
    ON work_notes(owner_id, capture_idempotency_key)
    WHERE capture_idempotency_key IS NOT NULL AND deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_work_action_items_open
    ON work_action_items(owner_id, created_at DESC)
    WHERE status = 'open' AND deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_action_items_promoted_target
    ON work_action_items(promoted_work_item_id)
    WHERE promoted_work_item_id IS NOT NULL AND deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_work_projects_live_name
    ON work_projects(owner_id, name COLLATE NOCASE)
    WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_work_projects_active
    ON work_projects(owner_id, status)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_work_items_project_live
    ON work_items(owner_id, project_id, status)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_work_items_deadline
    ON work_items(owner_id, deadline_on)
    WHERE deleted_at IS NULL AND deadline_on IS NOT NULL
      AND status NOT IN ('done','cancelled');
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_items_action_item_origin
    ON work_items(action_item_id)
    WHERE action_item_id IS NOT NULL AND deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_work_priority_policies_active_owner
    ON work_priority_policies(owner_id)
    WHERE is_active = 1;
"""


def migrate_work_schema(con) -> None:
    """WorkOS schema entry point — idempotent, safe on fresh and upgraded DBs."""
    migrate_work_phase1(con)
    verify_work_table_governance(con)


def migrate_work_phase1(con) -> None:
    """WOS-1 Commitment ledger + Capture tables, indexes, and default policy.

    Idempotent: every DDL statement is IF NOT EXISTS and the policy seed only
    writes when no active policy exists. Forward-only — no DROP (ADR 0012).
    """
    con.executescript(_PHASE1_DDL)
    con.executescript(_PHASE1_INDEXES)
    from .seed import ensure_default_priority_policy

    ensure_default_priority_policy(con)
    # Flush the seed INSERT so the shared init_db connection holds no open write
    # lock when later steps (e.g. finance seed) open their own connection.
    con.commit()


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
