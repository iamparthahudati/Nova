# ADR 0009 — Layered package taxonomy: Core / Services / Domains

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0010](0010-service-isolation.md),
  [0011](0011-domain-isolation.md),
  [0007](0007-composition-root-owns-all-wiring.md),
  [0023](0023-architecture-testing.md)

## Context

A codebase intended to survive a decade and to grow by *addition* (new
capabilities) rather than *modification* (touching existing code) needs a small,
fixed set of package *kinds* with unambiguous ownership and a strict,
one-directional dependency rule. Without named kinds and a direction, "where does
this code go?" is answered ad hoc, and dependencies grow sideways until the graph
is a mesh no one can reason about.

## Decision

Every package is exactly one of three kinds, with a strict upward-only
dependency rule:

| Kind | Owns | May depend on |
|---|---|---|
| **Core Infrastructure** (`nova.core.*`) | runtime, memory, brain, contracts | stdlib + vetted third-party libs only |
| **Services** (`nova.services.*`) — leaves | reusable behaviors (Voice, Calendar, Automation, Knowledge) | Core only, via injection |
| **Domains** (`nova.domains.*`) | business logic + persistence for a user capability (Finance, Wellness, Productivity) | Core; Services (injected); Domains only under strict constraint |

The core principle is **clear ownership: every package has one responsibility;
packages never depend sideways, only upward through public interfaces.** New
capability = new package, not a widened existing one. The growth strategy is
explicit: new domains are added as packages without modifying existing code and
with no core framework change.

## Alternatives Considered

1. **Flat package structure** — one level, no kinds, informal conventions.
2. **Feature-sliced / vertical slices** — group everything for a feature
   together, no shared horizontal layers.
3. **Deeper layering** (e.g. separate application/service/repository/domain tiers
   in the classic enterprise style).

## Consequences

- "Where does this go?" has one answer determined by the code's kind, and the
  legal dependencies of that kind are known in advance.
- The system grows by addition: a new domain is a new package plus a few wiring
  lines at the root ([0007](0007-composition-root-owns-all-wiring.md)); existing
  code is untouched.
- The dependency direction is machine-checkable, and it is
  ([0023](0023-architecture-testing.md)).
- The taxonomy must be respected forever; introducing a fourth kind is itself an
  architectural decision requiring an ADR.

## Why Alternatives Were Rejected

- **Flat structure** has no enforceable direction; dependencies grow sideways and
  the graph becomes a mesh — the exact ten-year erosion this taxonomy prevents.
- **Feature slices** optimize for co-locating one feature at the cost of the
  shared, reusable horizontal foundation (one Memory, one Brain, one runtime)
  that Nova's whole model depends on. Reasoning and storage must be *shared*
  ownership, not sliced per feature.
- **Deeper enterprise layering** adds tiers and indirection that a single-process,
  personal-scale system does not need; three kinds are the minimum that still
  gives clear ownership and a testable direction. More tiers, more ceremony, no
  benefit.

## Future Evolution

- New services and domains are added within the existing three kinds
  indefinitely — this is the designed growth path.
- Tools and Tests are organizational tiers around these three package kinds;
  they consume the kinds but do not add a new dependency direction.
- A genuinely new *kind* of package (should one ever be justified) supersedes
  this ADR explicitly rather than being slipped in.
