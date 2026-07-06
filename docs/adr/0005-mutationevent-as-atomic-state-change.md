# ADR 0005 — MutationEvent as the atomic unit of state change

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0004](0004-memory-is-the-only-storage-owner.md),
  [0006](0006-event-driven-single-process-runtime.md),
  [0015](0015-explainable-decision-making.md),
  [0021](0021-read-only-api-philosophy.md)

## Context

Nova changes state as a side effect of conversation: the user says something,
Brain picks a tool, the tool performs a domain operation, and *something durable
happens* (a task is created, money is logged, a habit is recorded). The system
needs a single, uniform way to represent "a business fact just changed" so that
persistence, semantic-memory production, live UI push, and audit all hang off the
same object rather than each domain inventing its own change-notification shape.

Without this, every downstream concern (what to persist, what to embed into
memory, what to push over WebSocket, what to log for audit) would be wired
per-domain and drift apart.

## Decision

Every successful domain operation produces a **`MutationEvent`** — an
**immutable, frozen record of one successful business mutation** — and all
persistence and propagation is driven by these events.

Two invariants are cardinal and tested:

1. **No mutation without an event.** Every successful domain write produces a
   `MutationEvent`.
2. **No event without a mutation.** A `MutationEvent` is only created for a
   completed domain operation — never speculatively.

Events are frozen dataclasses (`event_type`, `entity_type`, `operation`,
`entity`, …), built fresh per turn by `tool_calls_to_mutations()`, finalized by
`finalize_mutations()`, published to WebSocket subscribers before memory writes
complete, then fed to deterministic memory producers. Read-only tools produce no
event.

## Alternatives Considered

1. **Direct writes, no event object** — tools call Memory and each separately
   notifies whoever needs to know.
2. **Mutable event objects** updated as they flow through the pipeline.
3. **A full event-sourcing store** where events are the primary persistence and
   state is a projection.

## Consequences

- One atomic unit of state change underpins persistence, memory production, live
  push, and audit — added concerns hang off `MutationEvent`, not off each domain.
- Immutability makes the flow reason-about-able: an event's fields never change
  after creation, so subscribers and producers see a stable fact.
- The event stream is a natural audit and explainability substrate
  ([0015](0015-explainable-decision-making.md)) — *what changed and why* is
  recorded structurally, not reconstructed from logs.
- Every domain must route writes through the event path; a raw write that skips
  the event is a bug the invariant tests catch.

## Why Alternatives Were Rejected

- **Direct writes with no event** re-scatter change-notification across domains,
  the same erosion these invariants exist to prevent, and leave no uniform audit
  substrate.
- **Mutable events** defeat the point: if fields change mid-flight, subscribers
  race the mutation and the "immutable record of what happened" guarantee is
  gone. Immutability is the property that makes the event trustworthy.
- **Full event sourcing** was rejected as over-engineering at personal scale:
  SQLite tables are the system of record ([0012](0012-sqlite-as-system-of-record.md))
  and are simple to query directly. `MutationEvent` gives the *propagation and
  audit* benefits of events without paying the projection-rebuild complexity of
  making events the source of truth.

## Future Evolution

- If a durable event log is ever wanted (replay, richer audit, analytics), the
  `MutationEvent` is already the right shape to persist — it becomes an
  append-only table alongside the ledger, additively, without changing producers.
- New propagation concerns (a new UI channel, a new memory producer) subscribe to
  the existing event flow; they never require a new change-notification mechanism.
