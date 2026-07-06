# ADR 0001 — Local-first architecture

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0002](0002-tiered-three-model-ai-architecture.md),
  [0003](0003-brain-is-the-only-claude-client.md),
  [0012](0012-sqlite-as-system-of-record.md),
  [0018](0018-voice-first-interaction.md)

## Context

Nova is a personal assistant that sees a user's finances, schedule, habits,
conversations, and — in later phases — their screen. This is the most private
data a person owns. Nova also runs continuously on a single user's machine at
personal scale (thousands of entities, not billions), and must be cheap enough
to run all day without a per-interaction cloud bill for routine work.

Two forces therefore dominate: **privacy** (this data should not leave the
device unless reasoning genuinely requires it) and **cost/latency** (routine
perception should not incur network round-trips or API charges).

## Decision

Nova is **local-first**. All persistence is on-device (see
[0012](0012-sqlite-as-system-of-record.md),
[0013](0013-lancedb-as-vector-index.md)); routine perception runs on local
models (Whisper for speech, on-device embeddings for semantic memory, local OCR
for vision); and the network is reserved for the one capability that genuinely
needs a frontier model — reasoning — routed through a single client
(see [0002](0002-tiered-three-model-ai-architecture.md),
[0003](0003-brain-is-the-only-claude-client.md)). There is no cloud database and
no cloud sync in Nova Core v1.0.

This is stated as a governing rule ("Local-first stays local-first"), not a
preference: it is a privacy and cost constraint that every downstream decision
must respect.

## Alternatives Considered

1. **Cloud-first / SaaS architecture.** Central database, server-side reasoning,
   thin client.
2. **Hybrid with cloud sync of raw data.** Local operation but continuous
   replication of the ledger to a cloud store for backup/multi-device.
3. **Fully local, including reasoning** (a local LLM for the Brain).

## Consequences

- Strong privacy posture by construction: finance, screen OCR, and conversation
  content never leave the device except as the specific text handed to the
  reasoning model, gated per-turn.
- No cloud infrastructure to operate, secure, or pay for; steady-state cost is
  dominated by local model RAM (hundreds of MB) plus metered reasoning calls.
- The machine's resources bound the system: startup pays a local model-load cost
  (5–30 s), and platform coupling (macOS, AppleScript, CPU Whisper) is accepted.
- Multi-device and cloud backup are explicitly out of scope for v1.0 and become
  future work, not assumptions baked into the core.

## Why Alternatives Were Rejected

- **Cloud-first** inverts the privacy model — the most sensitive data a user owns
  would sit on someone else's server — and adds recurring cost and an always-on
  network dependency for a single-user tool. Rejected on privacy first, cost
  second.
- **Hybrid raw-data sync** reintroduces exactly the privacy exposure local-first
  exists to avoid, for a benefit (multi-device) not required by v1.0.
- **Fully local reasoning** was rejected on quality, not principle: the assistant's
  usefulness depends on frontier-grade reasoning that local models did not match
  at v1.0. The compromise is the tiered model architecture
  ([0002](0002-tiered-three-model-ai-architecture.md)) — local for perception,
  cloud for reasoning only.

## Future Evolution

- If a local reasoning model reaches the quality bar, the Brain's single client
  boundary ([0003](0003-brain-is-the-only-claude-client.md)) is exactly the seam
  that lets it be swapped without touching callers — the architecture is already
  shaped for it.
- Optional, user-controlled **encrypted cloud backup** (raw ledger, not
  reasoning) is a legitimate future feature; it must be opt-in and must not
  become a runtime dependency of the core.
