# ADR 0020 — FastAPI facade as the desktop boundary

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0019](0019-electron-desktop-separate-process.md),
  [0021](0021-read-only-api-philosophy.md),
  [0024](0024-stable-contracts-flexible-internals.md)

## Context

The desktop app is a separate process with no Python import path
([0019](0019-electron-desktop-separate-process.md)); it needs a network
interface to read Nova's state and receive live updates (voice transcript,
notifications, agent-job status). That interface must be a *thin* boundary over
the existing service/domain public APIs — if it grows its own logic, it becomes a
second implementation of the domains and drifts from them.

## Decision

Expose a single **FastAPI** facade — `services/api` — as the one network boundary
for the desktop UI. It extends, rather than replaces, what `dashboard.py`
already runs.

- **Read endpoints** are thin wrappers over each service/domain's existing public
  API (memory recall, graph queries, planner briefing, task/habit/product lists)
  — **no new logic in the facade.**
- A **WebSocket channel** pushes live events (voice transcript state,
  notifications, agent job status) — the upgrade path from `dashboard.py`'s
  ~15 s polling. `MutationEvent`s are published to WebSocket subscribers as they
  occur ([0005](0005-mutationevent-as-atomic-state-change.md)).
- Request/response shapes are versioned **contracts** in `packages/api-contracts`,
  keeping the frontend and backend able to evolve independently
  ([0024](0024-stable-contracts-flexible-internals.md)).

## Alternatives Considered

1. **Flask** (what `dashboard.py` used) carried forward as the API.
2. **A hand-rolled HTTP server** or a lower-level ASGI setup.
3. **gRPC / a binary RPC protocol** between desktop and backend.

## Consequences

- One enforced boundary: everything the desktop reads or subscribes to goes
  through the facade's public contracts, so the UI cannot reach a service
  internal.
- FastAPI gives typed request/response models and first-class WebSocket support,
  which fits the contract discipline and the live-push requirement directly.
- The facade stays thin — a wrapper, not a brain — so the domains remain the
  single implementation of their logic.
- `dashboard.py` keeps working unmigrated; the facade is additive, not a
  big-bang replacement.

## Why Alternatives Were Rejected

- **Flask carried forward** lacks native async/WebSocket ergonomics and typed
  models; the live-push channel and contract-typed endpoints are exactly what
  pushed the choice to FastAPI. Staying on Flask would mean bolting those on.
- **A hand-rolled server** re-implements routing, validation, and WebSocket
  handling that FastAPI provides and that the team would otherwise maintain by
  hand — cost with no benefit.
- **gRPC / binary RPC** imposes a codegen toolchain and a non-browser-native
  protocol on a local desktop↔backend link, where HTTP/JSON + WebSocket is
  simpler, debuggable with `curl`, and already matches the contracts package.

## Future Evolution

- New clients (additional desktop surfaces, a future mobile or CLI client) speak
  the same facade — the API, not any one client, is the durable contract
  ([0019](0019-electron-desktop-separate-process.md)).
- New read endpoints are added as thin wrappers over service/domain public APIs.
  Anything that would put *logic* in the facade is a signal it belongs in a
  service or domain instead — the facade must stay thin.
- Write access is intentionally excluded here and governed separately
  ([0021](0021-read-only-api-philosophy.md)).
