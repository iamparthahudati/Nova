# ADR 0010 — Service isolation (services are leaves)

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0009](0009-layered-package-taxonomy.md),
  [0008](0008-dependency-injection-over-imports.md),
  [0011](0011-domain-isolation.md),
  [0023](0023-architecture-testing.md)

## Context

Services are Nova's reusable behaviors that touch the outside world: Voice
(microphone, Whisper, TTS), Calendar (AppleScript), Automation (app control,
notifications), Knowledge (weather, RSS, GitHub). These are exactly the parts of
the system most likely to be replaced wholesale over a decade — a new STT model,
a different calendar backend, a new OS bridge. For that replaceability to be
real, a service must not accumulate dependencies on domains or on other services.

## Decision

**Services are leaves.** A service depends only on Core Infrastructure (and its
own external libraries), and only via dependency injection. A service **never**
imports a domain, and **never** imports another service. It exposes a small
public API and receives whatever it needs (callbacks, handlers) injected by the
composition root.

Concretely: Voice never imports Memory/Brain/domains (it receives injected
handlers); Calendar never persists and never calls Brain; Automation makes no
cross-service call to Calendar; Knowledge triggers reflection by *calling into
Brain through the sanctioned path*, never by reaching sideways. Cross-service
fusion (e.g. "is this screenshot a build error in this project") happens in Brain,
which is allowed to depend on everyone — never in a leaf.

## Alternatives Considered

1. **Services free to call each other** for convenience.
2. **A "services" god-package** with shared cross-service helpers.
3. **Services allowed to call domains** to "just get the data they need."

## Consequences

- A service can be swapped wholesale — Voice's Whisper model, Calendar's
  AppleScript bridge — because it sits behind a stable public API with no inbound
  coupling. This is the explicit ten-year replaceability strategy: replace
  leaves, not the trunk.
- Services are trivially testable in isolation with injected fakes; their lower
  coverage floor (75%) reflects only hardware/OS edges uncoverable in CI.
- Any cross-service capability must be expressed as an orchestration in Brain or
  the composition root, never smuggled into a leaf.
- The constraint is enforced by the architecture tests, not left to discipline.

## Why Alternatives Were Rejected

- **Services calling each other** creates a service mesh with cycles and destroys
  wholesale replaceability — the moment Automation imports Calendar, neither can
  be swapped independently. This is the exact coupling the leaf rule forbids.
- **A services god-package** centralizes the coupling instead of removing it;
  shared cross-service state re-couples the leaves through the back door.
- **Services calling domains** inverts the dependency direction
  ([0009](0009-layered-package-taxonomy.md)) — a leaf would depend on business
  logic that is supposed to depend on *it*. Rejected as a direction violation.

## Future Evolution

- New services (Vision, DevBrain in later phases) are added as new leaves with
  the same discipline: one responsibility, a public API, documented "does not
  own", no sideways edges.
- When a service is retired, it is removed as a whole with its injection point at
  the root — precisely because nothing depends on it laterally.
