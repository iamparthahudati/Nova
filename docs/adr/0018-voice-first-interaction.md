# ADR 0018 — Voice-first interaction

- **Status:** Accepted
- **Date recorded:** 2026-07-06
- **Deciders:** Principal Architect
- **Relates to:** [0001](0001-local-first-architecture.md),
  [0002](0002-tiered-three-model-ai-architecture.md),
  [0019](0019-electron-desktop-separate-process.md)

## Context

Nova is a personal assistant meant to be present throughout the day while the
user is doing something else — working, cooking, at the desk. The primary
interaction modality shapes the whole runtime: what runs at startup, what blocks
a turn, and what the first UI must render. A text-only chat app and a
voice-present assistant are different systems at the core, so the modality is an
architectural decision, not a UI preference.

## Decision

Nova is **voice-first**. The primary interaction loop is: wake word → local
Whisper transcription → reasoning turn → spoken/served response. This is
load-bearing in the runtime:

- Voice is a Core-adjacent **service** whose Whisper model is loaded at startup
  (a blocking 5–30 s Model-Load phase) and lives in memory for the whole run.
- Transcription is **local and synchronous** — it blocks the main thread by
  design ([0006](0006-event-driven-single-process-runtime.md)) and runs on-device
  for privacy and cost ([0002](0002-tiered-three-model-ai-architecture.md)).
- The first real UI surfaces (floating assistant, voice overlay with
  waveform/transcript) are built *around* voice, and are pure consumers of a
  transcript stream — not a replacement for it.

Voice-first does **not** mean voice-only: text entry and the desktop UI are
first-class, but they are peers layered on the same pipeline, not the center of
gravity.

## Alternatives Considered

1. **Text-first / chat-app** with voice as an optional add-on.
2. **Cloud speech-to-text** (a hosted STT API) instead of local Whisper.
3. **Always-listening continuous transcription** rather than wake-word gated.

## Consequences

- The runtime pays a real startup cost (Whisper load) and a per-turn main-thread
  block for transcription — both accepted as the price of a local, private voice
  loop.
- Whisper failure modes are first-class (download failure, OOM, inference
  timeout) and handled explicitly in the runtime's error catalog.
- The UI roadmap is oriented around ambient/voice surfaces first (floating
  assistant, voice overlay), with richer visual surfaces following.
- macOS/hardware coupling (microphone, audio libs) is inherent to the modality.

## Why Alternatives Were Rejected

- **Text-first** would produce a different product — a chat app — and would not
  justify the ambient, hands-busy presence Nova is designed for. Bolting voice on
  later cannot retrofit the startup/turn model a voice loop needs.
- **Cloud STT** streams the user's raw speech — among the most sensitive data
  they produce — to a third party on every turn, violating local-first
  ([0001](0001-local-first-architecture.md)), and adds per-turn cost and a network
  dependency to the highest-volume path. Rejected on privacy and cost.
- **Always-listening** maximizes both privacy exposure and compute for little
  benefit; wake-word gating keeps capture intentional. (Later opt-in ambient
  features, like periodic screen capture, are gated and off by default for the
  same reason.)

## Future Evolution

- Voice is a leaf service ([0010](0010-service-isolation.md)): the STT model
  (Whisper today) can be swapped for a better local model wholesale behind its
  public API, with no change to the pipeline.
- A local wake-word / VAD model and richer TTS are additive within the Voice
  service; visual voice feedback is a UI-side consumer of the transcript stream
  and never changes the service.
