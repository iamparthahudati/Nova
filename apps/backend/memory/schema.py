from . import _connection


def init_db() -> None:
    """Create nova.db and all tables if they don't already exist."""
    with _connection.connect() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                text       TEXT    NOT NULL,
                status     TEXT    NOT NULL DEFAULT 'open',
                created_at TEXT    NOT NULL,
                due        TEXT
            );

            CREATE TABLE IF NOT EXISTS money (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                type       TEXT    NOT NULL,
                amount     REAL    NOT NULL,
                note       TEXT,
                created_at TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS progress (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                area       TEXT,
                note       TEXT    NOT NULL,
                created_at TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                store      TEXT,
                status     TEXT    NOT NULL DEFAULT 'building',
                price      REAL,
                sold_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                text        TEXT    NOT NULL,
                remind_date TEXT    NOT NULL,
                remind_time TEXT,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS profile (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                observation TEXT    NOT NULL,
                category    TEXT    NOT NULL DEFAULT 'general',
                confidence  REAL    NOT NULL DEFAULT 0.7,
                updated_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS habits (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                logged_date TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            );

            -- Phase 2, Milestone 2.1/2.2: semantic memory ledger. Source of
            -- truth for every embedded memory; LanceDB (memory/semantic/) holds
            -- only a derived vector index rebuildable from this table.
            --
            -- 2.1 added the first seven columns. 2.2 added the lifecycle and
            -- embedding-provenance columns. 2.7 added the entity-extraction
            -- state pair (extracted-at stamp + attempt counter) that makes the
            -- graph-extraction sweep idempotent. Fresh installs get the full
            -- shape here; older installs are upgraded in place by
            -- _migrate_memories() (no data is ever dropped to migrate).
            CREATE TABLE IF NOT EXISTS memories (
                id                    TEXT    PRIMARY KEY,
                text                  TEXT    NOT NULL,
                source_type           TEXT    NOT NULL,
                source_id             TEXT,
                metadata              TEXT,
                content_hash          TEXT    NOT NULL DEFAULT '',
                tier                  TEXT    NOT NULL DEFAULT 'short_term',
                importance            REAL    NOT NULL DEFAULT 0.5,
                access_count          INTEGER NOT NULL DEFAULT 0,
                last_accessed_at      TEXT,
                supersedes_id         TEXT,
                deleted_at            TEXT,
                embedding_model       TEXT    NOT NULL,
                embedding_version     TEXT    NOT NULL DEFAULT '1',
                embedding_dimension   INTEGER NOT NULL DEFAULT 0,
                entities_extracted_at TEXT,
                extraction_attempts   INTEGER NOT NULL DEFAULT 0,
                created_at            TEXT    NOT NULL
            );

            -- Phase 2, Milestone 2.6: knowledge graph (memory/graph/). Two
            -- tables, nothing more — the graph is an extension of Memory, not
            -- a second database. REFERENCES clauses document intent; sqlite3
            -- doesn't enforce them without a per-connection pragma, so
            -- memory/graph/service.py enforces referential integrity itself
            -- (existence checks on link, edge cascade on entity delete).
            CREATE TABLE IF NOT EXISTS entities (
                id             TEXT PRIMARY KEY,
                type           TEXT NOT NULL,
                canonical_name TEXT NOT NULL,
                attributes     TEXT NOT NULL DEFAULT '{}',
                created_at     TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS edges (
                id               TEXT PRIMARY KEY,
                from_entity_id   TEXT NOT NULL REFERENCES entities(id),
                to_entity_id     TEXT NOT NULL REFERENCES entities(id),
                relation_type    TEXT NOT NULL,
                weight           REAL NOT NULL DEFAULT 1.0,
                source_memory_id TEXT REFERENCES memories(id),
                created_at       TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS accounts (
                id                    INTEGER PRIMARY KEY AUTOINCREMENT,
                name                  TEXT    NOT NULL,
                type                  TEXT    NOT NULL CHECK (type IN ('cash','bank','wallet','credit_card','loan','investment','other')),
                classification        TEXT    NOT NULL DEFAULT 'asset'
                                      CHECK (classification IN ('asset','liability')),
                currency              TEXT    NOT NULL DEFAULT 'INR',
                opening_balance_minor INTEGER NOT NULL DEFAULT 0,
                opening_balance_on    TEXT    NOT NULL,
                archived_at           TEXT,
                created_at            TEXT    NOT NULL,
                updated_at            TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS card_profiles (
                account_id            INTEGER PRIMARY KEY REFERENCES accounts(id),
                network               TEXT,
                last4                 TEXT,
                credit_limit_minor    INTEGER NOT NULL CHECK (credit_limit_minor > 0),
                statement_day         INTEGER NOT NULL CHECK (statement_day BETWEEN 1 AND 31),
                due_day_offset        INTEGER NOT NULL CHECK (due_day_offset > 0),
                autopay               INTEGER NOT NULL DEFAULT 0,
                created_at            TEXT    NOT NULL,
                updated_at            TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS statements (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id       INTEGER NOT NULL REFERENCES accounts(id),
                period_start     TEXT    NOT NULL,
                period_end       TEXT    NOT NULL,
                statement_date   TEXT    NOT NULL,
                due_date         TEXT    NOT NULL,
                total_due_minor  INTEGER,
                min_due_minor    INTEGER,
                created_at       TEXT    NOT NULL,
                updated_at       TEXT    NOT NULL,
                deleted_at       TEXT
            );

            CREATE TABLE IF NOT EXISTS finance_categories (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                created_at TEXT    NOT NULL,
                updated_at TEXT    NOT NULL,
                deleted_at TEXT
            );

            CREATE TABLE IF NOT EXISTS finance_merchants (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                created_at TEXT    NOT NULL,
                updated_at TEXT    NOT NULL,
                deleted_at TEXT
            );

            CREATE TABLE IF NOT EXISTS transactions (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id        INTEGER NOT NULL REFERENCES accounts(id),
                direction         TEXT    NOT NULL CHECK (direction IN ('debit','credit')),
                kind              TEXT    NOT NULL
                                  CHECK (kind IN ('expense','income','transfer','card_payment','adjustment')),
                amount_minor      INTEGER NOT NULL CHECK (amount_minor > 0),
                category_id       INTEGER REFERENCES finance_categories(id),
                merchant_id       INTEGER REFERENCES finance_merchants(id),
                note              TEXT,
                occurred_on       TEXT    NOT NULL,
                transfer_group_id TEXT,
                statement_id      INTEGER REFERENCES statements(id),
                source            TEXT    NOT NULL DEFAULT 'manual'
                                  CHECK (source IN ('manual','chat','voice','migrated_money')),
                legacy_money_id   INTEGER,
                created_at        TEXT    NOT NULL,
                updated_at        TEXT    NOT NULL,
                deleted_at        TEXT
            );

            CREATE TABLE IF NOT EXISTS reward_programs (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id       INTEGER NOT NULL REFERENCES accounts(id),
                name             TEXT    NOT NULL,
                unit             TEXT    NOT NULL
                                 CHECK (unit IN ('points','cashback_minor')),
                earn_rate_note   TEXT,
                expiry_note      TEXT,
                created_at       TEXT    NOT NULL,
                updated_at       TEXT    NOT NULL,
                deleted_at       TEXT
            );

            CREATE TABLE IF NOT EXISTS reward_events (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id       INTEGER NOT NULL REFERENCES reward_programs(id),
                kind             TEXT    NOT NULL
                                 CHECK (kind IN ('earned','redeemed','expired','adjusted')),
                direction        TEXT    NOT NULL CHECK (direction IN ('credit','debit')),
                amount           INTEGER NOT NULL CHECK (amount > 0),
                transaction_id   INTEGER REFERENCES transactions(id),
                note             TEXT,
                occurred_on      TEXT    NOT NULL,
                created_at       TEXT    NOT NULL,
                updated_at       TEXT    NOT NULL,
                deleted_at       TEXT
            );

            CREATE TABLE IF NOT EXISTS cashback_rules (
                id                         INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id                 INTEGER NOT NULL REFERENCES reward_programs(id),
                account_id                 INTEGER REFERENCES accounts(id),
                name                       TEXT    NOT NULL,
                flat_rate_bps              INTEGER NOT NULL DEFAULT 0
                                           CHECK (flat_rate_bps >= 0),
                category_multipliers         TEXT    NOT NULL DEFAULT '{}',
                merchant_multipliers         TEXT    NOT NULL DEFAULT '{}',
                excluded_category_ids      TEXT    NOT NULL DEFAULT '[]',
                excluded_merchant_ids      TEXT    NOT NULL DEFAULT '[]',
                excluded_mcc_codes         TEXT    NOT NULL DEFAULT '[]',
                excluded_transaction_kinds TEXT    NOT NULL DEFAULT '[]',
                monthly_cap_minor          INTEGER CHECK (monthly_cap_minor IS NULL OR monthly_cap_minor > 0),
                minimum_spend_minor        INTEGER NOT NULL DEFAULT 0
                                           CHECK (minimum_spend_minor >= 0),
                created_at                 TEXT    NOT NULL,
                updated_at                 TEXT    NOT NULL,
                deleted_at                 TEXT
            );
        """)
        # Bring a pre-2.2 `memories` table up to the shape above BEFORE indexing:
        # on such a database the CREATE above is a no-op (table already exists),
        # so the 2.2 columns don't exist yet and an index over them would fail.
        _migrate_memories(con)
        _migrate_reminders(con)
        from .finance.migrations import (
            migrate_finance_account_types,
            migrate_finance_cashback,
            migrate_finance_credit_cards,
            migrate_finance_indexes,
            migrate_finance_rewards,
        )

        migrate_finance_credit_cards(con)
        migrate_finance_account_types(con)
        migrate_finance_rewards(con)
        migrate_finance_cashback(con)

        # Dedup lookups (content_hash) and maintenance sweeps (tier, deleted_at)
        # are the hot query shapes; index them once the columns are guaranteed.
        con.executescript("""
            CREATE INDEX IF NOT EXISTS idx_memories_content_hash ON memories(content_hash);
            CREATE INDEX IF NOT EXISTS idx_memories_tier         ON memories(tier);
            CREATE INDEX IF NOT EXISTS idx_memories_deleted_at   ON memories(deleted_at);
            CREATE INDEX IF NOT EXISTS idx_memories_supersedes   ON memories(supersedes_id);

            -- The extraction sweep's hot query: oldest unprocessed live rows.
            -- Partial index so it stays tiny — once a memory is extracted (the
            -- steady state for every row) it leaves the index entirely.
            CREATE INDEX IF NOT EXISTS idx_memories_pending_extraction
                ON memories(created_at)
                WHERE entities_extracted_at IS NULL AND deleted_at IS NULL;

            -- Graph identity rules, enforced at the storage layer as the
            -- backstop for memory/graph/service.py's dedup: one entity per
            -- (type, name) ignoring case; one edge per (from, to, relation) —
            -- repetition reinforces edges.weight instead of adding rows.
            CREATE UNIQUE INDEX IF NOT EXISTS idx_entities_identity
                ON entities(type, canonical_name COLLATE NOCASE);
            CREATE UNIQUE INDEX IF NOT EXISTS idx_edges_identity
                ON edges(from_entity_id, to_entity_id, relation_type);
            -- Traversal fans out from both endpoints (undirected walk).
            CREATE INDEX IF NOT EXISTS idx_edges_from ON edges(from_entity_id);
            CREATE INDEX IF NOT EXISTS idx_edges_to   ON edges(to_entity_id);
        """)
        migrate_finance_indexes(con)

        from .work.migrations import migrate_work_schema

        migrate_work_schema(con)

        from .finance.seed import ensure_default_cash_account

        ensure_default_cash_account()


# Columns added after 2.1. Each entry is a full column definition that is
# ALTER-ADDed only if absent, so init_db() is safe to run against an older
# database without dropping the table or losing rows. 2.7's extraction-state
# pair rides the same mechanism: pre-2.7 rows get NULL/0, which correctly
# marks the entire existing history as pending its first extraction pass.
_MEMORIES_2_2_COLUMNS = [
    ("content_hash", "TEXT    NOT NULL DEFAULT ''"),
    ("tier", "TEXT    NOT NULL DEFAULT 'short_term'"),
    ("importance", "REAL    NOT NULL DEFAULT 0.5"),
    ("access_count", "INTEGER NOT NULL DEFAULT 0"),
    ("last_accessed_at", "TEXT"),
    ("supersedes_id", "TEXT"),
    ("deleted_at", "TEXT"),
    ("embedding_version", "TEXT    NOT NULL DEFAULT '1'"),
    ("embedding_dimension", "INTEGER NOT NULL DEFAULT 0"),
    ("entities_extracted_at", "TEXT"),  # 2.7
    ("extraction_attempts", "INTEGER NOT NULL DEFAULT 0"),  # 2.7
]


def _migrate_reminders(con) -> None:
    """Idempotently add `remind_time` to a `reminders` table created before
    timed reminders existed. NULL means a day-level reminder — exactly the
    behavior every pre-existing row had, so old data needs no rewrite.
    """
    existing = {row[1] for row in con.execute("PRAGMA table_info(reminders)").fetchall()}
    if "remind_time" not in existing:
        con.execute("ALTER TABLE reminders ADD COLUMN remind_time TEXT")


def _migrate_memories(con) -> None:
    """Idempotently bring a pre-2.2 `memories` table up to the 2.2 shape.

    Fresh databases already have every column from the CREATE above, so this is
    a no-op for them. Databases created under Milestone 2.1 are missing the
    lifecycle/embedding columns; we ALTER them in without touching existing rows
    — supersession and soft-delete are the project's deletion story, so schema
    migration must never drop data either.
    """
    existing = {row[1] for row in con.execute("PRAGMA table_info(memories)").fetchall()}
    for name, definition in _MEMORIES_2_2_COLUMNS:
        if name not in existing:
            con.execute(f"ALTER TABLE memories ADD COLUMN {name} {definition}")
