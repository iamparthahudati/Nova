# ADR 0007 — Composition root owns all wiring

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0006](0006-event-driven-single-process-runtime.md),
  [0008](0008-dependency-injection-over-imports.md),
  [0010](0010-service-isolation.md),
  [0011](0011-domain-isolation.md)

## Context

A system built from strictly isolated packages (services that are leaves, domains
that never call each other, a Brain that never imports its callers) still has to
be *assembled* somewhere: someone must create the event bus, load the models,
register tool handlers, inject the calendar read function into Brain, and start
the run loop. If that assembly logic leaks into the packages themselves, the
isolation is a fiction — a domain that wires up another domain has coupled to it.

## Decision

There is exactly **one composition root** — `nova.py` / `nova.main` — and it owns
*all* wiring and lifecycle: it creates the event bus, loads models, builds the
provider/tool-handler registries, performs the single dependency-injection step
(`brain.set_calendar_source(calendar.get_events)`), and runs the loop.

**The composition root contains no business logic.** It is pure assembly. Its
footprint in each subsystem is deliberately tiny (e.g. Phase 2 added exactly one
line, `agents.run_due_jobs()`, to the run loop). Everything the root touches, it
touches to connect — never to decide. A hard rule (Handbook / Engineering Spec):
no package may import the runtime except the composition root, and no package
wires another; only the root does.

## Alternatives Considered

1. **Distributed wiring** — each package imports and constructs its own
   dependencies where it needs them.
2. **A DI framework / container** that resolves dependencies by
   annotation/registration.
3. **Service locator** — a global registry packages pull dependencies from.

## Consequences

- Package isolation is *real*: because only the root wires, a domain physically
  cannot depend on another domain's construction, and services stay leaves
  ([0010](0010-service-isolation.md), [0011](0011-domain-isolation.md)).
- The entire dependency graph is readable in one file — the assembly *is* the
  architecture diagram, and it is acyclic by inspection.
- Testing is straightforward: tests construct exactly the wiring they need,
  because construction is not hidden inside packages.
- The root is intentionally the only place with broad imports; its low coverage
  floor (60%) is accepted because E2E tests exercise the wiring.

## Why Alternatives Were Rejected

- **Distributed wiring** is the erosion path: the moment a package constructs its
  own collaborators, boundaries blur and cycles appear. This is precisely what
  the single-root rule prevents.
- **A DI framework/container** hides the graph behind runtime resolution and
  annotations — "hidden magic" the Handbook explicitly rejects. At this scale,
  explicit constructor wiring in one file is clearer than any container and costs
  nothing.
- **Service locator** is a global mutable dependency source: it re-introduces the
  ambient coupling DI exists to remove and makes the graph unknowable statically.
  Rejected.

## Future Evolution

- As packages are added, the root grows by a handful of wiring lines each; this
  is expected and healthy. If the root ever grows *logic* (a branch that decides
  behavior, not just connects), that is the smell to extract into a package — the
  root must stay assembly-only.
- Multiple entry points (CLI, API server, test harness) may each be a composition
  root variant, but each stays pure assembly over the same packages.
