# ADR 0016 — Explicit uncertainty

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0015](0015-explainable-decision-making.md),
  [0004](0004-memory-is-the-only-storage-owner.md),
  [0005](0005-mutationevent-as-atomic-state-change.md)

## Context

Much of what Nova knows is *inferred*, not stated: a profile observation
extracted from conversation, an entity relation guessed from text, a memory's
importance, a detected "habit candidate." Inference is fallible. If inferred
beliefs are stored as if they were facts — flat, unqualified, permanent — the
system accumulates confident errors it cannot later question, and it cannot tell
the difference between "the user told me this" and "I guessed this."

## Decision

**Uncertainty is represented explicitly and carried through the system, never
flattened into false certainty.** Concretely:

- **Confidence is a first-class field.** Reflection output carries a `confidence`
  score per observation; inferred records are qualified rather than asserted.
- **Importance is a prior, not a verdict.** A memory's write-time importance is
  "a starting prior, not a final judgment"; a memory earns `long-term` only by
  *repeatedly proving useful* (access reinforcement), and decays if it doesn't —
  the system defers judgment to evidence over time.
- **Belief can decay.** When a profile observation is increasingly contradicted
  by recent behavior ("drift"), its confidence *should decay* — belief is not
  frozen once written.
- **Ranking blends signals, not a single hard label.** Recall composites
  similarity, importance, recency decay, and access count — an explicit
  weighting of uncertain signals, with weights the Learning Engine may tune as it
  observes what actually matters.

Uncertainty is preserved by the supersession model
([0015](0015-explainable-decision-making.md)): a corrected belief is a new,
higher-confidence row superseding the old one, keeping the history of what was
believed and how sure Nova was.

## Alternatives Considered

1. **Boolean facts** — store inferences as true/false with no confidence.
2. **Confidence computed only at read time**, never persisted.
3. **Hard classification at write time** — assign a memory its final tier
   immediately from its initial importance.

## Consequences

- Nova can distinguish stated fact from inference and act proportionately — it can
  hedge, ask, or defer instead of asserting a guess.
- Wrong inferences are self-correcting: low-confidence, un-reinforced beliefs
  decay and get superseded rather than calcifying.
- Every consumer must handle graded belief (a confidence, a tier) rather than a
  boolean — a permanent but deliberate cost that keeps the system honest.

## Why Alternatives Were Rejected

- **Boolean facts** collapse the crucial distinction between known and guessed;
  the first confident-but-wrong inference becomes an un-questionable "fact." This
  is exactly the failure mode explicit uncertainty exists to prevent.
- **Read-time-only confidence** cannot capture how sure Nova was *when it learned
  something*, and cannot support drift/decay over time — the signal must be
  persisted to be diffed across weeks.
- **Hard write-time classification** contradicts the earn-your-tier model: a
  memory written with high initial importance but never recalled would be
  permanently over-ranked. Tiers are recomputed from evidence, not fixed at
  birth.

## Future Evolution

- Confidence-shaped output contracts (extraction, learning insights) are made
  code-canonical (schema + validator in Brain) as they are introduced, so the
  uncertainty fields are validated at the AI edge, not merely conventional.
- Surfacing uncertainty to the user ("I think, but I'm not sure…") is a UI/voice
  refinement the persisted confidence already supports — a read-side change.
