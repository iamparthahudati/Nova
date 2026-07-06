# ADR 0013 — LanceDB as the vector index

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0004](0004-memory-is-the-only-storage-owner.md),
  [0012](0012-sqlite-as-system-of-record.md),
  [0002](0002-tiered-three-model-ai-architecture.md)

## Context

Semantic memory needs approximate-nearest-neighbour (ANN) search over embedding
vectors so that Nova can "recall what's relevant to *this* turn" instead of
always dumping the most recent rows. SQLite is the system of record
([0012](0012-sqlite-as-system-of-record.md)) but is not a vector search engine.
The vector store must be local-first (no server), must embed cleanly *inside*
Memory rather than becoming a second storage-owning service
([0004](0004-memory-is-the-only-storage-owner.md)), and must not become a second
source of truth.

## Decision

**LanceDB is the vector index**, living inside `memory/semantic/` and owned by
Memory. It holds one table keyed by the same UUID as the SQLite `memories`
ledger, storing the embedding vector plus a denormalized copy of the searchable
payload (text + minimal metadata) so a result can be rendered without a
round-trip to SQLite on the hot path.

LanceDB is explicitly a **derived, rebuildable index, never the source of
truth**: if it were deleted entirely, it could be fully rebuilt by re-embedding
every row in the `memories` ledger. That rebuildability is the acceptance test
for what belongs in it. `recall()` runs ANN in LanceDB for a candidate set, then
joins each candidate back to its SQLite row for tier/importance/access and
`deleted_at IS NULL` filtering — so SQLite remains authoritative for correctness
and lifecycle.

## Alternatives Considered

1. **A dedicated vector database server** (e.g. a hosted or self-hosted vector
   service).
2. **A SQLite vector extension** (e.g. `sqlite-vss`/`sqlite-vec`) to keep
   everything in one file.
3. **In-process brute-force** cosine search over vectors held in memory / a blob
   column.

## Consequences

- Embedded, local-first ANN with no server to run — consistent with
  [0001](0001-local-first-architecture.md).
- Clean two-store split: SQLite owns existence/lifecycle/transactions; LanceDB
  owns the vector + hot-path payload. Deletion is two-phase (immediate SQLite
  soft-delete for correctness; batched LanceDB compaction nightly).
- A temporary storage cost between soft-delete and compaction (orphaned but
  unreachable vectors) — accepted, since recall always filters via SQLite.
- One more engine inside Memory to manage (compaction, schema), but behind
  Memory's public API and invisible to callers.

## Why Alternatives Were Rejected

- **A dedicated vector DB server** reintroduces a daemon and operational weight
  that local-first forbids, for personal-scale vector counts that do not need it.
- **A SQLite vector extension** was a reasonable contender (single file), but was
  not chosen for v1.0: it ties vector search to a native extension's build/ABI on
  every platform and, at the time of the decision, offered weaker ANN indexing
  than a purpose-built embedded columnar store. This is the closest-run
  alternative and the most likely future revisit (see below).
- **Brute-force in-memory search** does not scale as the corpus grows over years
  and puts the whole vector set in RSS; the memory-usage discipline
  (bounded steady-state RSS) rules it out as a permanent design.

## Future Evolution

- Because LanceDB is a *derived index behind Memory*, swapping it (for a SQLite
  vector extension once mature, or another embedded store) is a Memory-internal
  change requiring only a re-embed/rebuild — callers are untouched. The
  rebuildability property is exactly what makes this swap cheap.
- If write-time embedding latency ever bites, a background embedding queue behind
  Memory's write path is the sanctioned place to add it
  ([0006](0006-event-driven-single-process-runtime.md)), not a redesign of the
  index boundary.
