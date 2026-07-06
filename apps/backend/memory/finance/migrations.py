"""Finance schema migrations — idempotent upgrades for memory/schema.py."""

from __future__ import annotations


def migrate_finance_indexes(con) -> None:
    """Finance indexes — idempotent, safe on fresh and upgraded databases."""
    con.executescript("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_live_name
            ON accounts(name COLLATE NOCASE) WHERE archived_at IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_finance_categories_name
            ON finance_categories(name COLLATE NOCASE) WHERE deleted_at IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_finance_merchants_name
            ON finance_merchants(name COLLATE NOCASE) WHERE deleted_at IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_legacy_money
            ON transactions(legacy_money_id) WHERE legacy_money_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_transactions_account_occurred
            ON transactions(account_id, occurred_on DESC, id DESC)
            WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_transactions_occurred
            ON transactions(occurred_on) WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_transactions_transfer_group
            ON transactions(transfer_group_id) WHERE transfer_group_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_statements_account_due
            ON statements(account_id, due_date) WHERE deleted_at IS NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_statements_account_period
            ON statements(account_id, period_start) WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_transactions_statement
            ON transactions(statement_id) WHERE statement_id IS NOT NULL;
        CREATE UNIQUE INDEX IF NOT EXISTS idx_reward_programs_account_name
            ON reward_programs(account_id, name COLLATE NOCASE)
            WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_reward_events_program_occurred
            ON reward_events(program_id, occurred_on)
            WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_cashback_rules_program
            ON cashback_rules(program_id)
            WHERE deleted_at IS NULL;
    """)


def migrate_finance_cashback(con) -> None:
    """Idempotent upgrade for cashback rule table."""
    tables = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    if "cashback_rules" not in tables:
        con.executescript("""
            CREATE TABLE cashback_rules (
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


def migrate_finance_rewards(con) -> None:
    """Idempotent upgrade for reward program and event tables."""
    tables = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    if "reward_programs" not in tables:
        con.executescript("""
            CREATE TABLE reward_programs (
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
        """)
    if "reward_events" not in tables:
        con.executescript("""
            CREATE TABLE reward_events (
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
        """)


def migrate_finance_credit_cards(con) -> None:
    """Idempotent upgrade for credit-card tables and account type widening."""
    tables = {
        row[0]
        for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    if "card_profiles" not in tables:
        con.executescript("""
            CREATE TABLE card_profiles (
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
        """)
    if "statements" not in tables:
        con.executescript("""
            CREATE TABLE statements (
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
        """)
    txn_cols = {row[1] for row in con.execute("PRAGMA table_info(transactions)").fetchall()}
    if "statement_id" not in txn_cols:
        con.execute(
            "ALTER TABLE transactions ADD COLUMN statement_id INTEGER REFERENCES statements(id)"
        )
    _migrate_accounts_type_credit_card(con)
    _migrate_transactions_card_payment_kind(con)


def _migrate_transactions_card_payment_kind(con) -> None:
    """Widen transactions.kind CHECK to allow card_payment on upgraded databases."""
    row = con.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='transactions'",
    ).fetchone()
    if row is None:
        return
    create_sql = row[0] or ""
    if "card_payment" in create_sql:
        return
    con.executescript("""
        CREATE TABLE transactions_new (
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
        INSERT INTO transactions_new
        SELECT id, account_id, direction, kind, amount_minor,
               category_id, merchant_id, note, occurred_on,
               transfer_group_id, statement_id, source, legacy_money_id,
               created_at, updated_at, deleted_at
        FROM transactions;
        DROP TABLE transactions;
        ALTER TABLE transactions_new RENAME TO transactions;
    """)
    con.executescript("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_transactions_legacy_money
            ON transactions(legacy_money_id) WHERE legacy_money_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_transactions_account_occurred
            ON transactions(account_id, occurred_on DESC, id DESC)
            WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_transactions_occurred
            ON transactions(occurred_on) WHERE deleted_at IS NULL;
        CREATE INDEX IF NOT EXISTS idx_transactions_transfer_group
            ON transactions(transfer_group_id) WHERE transfer_group_id IS NOT NULL;
        CREATE INDEX IF NOT EXISTS idx_transactions_statement
            ON transactions(statement_id) WHERE statement_id IS NOT NULL;
    """)


def _migrate_accounts_type_credit_card(con) -> None:
    """Widen accounts.type CHECK to allow credit_card on upgraded databases."""
    row = con.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='accounts'",
    ).fetchone()
    if row is None:
        return
    create_sql = row[0] or ""
    if "credit_card" in create_sql:
        return
    con.executescript("""
        CREATE TABLE accounts_new (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            name                  TEXT    NOT NULL,
            type                  TEXT    NOT NULL CHECK (type IN ('cash','bank','wallet','credit_card')),
            classification        TEXT    NOT NULL DEFAULT 'asset'
                                  CHECK (classification IN ('asset','liability')),
            currency              TEXT    NOT NULL DEFAULT 'INR',
            opening_balance_minor INTEGER NOT NULL DEFAULT 0,
            opening_balance_on    TEXT    NOT NULL,
            archived_at           TEXT,
            created_at            TEXT    NOT NULL,
            updated_at            TEXT    NOT NULL
        );
        INSERT INTO accounts_new
        SELECT id, name, type, classification, currency,
               opening_balance_minor, opening_balance_on,
               archived_at, created_at, updated_at
        FROM accounts;
        DROP TABLE accounts;
        ALTER TABLE accounts_new RENAME TO accounts;
    """)
    con.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_accounts_live_name
            ON accounts(name COLLATE NOCASE) WHERE archived_at IS NULL
    """)
