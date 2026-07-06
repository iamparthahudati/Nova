# ADR 0015 — Explainable decision-making

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0005](0005-mutationevent-as-atomic-state-change.md),
  [0016](0016-explicit-uncertainty.md),
  [0004](0004-memory-is-the-only-storage-owner.md)

## Context

Nova acts on a user's behalf — it logs money, creates tasks, surfaces insights
("your task completion drops in weeks with no exercise"), and adjusts its own
model of the user through reflection and learning. An assistant that changes
state and offers judgments but cannot say *what it did* and *why* is neither
trustworthy nor debuggable. Over ten years, opacity is also a maintenance
hazard: a future engineer must be able to reconstruct why the system believed or
did something.

## Decision

**Decisions and state changes must be explainable from recorded structure, not
reconstructed from guesswork.** This is realized through several already-made
choices working together:

- **Structured mutations.** Every state change is a `MutationEvent` recording
  *what* changed (entity, operation, data)
  ([0005](0005-mutationevent-as-atomic-state-change.md)) — the audit substrate.
- **Provenance on derived knowledge.** Graph edges carry the memory/conversation
  that produced them ([0014](0014-property-graph-in-sqlite.md)); memories carry
  `source_type`/`source_id`. Every derived fact points back to its origin.
- **History, not overwrite.** Understanding evolves by *supersession*
  (`supersedes_id` chains), not in-place mutation, so the trail of *how belief
  changed over time* survives — this is what lets Learning diff this week's model
  against last week's.
- **Insights are traceable, not asserted.** Learning runs cheap local
  pre-filters (streaks, frequencies, deltas) first, and only the patterns that
  clear them go to Brain for synthesis — so a surfaced insight is backed by a
  concrete statistical signal, not an unattributable model whim.

## Alternatives Considered

1. **Opaque mutation** — change state directly, log only free text.
2. **Overwrite-in-place** for evolving beliefs (profile, tiers).
3. **Unattributed insights** — let the reasoning model assert conclusions with no
   recorded supporting signal.

## Consequences

- "What did Nova do, and why?" is answerable from the event stream, provenance
  fields, and supersession chains — structurally, not by log archaeology.
- The same structure powers Learning's drift detection and any future audit or
  "explain this" UI surface, for free.
- A modest, permanent cost: every state change carries structure and provenance,
  and belief updates keep history instead of overwriting.

## Why Alternatives Were Rejected

- **Opaque mutation** makes the system untrustworthy and undebuggable — there is
  no reliable record of what changed, only prose logs that drift from reality.
  Directly contrary to why `MutationEvent` exists.
- **Overwrite-in-place** destroys the very signal explainability needs: once last
  week's belief is gone, "why did this change?" is unanswerable and drift
  detection is impossible. Supersession keeps the trail
  ([0016](0016-explicit-uncertainty.md) depends on it too).
- **Unattributed insights** would let Nova make confident claims it cannot
  substantiate — the opposite of explainable, and corrosive to trust the first
  time an unsupported claim is wrong.

## Future Evolution

- An explicit "explain this decision/insight" surface (UI or voice) is a natural
  future feature; the recorded structure to power it already exists, so it is a
  read-side addition, not a data-model change.
- If a durable `MutationEvent` log is added ([0005](0005-mutationevent-as-atomic-state-change.md)),
  explainability strengthens further — replay becomes possible — additively.
