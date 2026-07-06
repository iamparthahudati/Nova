# ADR 0008 — Dependency injection over cross-boundary imports

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0003](0003-brain-is-the-only-claude-client.md),
  [0007](0007-composition-root-owns-all-wiring.md),
  [0010](0010-service-isolation.md),
  [0011](0011-domain-isolation.md)

## Context

Packages need each other's *behavior* without depending on each other's *code*.
Brain needs today's calendar events but must not import the Calendar service.
Runtime needs to dispatch to domain tools but must not import every domain.
Services need to be triggered without knowing who triggers them. Direct imports
across these boundaries would create the coupling and cycles the whole
architecture is built to avoid.

## Decision

Cross-boundary access is by **dependency injection**, never by import. The
composition root ([0007](0007-composition-root-owns-all-wiring.md)) passes
functions and registries into the packages that consume them:

- Brain receives the calendar read function via `brain.set_calendar_source(
  calendar.get_events)` — the single DI point in the runtime — and receives
  `context_providers` and tool handlers the same way. **Brain never imports
  Calendar or any service.**
- Runtime dispatches Claude's tool calls through an injected `TOOL_HANDLERS`
  dict; it never imports the domains behind those handlers.
- Services receive callbacks/handlers (e.g. Voice, Pomodoro's `speak_callback`)
  rather than importing Memory, Brain, or domains.

The shape is uniform: a package declares the *type* of collaborator it needs
(a callable, a provider), and the root supplies the concrete one. Wall clock and
RNG are injected the same way, which is also what makes the system deterministic
and testable.

## Alternatives Considered

1. **Direct imports** across package boundaries.
2. **A global registry / service locator** packages read from.
3. **A DI container framework** resolving dependencies automatically.

## Consequences

- The dependency graph stays acyclic and the boundaries stay real — enforced by
  the architecture tests ([0023](0023-architecture-testing.md)).
- Testing is trivial: inject a scripted fake Claude, a fixed clock, a fake
  calendar source. Fakes at the injection seam survive refactors
  ([0022](0022-testing-philosophy.md)).
- A small, explicit cost at the root: every collaborator must be passed in. This
  is deliberate — it keeps the wiring visible in one place.
- Packages are honest about their dependencies: what a package needs is exactly
  what is injected into it, nothing ambient.

## Why Alternatives Were Rejected

- **Direct imports** create exactly the cross-boundary coupling and cycles the
  architecture forbids (a service importing a domain, Brain importing Calendar).
  This is the primary thing DI exists to prevent.
- **Global registry / service locator** trades explicit imports for ambient
  global state — the coupling is hidden rather than removed, and the graph
  becomes unknowable statically. Rejected (same reasoning as
  [0007](0007-composition-root-owns-all-wiring.md)).
- **A DI container** adds framework magic and runtime resolution the Handbook's
  "no hidden magic" rule rejects; explicit injection at one root is clearer at
  this scale.

## Future Evolution

- New collaborators follow the identical shape — declare the callable/provider
  type, inject at the root. No new mechanism is needed as the system grows.
- The injected-function seam (`set_calendar_source`, `TOOL_HANDLERS`,
  `context_providers`) is also the swap point for future providers (a new
  calendar backend, a new tool source) without touching consumers.
