# ADR 0004 — Memory is the only storage owner

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0003](0003-brain-is-the-only-claude-client.md),
  [0005](0005-mutationevent-as-atomic-state-change.md),
  [0012](0012-sqlite-as-system-of-record.md),
  [0013](0013-lancedb-as-vector-index.md),
  [0014](0014-property-graph-in-sqlite.md)

## Context

Nova has many producers of durable state: Finance logs money and tasks, Wellness
logs habits, Knowledge logs journal entries, Brain writes conversation turns,
Vision writes OCR text, the Graph writes entities and edges, Learning writes
insights. If each producer opened the database (or a second store) directly, the
schema would be owned by no one, transactional guarantees would be
per-caller, migrations would be un-coordinated, and a second storage engine
(vectors, graph) would tempt each new capability to bring its own store.

## Decision

**`nova.core.memory` is the single owner of all persistence — structured *and*
vector *and* graph.** Domains and services decide *what* to persist; Memory
decides *how* it is stored and executes every read and write through its public
API (`add_task()`, `add_money()`, `remember()`, `recall()`, `create_entity()`,
`link_entities()`, …). No other package opens `nova.db`, opens a LanceDB
connection, or manages schema.

New storage capabilities slot *inside* Memory rather than becoming new
storage-owning services: semantic memory is `memory/semantic/`, the knowledge
graph is `memory/graph/` — both re-exported through Memory's public API. LanceDB
does not become a second "owns-its-own-storage" service; it is a derived index
that lives inside Memory ([0013](0013-lancedb-as-vector-index.md)).

## Alternatives Considered

1. **Each domain owns its own tables/DB** — Finance opens its ledger, Wellness
   opens its habit store, etc.
2. **A separate vector service and a separate graph service**, each owning its
   own engine alongside Memory.
3. **A shared DB-access helper** importable by all, with schema conventions but
   no single owner.

## Consequences

- One schema owner, one migration path, one place transactions and integrity
  live. A write is a single call through a stable verb.
- Storage engines are swappable behind Memory's API: SQLite, LanceDB, and the
  graph tables are implementation details callers never see.
- The `MutationEvent` invariant ([0005](0005-mutationevent-as-atomic-state-change.md))
  is enforceable because every write funnels through Memory.
- Memory becomes a widely depended-upon package; it must keep its public API
  stable and never leak SQL/vector specifics upward
  ([0024](0024-stable-contracts-flexible-internals.md)).

## Why Alternatives Were Rejected

- **Per-domain storage** destroys the single-owner property: no coordinated
  migrations, no shared integrity, and cross-cutting features (semantic recall
  over *all* memories, a graph spanning all entities) become impossible without
  reaching across domain-owned stores. Rejected as the erosion path.
- **Separate vector/graph services** was explicitly rejected: a graph service
  would own persistence (forbidden) yet not be allowed to reason (forbidden),
  making it an empty pass-through — so the graph became `memory/graph/`. Vectors
  are a *derived, rebuildable* index of the SQLite ledger, which is definitionally
  Memory's job, not a peer store's.
- **A shared DB helper** provides convention without ownership; anyone can still
  write anywhere, so the invariant is unenforceable. Same failure as the
  llm-utils alternative in [0003](0003-brain-is-the-only-claude-client.md).

## Future Evolution

- A new storage engine (a different vector store, a time-series store) is added
  *inside* Memory behind its public API, exactly as LanceDB and the graph were.
- The rebuildability test is the guardrail for any future store: if it cannot be
  regenerated from the SQLite ledger, it is a new source of truth and needs its
  own ADR before it is allowed in.
