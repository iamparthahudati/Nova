# ADR 0019 — Electron desktop as a separate process

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0020](0020-fastapi-facade.md),
  [0021](0021-read-only-api-philosophy.md),
  [0018](0018-voice-first-interaction.md)

## Context

Nova needs a real visual UI — a floating assistant, a voice overlay, a sidebar,
a dashboard, widgets. The existing `dashboard.py` proved the shape of a second
process reading Memory, but it also committed a boundary violation the review
flagged: it re-implemented Calendar's AppleScript fetch instead of calling
`calendar.get_events()`. Any UI that *can* import the Python services will
eventually duplicate their logic. The UI decision is thus really a boundary
decision.

## Decision

The desktop UI is a **separate process** — an **Electron + React** application at
`apps/desktop/` — that talks to the backend **only over the network** (HTTP /
WebSocket) through the API facade ([0020](0020-fastapi-facade.md)). It has **no
Python import path** into Nova at all.

This is deliberately a forcing function, not just a tech choice: because an
Electron/JS renderer *cannot* import Python service modules, it is
*architecturally incapable* of duplicating Calendar's AppleScript logic (or any
service internal) the way `dashboard.py` did. The stack (React 19, Vite, Zustand,
Tailwind, shadcn/ui; TS main/preload) is an implementation detail; the
*process/network boundary* is the decision.

## Alternatives Considered

1. **An in-process Python GUI** (e.g. a native/Tk/Qt or Python-webview UI sharing
   the interpreter).
2. **A web UI served in-process** but still able to call Python directly
   server-side (extending `dashboard.py`'s pattern).
3. **A native macOS app** talking to Python via a custom bridge.

## Consequences

- The desktop app can only reach Nova through the API's public surface — it is
  the first consumer that *cannot* cheat past a boundary, which is the entire
  point.
- A rich, modern UI toolchain (React/Electron) is available for the ambient
  surfaces voice-first needs ([0018](0018-voice-first-interaction.md)).
- Two runtimes to build and ship (Python backend + Electron app) and an IPC/HTTP
  boundary to define — accepted as the cost of an enforceable boundary.
- Electron's memory footprint and packaging are accepted trade-offs for
  cross-render-stack velocity on desktop.

## Why Alternatives Were Rejected

- **An in-process Python GUI** shares the interpreter and can import any service —
  reintroducing exactly the `dashboard.py` violation, on purpose-defeating terms.
  The value of the decision is the *inability* to import; an in-process GUI throws
  that away.
- **A web UI that still calls Python server-side directly** has the same defect:
  as long as there is a Python import path, logic gets duplicated across it. The
  network boundary must be the *only* path.
- **A native macOS app with a custom bridge** couples the UI to one platform and
  to a bespoke IPC contract, for no gain over a standard HTTP/WebSocket facade.

## Future Evolution

- Because the boundary is HTTP/WebSocket, the frontend stack is fully replaceable
  (a different web framework, or additional clients — mobile, CLI) without
  touching the backend; each new client speaks the same API.
- `dashboard.py` remains valid as a legacy direct-Memory reader; new UI work goes
  through the facade. The facade — not the Electron choice — is the durable part.
