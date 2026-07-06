# ADR 0000 — Record architecture decisions

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect (custodian of Nova Core)
- **Supersedes:** —
- **Superseded by:** —

## Context

Nova Core v1.0 is frozen. Its architecture, runtime, and engineering standards
are captured across four large documents, but the *rationale* for individual
high-impact decisions is distributed through those documents as prose. In a
system explicitly designed to still make sense in ten years, the largest risk is
not a wrong decision — it is a correct decision that a future engineer cannot
distinguish from an accident, and so "cleans up" or reverses without knowing
what it was load-bearing for.

The Engineering Handbook (§8.4) already mandates ADRs for any decision that is
non-obvious, hard to reverse, or crosses a boundary, and fixes their location
(`docs/adr/NNNN-short-title.md`) and format (Context → Decision → Consequences →
Alternatives). What did not yet exist was the founding library covering the
irreversible decisions made *before* the ADR discipline was in force.

## Decision

Adopt Architecture Decision Records as the permanent, append-only record of
Nova's irreversible and high-impact architectural decisions, and retroactively
author one ADR for each such decision already embodied in Nova Core v1.0.

- Location and naming: `docs/adr/NNNN-short-title.md`.
- Structure: Context, Decision, Alternatives Considered, Consequences, Why
  Alternatives Were Rejected, Future Evolution.
- ADRs are immutable once Accepted. A change of course is a new, superseding ADR
  that links the old one, never an edit.
- An ADR records a decision and its trade-off; it does **not** re-open the frozen
  architecture.

## Alternatives Considered

1. **No formal record; rely on the frozen specs.** The specs describe *what* the
   system is; they are not organized around *why each irreversible choice was
   made* and what was rejected.
2. **A single "decisions" chapter appended to a spec.** One monolithic document
   cannot be append-only per-decision, is harder to link to precisely, and
   invites editing history in place.
3. **An external wiki / issue tracker.** Moves the record out of the repository,
   where it drifts from the code and is not versioned alongside it.

## Consequences

- Every irreversible decision has a stable, linkable home that travels with the
  code and is reviewed like code.
- Future engineers inherit not just the design but the discarded alternatives,
  which is what actually prevents re-litigation.
- A modest ongoing cost: any future boundary-crossing or hard-to-reverse change
  must ship with an ADR (already required by Handbook §8.4).

## Why Alternatives Were Rejected

Alternatives 1–3 all fail the ten-year test in the same way: they separate the
rationale from the artifact, either in time (undated prose), in structure
(no per-decision immutability), or in location (out of the repo). The whole
value of an ADR is that it is small, dated, immutable, and co-located with the
thing it explains.

## Future Evolution

The ADR *process* itself is not expected to change. If the repository ever adopts
a tool-assisted ADR format (e.g. structured front-matter for tooling), that is a
formatting migration recorded as its own ADR, applied additively, never a reason
to rewrite existing records.
