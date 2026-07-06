# ADR 0012 — SQLite as the system of record

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0001](0001-local-first-architecture.md),
  [0004](0004-memory-is-the-only-storage-owner.md),
  [0013](0013-lancedb-as-vector-index.md),
  [0014](0014-property-graph-in-sqlite.md)

## Context

Nova needs durable, transactional storage for a single user's structured state:
tasks, money, products, habits, profile, conversation history, memory ledger,
and graph entities/edges. The scale is personal — thousands to low millions of
rows over years, one writer, no network — and the deployment is local-first
([0001](0001-local-first-architecture.md)): no server to run, no second machine,
no cloud.

## Decision

**SQLite (`nova.db`) is Nova's system of record** — the single, transactional,
on-device source of truth for all structured state, owned exclusively by Memory
([0004](0004-memory-is-the-only-storage-owner.md)). Everything that must be
correct, transactional, and authoritative lives here: entity existence and
lifecycle, the memory ledger, relationships, and the graph tables
([0014](0014-property-graph-in-sqlite.md)). Derived stores (the LanceDB vector
index) are rebuildable projections of it, never sources of truth.

Schema changes are additive/expand-only migrations owned by Memory. Tests use a
real temporary SQLite database, never a mock — the database is never mocked
([0022](0022-testing-philosophy.md)).

## Alternatives Considered

1. **A client/server RDBMS** (PostgreSQL, MySQL).
2. **An embedded document / key-value store** (e.g. a JSON store, LMDB).
3. **Flat files** (JSON/SQLite-less) for a "simple" personal tool.

## Consequences

- Zero operational footprint: an in-process library, one file, no daemon —
  exactly what local-first requires.
- Full ACID transactions back the `MutationEvent` persistence guarantees
  ([0005](0005-mutationevent-as-atomic-state-change.md)); a single UPDATE is the
  correctness-critical primitive (e.g. soft-delete visibility).
- Rich SQL — including recursive CTEs — is available, which is what makes an
  in-database property graph viable ([0014](0014-property-graph-in-sqlite.md))
  and avoids a separate graph engine.
- Single-writer and single-file are accepted limits; they match the single-user,
  single-process runtime ([0006](0006-event-driven-single-process-runtime.md)).

## Why Alternatives Were Rejected

- **A client/server RDBMS** requires running and securing a database daemon —
  operational weight with no benefit at single-user scale, and a violation of
  local-first's "no server" posture. Its concurrency and scale features solve
  problems Nova does not have.
- **A document/KV store** gives up SQL, transactions across entities, and
  relational queries (joins, CTEs) that the memory ledger and graph depend on —
  Nova would end up re-implementing half a relational engine.
- **Flat files** cannot provide transactions, concurrent-safe writes, or
  queryability; a "simple" personal tool that logs finances still needs the money
  arithmetic to sum exactly and survive a crash mid-write.

## Future Evolution

- Because Memory owns all storage behind a public API, the engine *could* be
  swapped without touching callers — but the trigger would have to be a concrete,
  observed limit (write contention, dataset size) that SQLite genuinely cannot
  meet, which personal scale is not expected to reach.
- New structured state is a new table/migration inside Memory, additive, never a
  new store.
