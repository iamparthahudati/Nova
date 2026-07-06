# ADR 0014 — Property graph in SQLite over a dedicated graph DB / RDF

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0012](0012-sqlite-as-system-of-record.md),
  [0004](0004-memory-is-the-only-storage-owner.md),
  [0011](0011-domain-isolation.md)

## Context

Nova models the nouns implicit in a user's life and how they connect: people,
projects, tasks, goals, habits, meetings, documents, conversations, products, and
relations like `person —WORKS_ON→ project` or `habit —SUPPORTS→ goal`. Brain uses
this to enrich context ("who else is on this project?"). The data model needed is
a **labeled property graph** — typed nodes with free-form attributes, typed
weighted edges with provenance — at personal scale (thousands of entities/edges),
where edges also reference `memories.id` for provenance.

## Decision

The knowledge graph is implemented as **two SQLite tables inside `nova.db`** —
`entities` and `edges` — under `memory/graph/`, owned by Memory and re-exported
through its public API (`create_entity`, `link_entities`, `related_entities`,
`entity_edges`, …). Traversal uses SQLite's recursive CTEs. There is **no
dedicated graph database and no RDF/triple store.**

This was a deliberate correction during implementation: a standalone
`services/graph` was considered and rejected because it would own persistence
(forbidden by [0004](0004-memory-is-the-only-storage-owner.md)) yet not be
allowed to reason (forbidden by [0003](0003-brain-is-the-only-claude-client.md)),
making it an empty pass-through. Since edges reference `memories.id` — an
intra-database relationship — the graph belongs with the tables' owner. The graph
is an *extension of Memory*, exactly like semantic memory.

## Alternatives Considered

1. **A dedicated graph engine** (Neo4j, Kuzu, etc.).
2. **An RDF / triple store** with SPARQL.
3. **A standalone `services/graph` package** owning its own store.

## Consequences

- Zero new infrastructure: the graph rides on the storage engine, backups,
  transactions, and migrations Nova already has ([0012](0012-sqlite-as-system-of-record.md)).
- Provenance is a foreign key (`edges → memories.id`) — a plain relational join,
  not a cross-store correlation.
- Population respects the boundaries: Brain (or a cheap local heuristic) extracts
  entities/relations and calls Memory's graph verbs; the graph never reasons and
  never calls Brain, keeping `brain → memory(graph)` acyclic.
- Traversal expressiveness is bounded by what recursive CTEs do well — fine for
  depth-1–2 neighbourhood queries at personal scale.

## Why Alternatives Were Rejected

- **A dedicated graph engine** is a new infrastructure dependency for a problem
  SQLite's recursive CTEs already solve at thousands-of-edges scale. Its value
  (billions of edges, deep traversal) addresses a scale Nova does not have.
- **RDF / triple stores** impose the open-world, URI-everything modeling and
  SPARQL toolchain — heavyweight semantics for what is a closed, personal,
  labeled-property graph. Wrong model, high ceremony.
- **A standalone graph service** is architecturally illegal here: it could
  neither own storage nor reason, so it would be an empty shim around Memory
  calls, and its edges' provenance links belong in the database that owns
  `memories`. Rejected in favor of `memory/graph/`.

## Future Evolution

- Revisit **only** on a concrete, observable trigger: traversal complexity or
  edge volume genuinely outgrowing what SQLite CTEs handle. That is a measured
  condition, not a hypothetical.
- If that trigger fires, the graph tables can be projected into a dedicated
  engine as a *derived* store behind Memory's existing graph API — the public
  verbs (`related_entities`, etc.) stay stable, so Brain and other readers are
  unaffected.
