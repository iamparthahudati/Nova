# ADR 0017 — Finance as the first domain

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0011](0011-domain-isolation.md),
  [0004](0004-memory-is-the-only-storage-owner.md),
  [0005](0005-mutationevent-as-atomic-state-change.md),
  [0009](0009-layered-package-taxonomy.md)

## Context

A layered architecture with strict domain isolation is only proven once a *real*
domain is built through the whole pipeline: Electron → React → API → FastAPI →
Memory → `MutationEvent` → `finalize_mutations()`. The first domain built in
earnest sets the pattern every later domain (Wellness, Productivity, …) copies —
its entity design, its mutation vocabulary, its tool contracts, and its handling
of update/delete become the template. Choosing which capability goes first is
therefore a high-leverage decision, not just a scheduling one.

## Decision

**Finance is Nova's first fully-built domain** — money, tasks, and products, and
the spending/accounts model that grows from them. Finance was chosen to go first
because it exercises the hardest, most representative demands early:

- **Exact arithmetic** (balances, utilization, EMI) forces the money model to be
  correct, not merely loggable — surfacing that REAL floats are wrong for
  balances and that domain date (`occurred_at`) must be separated from audit date
  (`created_at`).
- **Update and delete** land here first ("Finance will be the first domain to
  need it, so it sets the pattern") — every later domain inherits that pattern.
- **A rich entity vocabulary** (accounts, transactions, categories, merchants)
  stress-tests the `entity_type`/`operation` mutation model against a real,
  growing schema rather than a toy one.

Finance obeys every boundary rule: it persists only through Memory's public API,
never opens the database, never calls another domain, and reaches Calendar only
via an injected tool handler — proving the isolation rules
([0011](0011-domain-isolation.md)) on a demanding case.

## Alternatives Considered

1. **Wellness (habits) first** — the simplest domain.
2. **Productivity (tasks/planning) first.**
3. **A deliberately trivial "toy" domain** purely to prove the pipeline.

## Consequences

- The pipeline and the boundary rules are validated on a *demanding* domain, so
  patterns later domains copy are battle-tested (money correctness, update/delete,
  date separation, growable vocabulary).
- Finance becomes the reference implementation of the domain contract; its shape
  is the template, so getting it right pays forward.
- Finance carries more inherent complexity than a first domain strictly needed —
  accepted, because that complexity is exactly what shakes out the pipeline's
  weak points early rather than late.

## Why Alternatives Were Rejected

- **Wellness first** is too simple to stress the model: habits need neither exact
  arithmetic, nor update/delete, nor a rich entity vocabulary. It would "prove"
  the pipeline against a case that hides the real design questions until a harder
  domain arrives — the worst time to discover them.
- **Productivity first** overlaps heavily with Planner logic already present and
  would not force the financial-grade correctness (exact sums, transfers,
  refunds) that most rigorously tests the mutation and persistence model.
- **A toy domain** proves wiring but not design; the patterns it sets would have
  to be redone the moment a real domain needed exactness and mutation — negative
  value.

## Future Evolution

- New domains follow Finance's established pattern (entities, mutations, tools,
  persistence via Memory, update/delete semantics) — they add packages without
  modifying Finance or the core ([0009](0009-layered-package-taxonomy.md)).
- Finance's own out-of-scope items (bank/UPI sync, receipt OCR, auto-import) are
  deferred by design — all data enters by hand, chat, or voice in v1.0 — and any
  later integration is additive behind the same domain boundary.
