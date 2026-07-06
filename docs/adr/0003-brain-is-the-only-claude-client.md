# ADR 0003 — Brain is the only Claude client

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0002](0002-tiered-three-model-ai-architecture.md),
  [0004](0004-memory-is-the-only-storage-owner.md),
  [0008](0008-dependency-injection-over-imports.md),
  [0024](0024-stable-contracts-flexible-internals.md)

## Context

Many parts of Nova want reasoning: Knowledge wants weekly reflection, Vision
wants to interpret a screenshot, Learning wants to turn patterns into a coaching
sentence, the Graph wants entities extracted from text. The naive path is for
each of these to hold an API key and call Claude directly.

That path produces a system with many uncontrolled egress points for private
data, many places prompts and output-contracts are defined, many places retry,
cost, and error handling are re-implemented, and no single seam at which the
reasoning provider could ever be changed. At personal scale with the most
sensitive data a user owns, uncontrolled model access is the failure mode.

## Decision

**Brain (`nova.core.brain`) is the only package that imports the `anthropic`
client or holds an API key. No service and no domain ever calls Claude
directly.** Other packages gather and structure data and hand it to Brain; Brain
owns Claude routing, system-prompt assembly, conversation history, entity
extraction, and reflection reasoning.

This generalizes the pattern Knowledge already used (`knowledge.reflection` →
`brain.run_reflection_job`) into a hard, testable rule: the architecture tests
assert that *nothing but Brain imports `anthropic`*
(see [0023](0023-architecture-testing.md)). Brain reaches other capabilities only
through dependency injection ([0008](0008-dependency-injection-over-imports.md)),
never by importing services or domains.

## Alternatives Considered

1. **Every service its own Claude client.** Each package calls the model when it
   needs reasoning.
2. **A shared "llm utils" helper module** importable by anyone, wrapping the
   client but not owning the boundary.
3. **A reasoning gateway as a separate service** that Brain and others both call.

## Consequences

- Exactly one egress point for reasoning: one API key, one place for cost and
  retry policy, one auditable seam for what data reaches the model.
- The reasoning provider is swappable at a single boundary — the whole point of
  [0002](0002-tiered-three-model-ai-architecture.md)'s reasoning tier being
  replaceable.
- All Claude input/output contracts live in one place and are code-canonical
  (schema + validator in Brain), keeping the AI edge testable
  ([0024](0024-stable-contracts-flexible-internals.md)).
- Brain becomes a package almost everything eventually depends on for reasoning;
  it must stay disciplined about not importing its callers (enforced by DI).

## Why Alternatives Were Rejected

- **Every service its own client** scatters the API key, the prompts, the cost
  controls, and — critically — the private-data egress across the codebase, with
  no seam to swap providers and nothing to audit. This is the exact anti-pattern
  the rule exists to forbid.
- **A shared llm-utils helper** looks like centralization but isn't: if anyone
  can import it, the egress points are still everywhere and the boundary is
  unenforceable by the architecture tests. Centralizing the *client* without
  centralizing the *ownership* buys nothing.
- **A separate reasoning-gateway service** adds a process/package boundary and
  indirection for a single-process, single-user system, duplicating what Brain
  already is. Rejected as needless infrastructure.

## Future Evolution

- Swapping or adding a reasoning provider (including an eventual local model per
  [0001](0001-local-first-architecture.md)) happens entirely inside Brain behind
  its public API; callers do not change.
- If reasoning ever needs to scale out of the single process, the *replacement*
  for this ADR would introduce a gateway and supersede it explicitly — it would
  not be a quiet relaxation of the "only Brain" rule.
