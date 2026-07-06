# ADR 0011 — Domain isolation (no domain calls another domain)

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0009](0009-layered-package-taxonomy.md),
  [0004](0004-memory-is-the-only-storage-owner.md),
  [0010](0010-service-isolation.md),
  [0017](0017-finance-as-the-first-domain.md)

## Context

Domains own business logic and persistence for a user-facing capability: Finance
(tasks, money, products), Wellness (habits), Productivity (progress, planning).
As domains multiply, the tempting shortcut is for one domain to import another —
Productivity reaching into Finance to read tasks, say. Once that happens, domains
can no longer be added, reasoned about, or removed independently, and the "grow
by addition" property ([0009](0009-layered-package-taxonomy.md)) is lost.

## Decision

**A domain never imports or calls another domain directly.** Each domain defines
its own entities, mutations, and tools; persists through Memory's public API
([0004](0004-memory-is-the-only-storage-owner.md)); and publishes
`MutationEvent`s upward ([0005](0005-mutationevent-as-atomic-state-change.md)).
When one domain genuinely needs data another owns, the connection is made by the
composition root (injection) or mediated by Brain — never by a direct
domain-to-domain import.

Domains also do not import services directly; a service a domain needs (e.g.
Calendar for Finance) is injected as a tool-handler input by the root, not
imported. This is asserted by the architecture tests: `nova.domains.X` MUST NOT
import `nova.domains.Y`.

## Alternatives Considered

1. **Domains call each other directly** when they need each other's data.
2. **A shared "domain-common" package** holding cross-domain logic.
3. **A domain event bus** letting domains subscribe to each other's mutations
   directly.

## Consequences

- Domains are independently addable and removable: a new domain is a new package
  plus wiring; a retired domain is deleted as a whole without unpicking inbound
  calls from peers.
- Cross-domain features are expressed where cross-cutting logic belongs — in
  Brain (which may depend on everyone) or in an orchestration layer — keeping the
  domains themselves simple and single-purpose.
- All cross-domain data flow is visible: it goes through Memory, the event
  stream, or the root, all of which are inspectable, rather than through a web of
  direct calls.

## Why Alternatives Were Rejected

- **Direct domain-to-domain calls** are the single fastest way to turn a clean
  package set into a mesh; within a few features every domain knows every other
  and none can move. This is the erosion the rule exists to stop.
- **A domain-common package** becomes a dumping ground that every domain depends
  on, coupling them transitively through shared logic — the same mesh with one
  more hop.
- **A domain event bus for cross-domain subscription** re-creates hidden coupling
  (domain A silently reacts to domain B) and competes with the one sanctioned
  change substrate, `MutationEvent`. If cross-domain reaction is needed, it lives
  in an explicit orchestrator, not in peer domains wired to each other.

## Future Evolution

- New domains (Wellness, Productivity, and beyond) are added under the identical
  constraint; Finance set the persistence/mutation/tool pattern they follow
  ([0017](0017-finance-as-the-first-domain.md)).
- If a real cross-domain workflow emerges, it is modeled as an explicit
  orchestration package that depends on the domains — never by relaxing the
  no-sideways-import rule between the domains themselves.
