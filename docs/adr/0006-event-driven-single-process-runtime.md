# ADR 0006 — Event-driven single-process runtime

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0001](0001-local-first-architecture.md),
  [0005](0005-mutationevent-as-atomic-state-change.md),
  [0007](0007-composition-root-owns-all-wiring.md)

## Context

Nova runs on one person's machine, serving one user, one conversation at a time.
Its workload is a sequence of conversation turns (2–10 s each, dominated by the
reasoning call) plus low-frequency background jobs (nightly memory maintenance,
weekly reflection). It is not a multi-tenant server and has no concurrency
requirement beyond "don't block the turn on slow I/O that can be deferred."

The question is how much runtime machinery this deserves: a full async
event-loop framework, a message broker and worker pool, or something smaller.

## Decision

Nova Core is a **single-process, event-driven runtime**. All user interaction
flows through **one synchronous conversation pipeline**: route to Brain →
execute tools → build `MutationEvent`s → persist → fire async cleanup jobs. The
"event-driven" quality is `MutationEvent` propagation
([0005](0005-mutationevent-as-atomic-state-change.md)), not an external event
loop or broker.

The lifecycle is five explicit phases — Cold Boot, Model Load, Memory Init,
Context Init, Ready — after which the run loop ticks. Background cadence (memory
maintenance, reflection, agent jobs) is handled by an in-process timestamp-gate
registry checked on each tick (generalizing `should_run_reflection()`), **not**
by cron, Celery, or any external scheduler. The composition root's run loop gains
at most a single call per background subsystem (e.g. `agents.run_due_jobs()`).

## Alternatives Considered

1. **Fully async runtime** (asyncio everywhere) for concurrency.
2. **Multi-process / worker + broker** (Celery, a task queue) for background
   jobs.
3. **Threaded server model** with a request pool.

## Consequences

- The mental model is small: one process, one synchronous turn, explicit phases.
  This is debuggable at 2 a.m. and matches the Handbook's "boring code wins".
- No broker, scheduler, or worker infrastructure to deploy or operate —
  consistent with local-first ([0001](0001-local-first-architecture.md)).
- Slow synchronous steps (Whisper transcription) block the main thread by design;
  genuinely deferrable work (LanceDB compaction, extraction sweeps) runs on
  bounded background threads fired from the composition root.
- The single-process assumption is load-bearing: profile is read-only during the
  run loop, and background jobs must not race foreground writes — a constraint
  that must hold for any future background work.

## Why Alternatives Were Rejected

- **Fully async** buys concurrency the single-user workload never needs, at the
  cost of async's well-known debugging and reasoning tax on every code path.
  Rejected as complexity without benefit.
- **Broker + workers** is server-scale infrastructure for six low-frequency jobs;
  the timestamp-gate registry does the same job in a few lines with no new
  process to run. Rejected as needless infrastructure for personal scale.
- **Threaded server** implies multi-request concurrency and shared-state locking
  that a one-user, one-turn-at-a-time tool does not have. Rejected.

## Future Evolution

- If write latency ever becomes a real problem (e.g. synchronous embedding at
  write time), the *one* sanctioned place a background queue would appear is
  behind Memory's write path — not a reason to introduce a broker across the
  system.
- If Nova ever needs to serve concurrent clients, that is a different product and
  a superseding ADR, not an incremental relaxation of the single-process rule.
