# ADR 0002 — Tiered three-model AI architecture

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0001](0001-local-first-architecture.md),
  [0003](0003-brain-is-the-only-claude-client.md),
  [0018](0018-voice-first-interaction.md)

## Context

Nova performs three fundamentally different kinds of machine-learning work, and
they have different cost, latency, and privacy profiles:

1. **Speech-to-text** — turning microphone audio into a transcript. High volume
   (every voice turn), latency-sensitive, no reasoning required.
2. **Embedding** — turning text into vectors for semantic memory recall. High
   volume (every remembered item and every query), cheap, no reasoning required.
3. **Reasoning** — understanding intent, choosing tools, synthesizing an answer,
   extracting entities, reflecting on the user. Low volume relative to the
   others, but genuinely needs a frontier model.

Treating all three as "call the big model" would be slow, expensive, and would
send far more private data to the cloud than necessary. Treating all three as
"run locally" would sacrifice the reasoning quality the assistant lives or dies
by (see [0001](0001-local-first-architecture.md)).

## Decision

Adopt a **three-model tiered architecture** that matches each class of work to
the cheapest model capable of it:

| Tier | Work | Model class | Location |
|---|---|---|---|
| Perception — speech | transcription | Whisper (`base.en`) | Local, CPU |
| Perception — semantic | embeddings (and OCR for vision) | small on-device model | Local |
| Reasoning | intent, tools, extraction, reflection | Claude (frontier) | Cloud, via Brain only |

The routing principle is fixed: **route routine work to a local model; reserve
the frontier model for reasoning that actually needs it.** The two local
perception tiers sit behind swappable provider interfaces (e.g. Whisper behind
Voice, an `EmbeddingProvider` behind Memory); the reasoning tier is reached only
through the single Brain client ([0003](0003-brain-is-the-only-claude-client.md)).

## Alternatives Considered

1. **One model for everything** — send audio and every recall to the frontier
   model's multimodal endpoint.
2. **Two tiers** — local speech, everything else (including embeddings) in the
   cloud.
3. **Local everything**, including a local reasoning LLM.

## Consequences

- Cost and latency are dominated by local inference for the high-volume paths;
  metered cloud spend tracks only the low-volume reasoning path.
- Privacy is preserved on the high-volume paths: raw audio and the full memory
  corpus never leave the device; only the specific text assembled for a turn is
  sent to reasoning.
- Three model lifecycles to own (load, cache, swap), each behind its own
  interface. The Whisper load is a blocking 5–30 s startup cost, accepted.
- Each tier evolves independently — a better local embedder or a better STT model
  is a leaf swap, not an architectural change.

## Why Alternatives Were Rejected

- **One model for everything** multiplies cost and latency by sending
  high-volume, low-complexity work to the most expensive model, and maximizes
  private-data egress. Rejected on all three of cost, latency, and privacy.
- **Two tiers (cloud embeddings)** would ship the entire memory corpus and every
  query to the cloud — the exact privacy exposure local-first forbids — to save a
  small local model that is cheap to run. Rejected.
- **Local reasoning** was rejected on quality at v1.0, identical to
  [0001](0001-local-first-architecture.md)'s reasoning; the tiering is precisely
  the compromise that keeps everything local *except* the tier that needs
  frontier quality.

## Future Evolution

- A fourth perception tier (local vision beyond OCR) slots in as another leaf
  provider without disturbing the tiering — Vision already follows this shape
  (local OCR always; frontier vision only on explicit request).
- If local reasoning quality catches up, the reasoning tier collapses into the
  local set behind the same Brain boundary; the tiering framework survives the
  change unchanged.
