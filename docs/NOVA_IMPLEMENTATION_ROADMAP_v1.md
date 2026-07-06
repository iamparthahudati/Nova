# NOVA IMPLEMENTATION ROADMAP v1

**Status:** Master Engineering Roadmap — Nova Core v1.0  
**Date:** July 6, 2026  
**Audience:** Development team, architects, stakeholders  
**Authority:** Principal Software Architect  
**Scope:** Implementation plan for 12–18 months (single senior engineer → team scale)

---

## EXECUTIVE SUMMARY

This document converts the frozen Nova Core v1.0 architecture (Runtime + Engineering specs) into a realistic, month-by-month implementation plan. It answers:

**"If I start tomorrow, exactly what should I build, in what order, and why?"**

### Key Principles

1. **Proof-of-concept first, optimization later.** Validate architectural assumptions early; refactor on learning.
2. **One senior engineer initially.** Realistic time estimates assume 1 engineer for the first 3–4 months, then team scaling.
3. **Independent PRs, weekly releases.** Every PR is stand-alone reviewable; deploy continuously.
4. **Architecture comes first, features second.** Build the foundation correctly, then add domains in parallel.
5. **Avoid optimism.** All estimates include testing, debugging, and iteration cycles.

### Expected Timeline

- **Milestone 0 (Weeks 1–2):** Foundation (DB schema, Memory layer, basic Brain).
- **Milestone 1 (Weeks 3–6):** Core Runtime (conversation pipeline, MutationEvents, event bus).
- **Milestone 2 (Weeks 7–10):** Finance Domain (tasks, money, products).
- **Milestone 3 (Weeks 11–14):** Voice Integration (wake word, transcription, TTS).
- **Milestone 4 (Weeks 15–18):** Desktop UI + API Facade (Electron + REST).
- **Milestone 5+ (Months 5–12):** Additional domains (Wellness, Productivity, Social), Phase 2 features.

**Total for v1.0 production-ready:** ~24 weeks (6 months) for one engineer. Team scales this to 4–5 months with 3–4 engineers.

---

## 1. OVERALL MILESTONE ROADMAP

### Milestone 0: Foundation & Core Infrastructure Setup
**Duration:** 2 weeks (Week 1–2)  
**Effort:** ~80 hours (senior engineer)  

**Goal:**  
Establish the rock-solid foundation: database schema, Memory layer (persistence abstraction), Brain (Claude interface), and the contract/type system. No conversation pipeline yet. Validation focus: architectural decisions, schema design, API contracts.

**Scope:**
- Repository organization (folder structure, package layout).
- Database schema (all v1.0 tables, idempotent migrations).
- Memory public API (add_task, get_task_by_id, add_money, etc.).
- Brain Claude client (route(), reflection(), extraction stubs).
- Contracts (MutationEvent, ConversationResult, enums, type defs).
- Connection pooling and error handling patterns.
- CI/CD setup (GitHub Actions, basic linting, type checking).

**Deliverables:**
- `nova/core/memory/schema.py` with all v1.0 tables.
- `nova/core/memory/__init__.py` with 30+ public functions.
- `nova/core/brain/__init__.py` with route(), reflection() stubs.
- `nova/core/contracts/` with complete type definitions.
- Initial test suite (unit tests for Memory + Brain).
- `.github/workflows/test.yml` CI pipeline.
- README with dev setup instructions.

**Definition of Done:**
- ✓ Database initializes, schema migrates on first run (idempotent).
- ✓ Memory public API can create/read all domain entities.
- ✓ Brain can call Claude API, handle responses.
- ✓ All unit tests pass locally and in CI.
- ✓ No circular dependencies; architecture tests pass.
- ✓ Type checking (mypy) passes with strict mode.

**Exit Criteria:**
- Memory can persist and retrieve tasks, money, progress rows.
- Brain can send/receive messages from Claude API.
- No runtime errors in basic flows.

**Risks:**
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Database schema incomplete | Medium | High | Review schema against all 12+ tables in spec; iterate early. |
| Memory API is incomplete | Medium | High | List all 50+ public functions in design doc; code review strict. |
| Brain API contracts wrong | Medium | High | Write contracts tests early; mock Claude calls before real API. |
| Type checking too strict | Low | Low | Configure mypy exclusions for vendor code; relax on 3rd party libs. |

---

### Milestone 1: Core Runtime & Conversation Pipeline
**Duration:** 4 weeks (Week 3–6)  
**Effort:** ~160 hours

**Goal:**  
Build the heart of Nova: the synchronous conversation pipeline. User speaks → transcript → Brain → tools → mutations → memory writes → WebSocket events. This is where the architecture's event-driven model is validated.

**Scope:**
- Conversation pipeline (`process_message()` in runtime/conversation.py).
- MutationEvent generation (deterministic tool → mutation mapping).
- Side-effects orchestration (mutation → memory write → event publication).
- Event bus (publish/subscribe for WebSocket).
- Tool dispatch wiring (dependency injection).
- Background thread spawning (entity extraction, reflection).
- Error boundaries and recovery (turn fails, app continues).

**Deliverables:**
- `nova/core/runtime/` package (conversation.py, mutation_event.py, side_effects.py, events.py).
- Tool instrumentation (record what was called).
- Memory producers (deterministic mutations → memory records).
- Event publishing infrastructure (fire-and-forget WebSocket).
- Full integration tests (transcript → memory write).

**Definition of Done:**
- ✓ Single conversation turn completes end-to-end without errors.
- ✓ MutationEvents are created and published correctly.
- ✓ Memory writes happen atomically (one transaction per turn).
- ✓ Background threads don't block main loop.
- ✓ Errors in tool execution don't crash the pipeline.
- ✓ Integration tests pass (full turn + memory persistence).

**Exit Criteria:**
- A tool can be registered, called by Claude, produce a result, and create a mutation.
- Mutations are visible in the database after a turn completes.
- WebSocket events are published (verified in tests).
- No memory writes are lost; transactions are atomic.

**Risks:**
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Tool dispatch is fragile | Medium | High | Design injection pattern first; test with multiple tool types. |
| Mutations don't match domain logic | Medium | High | Write comprehensive golden tests; compare against expected mutations. |
| Background thread coordination is wrong | Medium | Medium | Single background thread (extraction) initially; test isolation. |
| Event bus loses messages | Low | High | Use in-memory list; no persistence. Validate in tests. |
| Transaction atomicity breaks | Medium | High | Test multi-mutation turns; verify rollback on error. |

---

### Milestone 2: Finance Domain (Tasks, Money, Products)
**Duration:** 3 weeks (Week 7–9)  
**Effort:** ~120 hours

**Goal:**  
Implement the first user-facing domain. Users can add/complete tasks, log money, track products. This validates the domain → memory → mutation flow and proves the architecture works for real user workflows.

**Scope:**
- Finance domain package (`nova/domains/finance/`).
- Task logic (create, complete, query open/done tasks).
- Money logic (log expenses/earnings, summaries, filtering).
- Product logic (track ideas, shipping, sales).
- Tool handlers (10–15 conversational commands).
- Domain-specific memory producers (money entry → memory record).
- Integration tests (e2e: voice command → database).

**Deliverables:**
- `nova/domains/finance/` package (tasks.py, money.py, products.py, tools.py).
- Planner tool handlers (log_task, complete_task, get_open_tasks, etc.).
- Domain integration tests (tool dispatch → memory write).
- Golden tests (tool output format stability).
- API routes (GET /tasks, POST /tasks, GET /spending, etc.).

**Definition of Done:**
- ✓ "Add task buy milk" creates a task in the database.
- ✓ "How much did I spend this month?" queries and summarizes money records.
- ✓ Tasks can be completed, and status changes persist.
- ✓ All tool handlers return sensible spoken confirmations.
- ✓ Domain can be loaded, wired, and tested independently.
- ✓ No cross-domain dependencies introduced.

**Exit Criteria:**
- A realistic 10-minute user session (add tasks, log money, query summary) works end-to-end.
- All mutations for Finance tools are tested.
- Output format is stable (golden tests pass).

**Risks:**
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Tool output is inconsistent | Medium | Low | Write golden tests early; review output before release. |
| Money calculations are wrong | Low | High | Write unit tests for all math; test edge cases (negative, decimals). |
| Domain imports another domain | Low | High | Contract tests enforce isolation; code review checks imports. |
| Tool handlers are too complex | Medium | Low | Keep them simple (call domain logic, return string); test logic in domain. |

---

### Milestone 3: Voice Integration (Wake Word, Transcription, TTS)
**Duration:** 3 weeks (Week 10–12)  
**Effort:** ~120 hours

**Goal:**  
Give Nova a voice. Users speak naturally (wake word detection, transcription, text-to-speech). This completes the "Observation Layer" and validates end-to-end voice workflows.

**Scope:**
- Voice service package (`nova.services.voice/`).
- Wake word detection (overlapping windows, RMS gating).
- Whisper transcription (faster-whisper library).
- Text-to-speech (macOS `say` command).
- Audio I/O (sounddevice, microphone permissions).
- Wake word sensitivity tuning (threshold, false positive rate).
- Voice service integration tests (mic → transcript).

**Deliverables:**
- `nova/services/voice/` package (audio.py, wake_word.py, transcription.py, tts.py).
- `AssistantApp` composition root (nova.py).
- Main run loop (wake-word polling, transcript processing).
- Graceful shutdown (Ctrl+C).
- User-tunable RMS threshold configuration.
- E2E test (record sample audio → process → verify output).

**Definition of Done:**
- ✓ Wake word detection works reliably (tuned false positive rate ~1–5%).
- ✓ Transcription is accurate for clear speech.
- ✓ TTS speaks confirmed actions.
- ✓ Run loop doesn't block or hang.
- ✓ Microphone permissions are requested gracefully.
- ✓ Service is a leaf (no persistence, no Business logic).

**Exit Criteria:**
- User can speak naturally: "Rai, add task buy milk", and hear "Added task".
- Wake word doesn't trigger on silence or background noise (tune threshold).
- Latency is acceptable (~2–10 seconds per turn).

**Risks:**
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Wake word misses or false-triggers | High | High | Tune RMS threshold empirically; accept some false positives initially. |
| Transcription quality is poor | Medium | Low | Use faster-whisper (good accuracy); fallback to manual if needed. |
| Audio permissions are denied | Low | Medium | Clear error message; document how to grant in macOS settings. |
| Latency is unacceptable | Low | Medium | Measure per component (wake word, transcription, Brain); optimize locally. |
| TTS sounds robotic | Low | Low | Use macOS `say` (reasonably natural); accept it. |

---

### Milestone 4: Desktop UI + REST API Facade
**Duration:** 4 weeks (Week 13–16)  
**Effort:** ~160 hours

**Goal:**  
Build a desktop interface (Electron + React) and REST API layer. Users can interact via GUI or voice. This validates the API contract and gives product team visibility into user workflows.

**Scope:**
- REST API (FastAPI, read-only endpoints, WebSocket push).
- API routes (tasks, money, products, calendar, briefings).
- WebSocket event streaming (real-time updates).
- Electron desktop app (main.ts, preload.ts).
- React components (task list, spending dashboard, settings).
- API client (TypeScript, REST + WebSocket).
- Health checks and metrics (database status).

**Deliverables:**
- `nova/infra/api/main.py` (FastAPI app + routes).
- `nova/infra/api/routes/` (finance.py, productivity.py, etc.).
- `nova/infra/api/websocket/` (event streaming).
- `apps/desktop/src/` (Electron + React UI).
- API documentation (OpenAPI schema, examples).
- Integration tests (REST calls → database reads).

**Definition of Done:**
- ✓ REST API starts, serves task list (GET /tasks).
- ✓ WebSocket connection delivers real-time events.
- ✓ Desktop app displays tasks, can filter by status.
- ✓ API is read-only (no mutations from UI, only voice/CLI).
- ✓ Health endpoint reports database status.
- ✓ No circular dependencies (API calls Domains, Domains don't call API).

**Exit Criteria:**
- User can see logged tasks and spending in the desktop app.
- Real-time updates work (add task via voice, see it appear in UI immediately).
- API contract tests pass (read-only, no direct mutations).

**Risks:**
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Electron build is slow/complex | Medium | Low | Use Vite + TypeScript; keep simple; don't optimize initial build. |
| WebSocket connection is unstable | Medium | Medium | Use event listeners; reconnect on disconnect; test connection failures. |
| API is too slow (N+1 queries) | Low | Medium | Use SQL `JOIN` where needed; measure query time; optimize iteratively. |
| Desktop and backend get out of sync | Low | Medium | API is read-only (single source of truth is backend); UI is stateless. |

---

### Milestone 5: Wellness Domain (Habits, Health Tracking)
**Duration:** 2 weeks (Week 17–18)  
**Effort:** ~80 hours

**Goal:**  
Add health and habit tracking as a second domain. Proves parallel domain development is possible; no changes to Core Infrastructure.

**Scope:**
- Wellness domain package (`nova/domains/wellness/`).
- Habit logging and streak calculation.
- Daily habit summaries.
- Tool handlers (log_habit, get_habits_today, get_streak).
- Domain integration tests.

**Deliverables:**
- `nova/domains/wellness/` package (habits.py, tools.py).
- Domain tests (unit + integration).
- API routes (GET /habits, POST /habits/{name}/log).

**Definition of Done:**
- ✓ Habits can be logged and queried.
- ✓ Streak calculation is correct (no gaps).
- ✓ Domain is independent (no cross-domain imports).
- ✓ No changes to Finance, Core, Voice, or API.

**Exit Criteria:**
- User can log a habit, query today's habits, and see streaks.
- Domain isolation is proven (one domain added without changing others).

**Risks:**
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Streak logic is wrong | Low | Medium | Unit test with known edge cases (today, yesterday, month boundary). |
| Domain isolation breaks | Low | High | Code review enforces no cross-domain imports. |

---

### Milestone 6: Productivity Domain (Progress, Planning, Briefings)
**Duration:** 3 weeks (Week 19–21)  
**Effort:** ~120 hours

**Goal:**  
Add daily planning and progress logging. Requires interaction with Finance (tasks), Wellness (habits), and Knowledge service (weather). Proves complex domain interactions work correctly.

**Scope:**
- Productivity domain (`nova/domains/productivity/`).
- Progress logging (work summaries, areas).
- Daily planning logic (prioritize tasks, weather context).
- Morning/evening briefing assembly.
- Tool handlers (log_progress, build_daily_plan, get_briefing).
- Dependency injection (Knowledge service for weather).

**Deliverables:**
- `nova/domains/productivity/` package (progress.py, planner.py, briefing.py, tools.py).
- Domain tests (unit + integration with injected dependencies).
- Briefing golden tests (format stability).

**Definition of Done:**
- ✓ Daily plan is built from open tasks + weather + profile.
- ✓ Morning briefing includes tasks, habits, and weather.
- ✓ Cross-domain reads happen through Memory, not direct imports.
- ✓ Domain isolation is maintained.

**Exit Criteria:**
- User can request a morning briefing and hear a sensible, weather-aware summary.
- Progress is logged and queryable.

**Risks:**
| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Weather API is unavailable | Medium | Low | Graceful degradation (briefing works without weather). |
| Planning logic is fragile | Medium | Low | Test with synthetic data; verify multiple scenarios. |

---

### Milestone 7: Calendar Service & Social Domain
**Duration:** 3 weeks (Week 22–24)  
**Effort:** ~120 hours

**Goal:**  
Integrate Apple Calendar (macOS), add reminders/events domain. Proves external service integration and complex scheduling logic.

**Scope:**
- Calendar service (`nova.services.calendar/`).
- Apple Calendar CRUD via AppleScript.
- NL date/time parsing.
- Social domain (`nova.domains.social/`).
- Reminder creation and due-date checking.
- Event creation and calendar sync.
- Tool handlers.

**Deliverables:**
- `nova/services/calendar/` package (applescript.py, parsing.py).
- `nova/domains/social/` package (reminders.py, events.py, tools.py).
- Calendar integration tests.

**Definition of Done:**
- ✓ User can create calendar events via voice ("schedule meeting at 2pm tomorrow").
- ✓ Reminders are checked and announced.
- ✓ Calendar service is a leaf (reads events, doesn't store them locally).

**Exit Criteria:**
- Calendar event created via Nova appears in Apple Calendar.
- Reminders due today are announced.

---

## 2. PR-BY-PR IMPLEMENTATION PLAN

Each milestone breaks into 4–8 PRs, each independently reviewable and testable.

### Milestone 0: Foundation

#### PR 0.1: Repository structure & schema design
**Files affected:** `docs/`, `.github/`, `nova/core/memory/schema.py`

**Purpose:** Establish folder layout, database schema (all tables, migrations), CI basics.

**Why now:** Foundation must be rock-solid before any code is built on top.

**Complexity:** M (Medium)

**Blocking dependencies:** None

**Expected tests:**
- Schema initialization is idempotent (run twice, same result).
- All 12 tables are created with correct columns.
- Schema version tracking works.

---

#### PR 0.2: Memory public API (all 50+ functions)
**Files affected:** `nova/core/memory/__init__.py`, `nova/core/memory/finance/*.py`, etc.

**Purpose:** Implement all Memory read/write functions for all domains.

**Why now:** Every other layer depends on Memory; API must be complete before integration.

**Complexity:** L (Large) — lots of functions, but each is a simple SQL wrapper.

**Blocking dependencies:** PR 0.1 (schema exists)

**Expected tests:**
- CRUD operations for each domain (tasks, money, habits, reminders, etc.).
- Queries return correctly structured dicts.
- Idempotent operations (insert same row twice = same state).

---

#### PR 0.3: Brain Claude client & contracts
**Files affected:** `nova/core/brain/client.py`, `nova/core/contracts/`

**Purpose:** Anthropic API wrapper, type definitions, MutationEvent dataclass.

**Why now:** Brain and Contracts are foundations; needed for runtime.

**Complexity:** M

**Blocking dependencies:** PR 0.1

**Expected tests:**
- Claude API call succeeds (mock the API).
- Response parsing works (text, tool_use blocks).
- MutationEvent is immutable (frozen dataclass).
- All type annotations are correct (mypy passes).

---

#### PR 0.4: CI/CD & development environment
**Files affected:** `.github/workflows/`, `pyproject.toml`, requirements.txt, README.md

**Purpose:** GitHub Actions (test, lint, type check), local dev setup.

**Why now:** Enable fast iteration and catch regressions early.

**Complexity:** S (Small)

**Blocking dependencies:** PRs 0.1–0.3

**Expected tests:**
- Workflow runs on PR and passes.
- mypy, isort, black all pass.
- Architecture tests catch circular dependencies.

---

### Milestone 1: Core Runtime

#### PR 1.1: Conversation pipeline skeleton
**Files affected:** `nova/core/runtime/conversation.py`, `nova.py` (composition root)

**Purpose:** Basic turn execution: input → Claude → output.

**Why now:** Validate the end-to-end flow before adding complexity.

**Complexity:** M

**Blocking dependencies:** PR 0.3 (Brain), PR 0.2 (Memory for history)

**Expected tests:**
- process_message() returns a ConversationResult.
- Claude is called once per turn.
- Reply text is returned without mutations (yet).

---

#### PR 1.2: MutationEvent generation
**Files affected:** `nova/core/runtime/mutation_builders.py`, `nova/core/contracts/mutation_event.py`

**Purpose:** Deterministic tool_calls → mutations mapping.

**Why now:** Mutations are the atomic unit of change; must be bulletproof.

**Complexity:** M

**Blocking dependencies:** PR 1.1, PR 0.3 (Contracts)

**Expected tests:**
- Same tool calls → same mutations (deterministic).
- Multiple tools per turn → multiple mutations.
- Read-only tools → no mutations.

---

#### PR 1.3: Side-effects & event publishing
**Files affected:** `nova/core/runtime/side_effects.py`, `nova/core/runtime/events.py`

**Purpose:** Mutations → memory writes + WebSocket events (fire-and-forget).

**Why now:** Complete the mutation pipeline.

**Complexity:** M

**Blocking dependencies:** PR 1.2, PR 0.2 (Memory), PR 0.4 (CI enables testing)

**Expected tests:**
- MutationEvents are published before memory writes complete.
- Memory writes are atomic (one transaction per turn).
- Event subscribers receive notifications.
- Failures in one producer don't block others.

---

#### PR 1.4: Memory producers (conversation → memory)
**Files affected:** `nova/core/runtime/memory_producers.py`

**Purpose:** Extract memories from conversations and mutations deterministically.

**Why now:** Semantic memory production is a key part of the pipeline.

**Complexity:** S

**Blocking dependencies:** PR 1.3, PR 0.2 (Memory)

**Expected tests:**
- Conversation exchange produces a memory record.
- Money mutation produces a spending memory.
- Memories have correct tier (short-term, long-term, etc.).

---

#### PR 1.5: Tool dispatch & instrumentation
**Files affected:** `nova/core/runtime/` (tool dispatch), `nova/core/runtime/_tool_instrumentation.py`

**Purpose:** Execute tools via injected handlers, record what was called.

**Why now:** Tools are the interface between Claude and domain logic.

**Complexity:** M

**Blocking dependencies:** PR 1.1

**Expected tests:**
- Tools are called with correct arguments.
- Results are recorded in _tool_events.
- Tool exceptions don't crash the pipeline.
- Tool output is always a string.

---

#### PR 1.6: Error boundaries & recovery
**Files affected:** `nova/core/runtime/conversation.py` (error handling)

**Purpose:** Catch failures at each layer, provide graceful degradation.

**Why now:** Production system must never crash due to a tool failure.

**Complexity:** M

**Blocking dependencies:** PR 1.1–1.5

**Expected tests:**
- Tool exception → turn returns error, app continues.
- Memory write fails → turn continues, error is logged.
- Claude API timeout → turn fails, user hears fallback message.
- Database constraint violation → ignored, turn continues.

---

#### PR 1.7: Background threading (entity extraction)
**Files affected:** `nova/core/runtime/side_effects.py` (thread spawning)

**Purpose:** Spawn entity extraction as background daemon (non-blocking).

**Why now:** Prevent extraction latency from blocking user interaction.

**Complexity:** M

**Blocking dependencies:** PR 1.3 (side effects)

**Expected tests:**
- Background thread spawns without blocking main thread.
- Exceptions in thread are logged but don't affect main thread.
- Thread completion publishes WebSocket events.

---

#### PR 1.8: Integration test: full turn
**Files affected:** `tests/integration/test_conversation_pipeline.py`

**Purpose:** End-to-end test: input → pipeline → memory + events.

**Why now:** Validate entire Milestone 1 before moving to domains.

**Complexity:** M

**Blocking dependencies:** All PR 1.x

**Expected tests:**
- Real transcript processed.
- Claude called, tool executed.
- Mutation created, published, persisted.
- Database state is correct.
- Errors are handled gracefully.

---

### Milestone 2: Finance Domain

#### PR 2.1: Finance domain scaffolding
**Files affected:** `nova/domains/finance/`, Memory for finance tables, contracts for domain codes

**Purpose:** Create Finance package structure, domain isolation.

**Why now:** Validate domain architecture before implementing logic.

**Complexity:** S

**Blocking dependencies:** PR 0.1 (schema), PR 0.3 (Contracts)

**Expected tests:**
- Domain imports only Memory + Contracts.
- No circular dependencies.
- No imports of other domains.

---

#### PR 2.2: Task logic & handlers
**Files affected:** `nova/domains/finance/tasks.py`, `nova/domains/finance/tools.py`

**Purpose:** Task creation, completion, querying. Tool handlers for Claude.

**Why now:** Tasks are core to productivity tracking.

**Complexity:** M

**Blocking dependencies:** PR 2.1, PR 0.2 (Memory API)

**Expected tests:**
- log_task() creates a task with due date.
- complete_task() marks it done.
- get_open_tasks() returns only open tasks.
- Tool handlers return spoken confirmations.

---

#### PR 2.3: Money logic & handlers
**Files affected:** `nova/domains/finance/money.py`, `nova/domains/finance/tools.py`

**Purpose:** Expense/earnings logging, summaries, filtering by category.

**Why now:** Core to financial tracking.

**Complexity:** M

**Blocking dependencies:** PR 2.1, PR 0.2

**Expected tests:**
- Money is logged with type (earned, spent).
- Summaries are calculated correctly (sum, filter by date, category).
- get_spending_summary("Swiggy", "this month") returns correct amount.
- Tool output is clear and spoken-friendly.

---

#### PR 2.4: Product logic & handlers
**Files affected:** `nova/domains/finance/products.py`

**Purpose:** Track product ideas, shipping status, sales.

**Why now:** Nice-to-have but completes the Finance domain.

**Complexity:** S

**Blocking dependencies:** PR 2.1, PR 0.2

**Expected tests:**
- Products can be tracked from idea → shipped → sale.
- Status transitions are correct.

---

#### PR 2.5: Finance → Memory producers
**Files affected:** `nova/core/runtime/memory_producers.py` (Finance-specific logic)

**Purpose:** Mutations (money.logged, task.created) → semantic memories.

**Why now:** Semantic memory production is critical for recall later.

**Complexity:** S

**Blocking dependencies:** PR 1.4 (memory producers), PR 2.2–2.4 (domain logic)

**Expected tests:**
- Money logged → memory record created.
- Memory has correct tier, text, metadata.

---

#### PR 2.6: Finance integration tests
**Files affected:** `tests/integration/test_finance_flow.py`, `tests/golden/test_finance_output.py`

**Purpose:** Full e2e Finance flows, output format stability.

**Why now:** Validate domain works end-to-end before moving on.

**Complexity:** M

**Blocking dependencies:** PR 2.1–2.5, PR 1.8 (full pipeline works)

**Expected tests:**
- "Add task buy milk tomorrow" → task appears in DB.
- "How much Swiggy this month?" → correct summary.
- Output format is stable (golden tests).

---

### Milestone 3: Voice Integration

#### PR 3.1: Audio I/O & RMS gating
**Files affected:** `nova/services/voice/audio.py`

**Purpose:** Microphone input, noise gate to prevent false transcriptions.

**Why now:** Voice is the main user interface; gating is critical for reliability.

**Complexity:** M

**Blocking dependencies:** None (leaf service)

**Expected tests:**
- Audio chunks are captured from microphone.
- RMS calculation is correct.
- Threshold gating prevents silent chunks from being transcribed.

---

#### PR 3.2: Wake word detection
**Files affected:** `nova/services/voice/wake_word.py`

**Purpose:** Detect "rai" (or custom word) in overlapping windows.

**Why now:** Always-on listening depends on this.

**Complexity:** M

**Blocking dependencies:** PR 3.1

**Expected tests:**
- Wake word detected in clean audio.
- False positives on silence are minimized (tunable threshold).
- RMS gating prevents hallucination.

---

#### PR 3.3: Whisper transcription
**Files affected:** `nova/services/voice/transcription.py`

**Purpose:** Load Whisper model, transcribe audio.

**Why now:** Core observation mechanism.

**Complexity:** S

**Blocking dependencies:** None (leaf)

**Expected tests:**
- Model loads successfully (or downloads if needed).
- Transcription output is correct for clear speech.
- Model doesn't get reloaded per call (cached).

---

#### PR 3.4: Text-to-speech
**Files affected:** `nova/services/voice/tts.py`

**Purpose:** Speak confirmations via macOS `say`.

**Why now:** User feedback is essential.

**Complexity:** S

**Blocking dependencies:** None

**Expected tests:**
- speak() executes `say` command.
- Text is read aloud (manual verification).

---

#### PR 3.5: Voice service public API & composition
**Files affected:** `nova/services/voice/__init__.py`, `nova.py` (main)

**Purpose:** Wire Voice service into the app, start the run loop.

**Why now:** Complete the voice integration.

**Complexity:** M

**Blocking dependencies:** PR 3.1–3.4, PR 1.8 (process_message works)

**Expected tests:**
- Wake word polling doesn't block the main thread.
- process_message() is called for each detected command.

---

#### PR 3.6: Main run loop & composition root
**Files affected:** `nova.py`, `nova/core/runtime/__init__.py`

**Purpose:** Boot sequence, dependency injection, clean shutdown.

**Why now:** Tie everything together; user can start the app.

**Complexity:** M

**Blocking dependencies:** All Milestone 0, 1, 2, 3.1–3.5

**Expected tests:**
- App starts, initializes DB, loads Whisper, injects dependencies.
- Run loop is responsive (wake word polling never hangs).
- Ctrl+C shuts down cleanly.

---

#### PR 3.7: Voice integration e2e test
**Files affected:** `tests/e2e/test_voice_command.py`

**Purpose:** Full scenario: user speaks "add task", hears confirmation.

**Why now:** Validate entire voice path works.

**Complexity:** M

**Blocking dependencies:** PR 3.6, PR 2.6

**Expected tests:**
- Sample audio is recorded or provided.
- Transcription → process_message() → tool execution.
- Confirmation is spoken.
- Task appears in DB.

---

### Milestone 4: Desktop UI & REST API

#### PR 4.1: REST API scaffolding
**Files affected:** `nova/infra/api/main.py`

**Purpose:** FastAPI app with CORS, health check, basic middleware.

**Why now:** Foundation for all API endpoints.

**Complexity:** S

**Blocking dependencies:** None (new package)

**Expected tests:**
- App starts on port 8000.
- Health endpoint returns OK.

---

#### PR 4.2: API routes (Finance, Wellness, Productivity)
**Files affected:** `nova/infra/api/routes/*.py`

**Purpose:** GET endpoints for tasks, money, habits, progress (read-only).

**Why now:** Let product team see user data.

**Complexity:** M

**Blocking dependencies:** PR 4.1, PR 0.2 (Memory), PR 2.x (Finance domain)

**Expected tests:**
- GET /tasks returns all open tasks (JSON).
- GET /spending?month=2026-07 returns summary.
- Filters work (status, date range, category).
- Response schema matches OpenAPI spec.

---

#### PR 4.3: WebSocket event streaming
**Files affected:** `nova/infra/api/websocket/`, `nova/core/runtime/events.py` (wire WebSocket subscribers)

**Purpose:** Real-time event push to clients (new task → UI updates immediately).

**Why now:** Real-time feedback is critical for UX.

**Complexity:** M

**Blocking dependencies:** PR 4.1, PR 1.8 (events are published)

**Expected tests:**
- WebSocket connection accepts subscribers.
- Event is published → all subscribers receive it.
- Connection drop is handled gracefully.

---

#### PR 4.4: Electron scaffolding & React setup
**Files affected:** `apps/desktop/src/`, `apps/desktop/package.json`

**Purpose:** Boilerplate Electron + React app, asset build.

**Why now:** Foundation for UI.

**Complexity:** S

**Blocking dependencies:** None (new package)

**Expected tests:**
- App builds with Vite.
- Main window opens.
- DevTools work.

---

#### PR 4.5: React components (task list, dashboard)
**Files affected:** `apps/desktop/src/renderer/`, `apps/desktop/src/api/client.ts`

**Purpose:** Basic UI for tasks, spending, habits (read-only).

**Why now:** Product team can see user workflows.

**Complexity:** M

**Blocking dependencies:** PR 4.2 (API routes exist), PR 4.4 (Electron scaffolding)

**Expected tests:**
- Components render without errors.
- API calls are made (mock backend).
- Data is displayed in correct format.

---

#### PR 4.6: API client (TypeScript, REST + WebSocket)
**Files affected:** `apps/desktop/src/api/client.ts`

**Purpose:** Type-safe API client for React components.

**Why now:** Type safety prevents UI/API mismatches.

**Complexity:** S

**Blocking dependencies:** PR 4.2, PR 4.3 (API routes + WebSocket exist)

**Expected tests:**
- Client calls correct endpoints.
- Response is correctly typed.
- WebSocket auto-reconnects on disconnect.

---

#### PR 4.7: Real-time event listening in React
**Files affected:** `apps/desktop/src/renderer/hooks/`

**Purpose:** React hooks for event subscription (task added → UI updates).

**Why now:** Complete the real-time feedback loop.

**Complexity:** S

**Blocking dependencies:** PR 4.3 (WebSocket), PR 4.5 (React components)

**Expected tests:**
- Hook subscribes to events on mount.
- UI updates when events are received.
- Unsubscribe on unmount prevents memory leaks.

---

#### PR 4.8: API documentation & contract tests
**Files affected:** `docs/api/`, `tests/contracts/test_api_contract.py`

**Purpose:** OpenAPI spec, contract tests (ensure API doesn't break clients).

**Why now:** API is now stable; document and protect it.

**Complexity:** S

**Blocking dependencies:** PR 4.2, 4.3

**Expected tests:**
- OpenAPI schema is correct.
- All routes are documented.
- Contract tests verify backwards compatibility.

---

### Milestone 5: Wellness & Additional Domains

#### PR 5.1–5.3: Wellness domain (same pattern as Finance)
**Complexity:** M per PR

**Blocking dependencies:** All Milestone 0, 1, 2, 3, 4 (domains are added independently)

Same pattern as Finance PRs (scaffolding, logic, integration tests).

---

#### PR 6.1–6.4: Productivity domain (more complex due to Knowledge service dependency)
**Complexity:** M–L per PR

---

#### PR 7.1–7.4: Calendar service + Social domain
**Complexity:** M–L per PR

---

## 3. REPOSITORY EVOLUTION

### End of Milestone 0: Foundation

```
nova/
├── docs/
│   ├── architecture/
│   │   ├── NOVA_CORE_RUNTIME_SPECIFICATION_v1.md
│   │   ├── NOVA_ENGINEERING_SPECIFICATION_v1.md
│   │   └── ...
│   └── README.md
├── nova/
│   └── core/
│       ├── __init__.py
│       ├── memory/
│       │   ├── __init__.py (50+ functions)
│       │   ├── schema.py (all v1.0 tables)
│       │   ├── _connection.py
│       │   └── [finance, wellness, productivity, social, ai_context]/
│       ├── brain/
│       │   ├── __init__.py
│       │   ├── client.py (Claude API wrapper)
│       │   ├── history.py
│       │   └── tools.py (stub ASSISTANT_TOOLS)
│       └── contracts/
│           ├── __init__.py
│           ├── mutation_event.py
│           ├── entities.py
│           └── validators/
├── tests/
│   ├── unit/
│   │   ├── test_memory.py
│   │   ├── test_brain.py
│   │   └── test_contracts.py
│   └── conftest.py
├── .github/
│   └── workflows/
│       ├── test.yml
│       └── lint.yml
├── nova.py (skeleton, no logic yet)
├── pyproject.toml
├── requirements.txt
└── README.md
```

**Packages added:** 4 (Core: runtime, memory, brain, contracts) — stub only.

---

### End of Milestone 1: Runtime

```
nova/
├── nova/
│   ├── core/
│   │   └── runtime/
│   │       ├── __init__.py
│   │       ├── conversation.py (process_message)
│   │       ├── mutation_event.py
│   │       ├── mutation_builders.py (deterministic tool→mutation)
│   │       ├── side_effects.py (mutations→memory+events)
│   │       ├── events.py (event bus)
│   │       ├── memory_producers.py
│   │       └── _tool_instrumentation.py
├── tests/
│   ├── unit/ (new tests for runtime)
│   ├── integration/
│   │   └── test_conversation_pipeline.py
│   └── contracts/
│       └── test_runtime_memory_contract.py
└── (rest as before)
```

**Packages added:** Runtime (core layer) — fully functional.

---

### End of Milestone 2: Finance Domain

```
nova/
├── nova/
│   ├── core/ (unchanged)
│   └── domains/
│       └── finance/
│           ├── __init__.py
│           ├── tasks.py
│           ├── money.py
│           ├── products.py
│           └── tools.py
├── tests/
│   ├── unit/domains/
│   │   └── test_finance.py
│   ├── integration/
│   │   └── test_finance_flow.py
│   ├── golden/
│   │   └── test_finance_output.py
│   └── contracts/
│       └── test_domain_isolation.py
└── (rest as before)
```

**Packages added:** Domains/finance (first domain).

**Documents added:** Finance domain documentation.

---

### End of Milestone 3: Voice

```
nova/
├── nova/
│   ├── core/ (unchanged)
│   ├── services/
│   │   └── voice/
│   │       ├── __init__.py
│   │       ├── audio.py
│   │       ├── wake_word.py
│   │       ├── transcription.py
│   │       └── tts.py
│   └── domains/ (unchanged)
├── tests/
│   ├── unit/services/
│   │   └── test_voice.py
│   └── e2e/
│       └── test_voice_command.py
├── nova.py (main run loop, composition root)
└── (rest as before)
```

**Packages added:** Services/voice (first service, leaf).

**New executable:** nova.py is now fully runnable.

---

### End of Milestone 4: Desktop & API

```
nova/
├── nova/
│   ├── core/ (unchanged)
│   ├── services/ (unchanged)
│   ├── domains/ (unchanged)
│   └── infra/
│       └── api/
│           ├── __init__.py
│           ├── main.py (FastAPI app)
│           ├── routes/
│           │   └── finance.py (and others)
│           └── websocket/
│               └── manager.py
├── apps/
│   ├── backend/ (nova.py + nova/)
│   └── desktop/
│       ├── src/
│       │   ├── main.ts
│       │   ├── preload.ts
│       │   ├── renderer/
│       │   │   ├── App.tsx
│       │   │   ├── pages/
│       │   │   ├── components/
│       │   │   └── hooks/
│       │   └── api/
│       │       └── client.ts
│       ├── package.json
│       ├── vite.config.ts
│       └── tsconfig.json
├── tests/
│   ├── contracts/
│   │   └── test_api_contract.py
│   └── (rest as before)
└── docs/
    └── api/
        └── openapi.yaml
```

**Packages added:** Infra/api (read-only REST + WebSocket).

**New app:** Desktop (Electron + React).

---

### End of Milestone 5+: Additional Domains

```
nova/
├── nova/
│   ├── core/ (unchanged)
│   ├── services/
│   │   └── (add knowledge, calendar, automation as needed)
│   └── domains/
│       ├── finance/ (complete)
│       ├── wellness/ (new)
│       ├── productivity/ (new)
│       ├── social/ (new)
│       └── ai_context/ (new)
└── (rest evolves naturally)
```

**Pattern:** Each new domain is a new folder with no changes to existing code.

---

## 4. DEVELOPMENT ORDER RATIONALE

### Why Core Infrastructure First?

1. **Every layer depends on Memory.** Get the storage abstraction right; iterate early.
2. **Runtime orchestration is fixed.** The conversation pipeline won't change; build it once.
3. **Brain is a thin client to Claude.** Implement early; it's mostly delegation to Claude.
4. **Contracts define the vocabulary.** Shared by all packages; must be complete before code.

### Why Finance Domain Before Voice?

1. **Finance logic is pure.** No external dependencies, easy to test and iterate.
2. **Proves the domain architecture.** If Finance doesn't work, Voice won't either.
3. **Domains are the main value.** Get one working completely before adding others.

### Why Voice After Domains?

1. **Voice is the interface, not the core.** It wraps an already-working conversation pipeline.
2. **No rework needed.** Once Finance works, Voice just calls process_message().
3. **Hardware dependencies.** Voice needs tuning; do it last to avoid rework.

### Why API + Desktop After Voice?

1. **Support, not core.** The app works on the command line; API is nice-to-have.
2. **API surface is read-only.** Once domains exist, API is straightforward to add.
3. **Desktop is purely UI.** Doesn't change backend; can be built in parallel.

### Why Additional Domains Last?

1. **Pattern is proven.** Finance proves the domain architecture; others follow the same pattern.
2. **No core changes needed.** Each domain is independent; parallelizable.
3. **Team can work in parallel.** Once the pattern is known, multiple engineers can own different domains.

---

## 5. TESTING STRATEGY PER MILESTONE

### Milestone 0: Foundation

**Unit tests:**
- Memory: CRUD operations for each domain.
- Brain: Claude API call + response parsing (mocked API).
- Contracts: Type definitions, immutability, serialization.

**Contract tests:**
- No circular dependencies.
- Only Brain imports anthropic.
- Only Memory imports sqlite3.

**Golden tests:**
- Schema initialization (snapshot of created tables).

**Coverage target:** >90% (core layer must be bulletproof).

---

### Milestone 1: Runtime

**Unit tests:**
- Conversation turn: input → output (no side effects).
- Mutation generation: tool results → mutations (deterministic).
- Event publishing: events are published in correct order.

**Integration tests:**
- Full turn: transcript → mutations → memory writes.
- Tool dispatch: handlers are called with correct args.
- Error boundaries: failures don't crash the pipeline.

**Contract tests:**
- Runtime doesn't import Domains.
- Memory writes are called via public API only.

**Golden tests:**
- Mutation event shape (structure stability).
- Event publication order.

**Coverage target:** >95% (runtime is the core orchestration).

---

### Milestone 2: Finance Domain

**Unit tests:**
- Task logic: create, complete, query (all paths).
- Money logic: logging, summaries, filtering (all calculations).
- Tool handlers: return spoken-friendly text.

**Integration tests:**
- Full finance flow: voice command → database state.
- Multiple tools in one turn: all mutations are created.
- Cross-turn consistency: restarting the app shows same data.

**Contract tests:**
- Finance only calls Memory (no other domains).
- Mutations are consistent (same input → same output).

**Golden tests:**
- Tool output format (spoken summaries).
- Mutation event shape for Finance operations.

**Coverage target:** >85% (domains are more complex but less critical than core).

---

### Milestone 3: Voice

**Unit tests:**
- RMS gating: silence is filtered correctly.
- Wake word detection: "rai" is detected in audio.
- Transcription: audio → text is correct.

**Integration tests:**
- Full voice flow: record → process → confirm.
- False positive rate (tuned empirically, acceptable ~1–5%).
- False negative rate (e.g., edge of window, acceptable ~5–10%).

**Golden tests:**
- Wake word detection accuracy (known audio samples).

**Coverage target:** >80% (hardware and transcription model are external; focus on integration).

---

### Milestone 4: API + Desktop

**Unit tests:**
- API routes: correct SQL queries, correct response shape.
- React components: render without errors (snapshot tests).
- TypeScript client: correct types, correct API calls.

**Integration tests:**
- API call → correct data returned.
- WebSocket event → UI updates.
- UI state matches backend state.

**Contract tests:**
- API is read-only (no mutations).
- WebSocket events match schema.

**Golden tests:**
- API response schema (snapshot).
- UI layout (visual regression).

**Coverage target:** >80% (API is straightforward; focus on contract tests).

---

### Milestone 5+: Additional Domains

Same pattern as Milestone 2 (Finance).

---

## 6. DOCUMENTATION ROADMAP

### Week 1 (Milestone 0 start)

- [ ] **Developer Setup Guide** (`docs/developer/GETTING_STARTED.md`)
  - Python environment, dependencies, database setup, running tests.

- [ ] **Architecture Overview** (`docs/architecture/OVERVIEW.md`)
  - One-page summary of the five layers, data flow diagram.

### Week 2 (Milestone 0 complete)

- [ ] **Memory Layer Documentation** (`docs/architecture/MEMORY_API.md`)
  - All 50+ public functions, usage examples, schema diagram.

- [ ] **API Design Doc** (`docs/architecture/API_CONTRACTS.md`)
  - Tool handler signature, Memory producer signature, context provider signature.

### Week 6 (Milestone 1 complete)

- [ ] **Runtime Specification** (already frozen)
  - Reference for developers working on runtime changes.

- [ ] **MutationEvent Documentation** (`docs/contracts/MUTATION_EVENTS.md`)
  - What events are created, when, and why.

### Week 9 (Milestone 2 complete)

- [ ] **Domain Development Guide** (`docs/developer/ADDING_DOMAIN.md`)
  - Step-by-step: new domain folder, Memory tables, tools, tests, integration.

- [ ] **Finance Domain Walkthrough** (`docs/domains/FINANCE.md`)
  - Concrete example of how Finance domain is organized.

### Week 12 (Milestone 3 complete)

- [ ] **Voice Integration Guide** (`docs/services/VOICE.md`)
  - How to adjust wake word sensitivity, add new voice commands, tune RMS threshold.

- [ ] **Running the App** (`docs/operations/RUNNING.md`)
  - How to start Nova, where logs go, common troubleshooting.

### Week 16 (Milestone 4 complete)

- [ ] **REST API Documentation** (`docs/api/ENDPOINTS.md`)
  - OpenAPI schema, curl examples, WebSocket message format.

- [ ] **Desktop App Guide** (`docs/ui/DESKTOP_APP.md`)
  - How to build and run Electron app, component structure.

### Week 21 (Milestone 5 complete)

- [ ] **Dependency Rules Checklist** (`docs/architecture/DEPENDENCY_CHECKLIST.md`)
  - 60+ rules, how to verify them locally.

- [ ] **Technical Debt Register** (`docs/TECHNICAL_DEBT.md`)
  - Known issues, prioritization, fix time estimates.

---

## 7. RISK REGISTER

### Critical Risks (Probability: High, Impact: High)

#### Risk 1: Memory schema is incomplete
**Probability:** Medium | **Impact:** High | **Severity:** ★★★★★

**Description:** Foundation phases misses a critical table or column, forcing rework after domains are built.

**Mitigation:**
- Schema review against all 12+ tables in spec (PR 0.1).
- Iterate early with synthetic data (Milestone 0 itself).
- Add schema migration tests (idempotent, version tracking).

**Rollback:** Migrations are reversible if they're additive. No rollback if existing columns are modified.

---

#### Risk 2: Runtime orchestration is fragile
**Probability:** Medium | **Impact:** High | **Severity:** ★★★★☆

**Description:** Conversation pipeline fails under concurrent access, error conditions, or edge cases.

**Mitigation:**
- Synchronous pipeline only (no concurrency bugs in Milestone 1).
- Comprehensive integration tests (Milestone 1, PR 1.8).
- Error boundary tests for all paths (PR 1.6).

**Rollback:** Rewrite conversation.py if fundamentally broken. Time: ~3 days.

---

#### Risk 3: Brain API contracts are wrong
**Probability:** Medium | **Impact:** High | **Severity:** ★★★★☆

**Description:** Tool handler signature, response parsing, or context provider contract is wrong, causing cascading failures.

**Mitigation:**
- Design contracts first (PR 0.3).
- Write contract tests before implementation (PR 1.5).
- Mock Claude API early (don't rely on real API).

**Rollback:** Redesign contracts, update all callers. Time: ~1 week.

---

#### Risk 4: Domain isolation is violated
**Probability:** Low | **Impact:** High | **Severity:** ★★★★☆

**Description:** Finance domain imports Wellness, or Services import each other, breaking architecture.

**Mitigation:**
- Architecture tests in CI (PR 0.4).
- Code review enforces rules (60+ invariants).
- Import validation script (detect violations automatically).

**Rollback:** Remove bad import, refactor. Time: ~1 day per violation.

---

### High Risks (Probability: Medium, Impact: Medium)

#### Risk 5: Wake word detection misses or false-triggers
**Probability:** High | **Impact:** Medium | **Severity:** ★★★☆☆

**Description:** RMS threshold tuning doesn't converge; either misses commands or triggers on silence.

**Mitigation:**
- Tune empirically (Milestone 3, PR 3.1).
- Accept some false positives/negatives initially (~5% acceptable).
- Fallback: user can press Enter (revert to Phase 1 behavior temporarily).

**Rollback:** Adjust threshold, accept lower accuracy initially, improve over time.

---

#### Risk 6: Whisper transcription quality is poor
**Probability:** Low | **Impact:** Medium | **Severity:** ★★☆☆☆

**Description:** Faster-whisper doesn't transcribe accurately in realistic environments.

**Mitigation:**
- Test with real audio (Milestone 3, PR 3.3).
- If accuracy is <90%, consider other models (but stays in scope).
- Fallback: user can text commands (no voice required).

**Rollback:** Switch transcription library, acceptance of reduced accuracy.

---

#### Risk 7: Claude API cost exceeds budget
**Probability:** Low | **Impact:** Medium | **Severity:** ★★★☆☆

**Description:** Prompt engineering or context size is inefficient, causing unexpected costs.

**Mitigation:**
- Use Haiku model initially (cost ~$0.01 per turn).
- Monitor token usage (PR 1.1, add logging).
- Cap context to 4000 tokens (Architecture spec).
- Test with real usage patterns early (Milestone 2).

**Rollback:** Switch to smaller context, more retrieval steps, or local LLM fallback.

---

#### Risk 8: Desktop app is slow or unstable
**Probability:** Medium | **Impact:** Medium | **Severity:** ★★★☆☆

**Description:** Electron + React app has N+1 queries, connection issues, or crashes.

**Mitigation:**
- Keep API read-only (single database, no consistency issues).
- Measure latency (Milestone 4, PR 4.2).
- Use React hooks for subscriptions (Milestone 4, PR 4.7).
- Graceful degradation (app works without real-time updates).

**Rollback:** Revert to command-line interface, skip Desktop app for initial release.

---

### Medium Risks (Probability: Medium, Impact: Low)

#### Risk 9: Testing is too slow
**Probability:** Medium | **Impact:** Low | **Severity:** ★★☆☆☆

**Description:** Full test suite takes >10 minutes, blocking iteration.

**Mitigation:**
- Keep unit tests fast (mock all external deps).
- Integration tests are separate (run before PR merge).
- Parallel test execution (pytest with -n flag).
- Profile slowest tests (Milestone 1).

**Rollback:** Skip flaky tests temporarily, focus on critical paths.

---

#### Risk 10: Dependency tree grows unmanageable
**Probability:** Low | **Impact:** Low | **Severity:** ★☆☆☆☆

**Description:** Too many third-party libraries, version conflicts, long installation times.

**Mitigation:**
- Minimal dependencies (Whisper, Anthropic SDK, FastAPI, SQLite only).
- Explicit version pins (requirements.txt, lock file).
- Quarterly dependency audit.

**Rollback:** Pin to known good versions, remove unused libraries.

---

## 8. SUCCESS METRICS

### Milestone 0: Foundation

**Technical:**
- ✓ All 12 tables created, schema migrations pass.
- ✓ All 50+ Memory functions implemented and tested.
- ✓ Architecture tests pass (no circular deps, isolated core).
- ✓ Type checking passes (mypy strict).
- ✓ CI/CD pipeline is green.

**Product:**
- No user-facing metrics (infrastructure only).

**Success:** Foundation is solid, zero rework needed by downstream milestones.

---

### Milestone 1: Runtime

**Technical:**
- ✓ process_message() works end-to-end.
- ✓ Mutations are deterministic (same input → same mutations).
- ✓ Error boundaries prevent crashes (all exception paths tested).
- ✓ MutationEvents are published correctly.
- ✓ Integration tests cover all major paths.

**Product:**
- The engine is proven; no user interaction yet (backend only).

**Success:** Core orchestration is bulletproof; ready for domains.

---

### Milestone 2: Finance Domain

**Technical:**
- ✓ Domain isolation verified (no cross-domain imports).
- ✓ All Finance operations (CRUD, queries) are correct.
- ✓ Tool handlers return sensible confirmations.
- ✓ Golden tests verify output format stability.

**Product:**
- ✓ User can log tasks/money via simulated voice.
- ✓ User can query summaries (realistic turn duration: 2–5 seconds).
- ✓ Data is persisted and survives app restart.

**Success:** First domain is complete; proven architecture works for real workflows.

---

### Milestone 3: Voice

**Technical:**
- ✓ Wake word detection works (tune RMS threshold).
- ✓ False positive rate <5%, false negative <10%.
- ✓ Transcription accuracy >85% on clear speech.
- ✓ TTS latency <2 seconds.

**Product:**
- ✓ "Rai, add task" works hands-free (full cycle: ~5–10 seconds).
- ✓ Confirmation is spoken.
- ✓ No terminal needed (background daemon optional, UI not required).

**Success:** Nova is now interactive via voice. Core value is proven.

---

### Milestone 4: Desktop UI

**Technical:**
- ✓ REST API is complete (all read endpoints).
- ✓ WebSocket streaming delivers real-time events.
- ✓ Electron app builds and starts.
- ✓ React components render without errors.

**Product:**
- ✓ User can see tasks/spending in desktop app.
- ✓ Real-time updates work (add task via voice, see it in UI).
- ✓ No direct UI mutations (all changes come from voice/voice).

**Success:** Product team can see user workflows visually. Additional users can be onboarded via UI.

---

### Milestone 5+: Additional Domains

**Technical:**
- ✓ New domains follow established pattern (no changes to Core).
- ✓ Domains are isolated (no cross-domain imports).
- ✓ All unit + integration tests pass.

**Product:**
- ✓ Each domain adds value (Habits increase retention, Planning drives daily engagement, etc.).
- ✓ User can interact with multiple domains in one session (multi-domain turns work).

**Success:** Prove that Nova can scale to >5 domains without architectural rework.

---

## 9. STOP CONDITIONS

Development should stop and architecture should be revisited if any of these are observed:

### Code Smell: Circular Dependencies

**Condition:** A→B and B→A (even transitively).

**Example:** Finance imports Productivity to access task priorities; Productivity imports Finance to log money.

**Response:** Refactor immediately. Introduce a common package (shared logic in Contracts or AI Context) and break the cycle. Time: ~2–3 days. Cannot proceed to next milestone until fixed.

---

### Code Smell: Services Import Each Other

**Condition:** Voice imports Automation, or Automation imports Knowledge.

**Example:** Voice wants to speak using Automation's TTS (instead of own implementation).

**Response:** This violates the "leaf service" principle. Services must be independently usable. Refactor: either move TTS logic to a shared service, or ensure Services only have self-contained behavior. Time: ~1 week. Cannot proceed until fixed.

---

### Code Smell: Domain Imports Another Domain

**Condition:** Finance imports Wellness to check if a habit was completed, instead of querying Memory.

**Example:** `from nova.domains.wellness import get_habit_streak`.

**Response:** Violates domain isolation. Refactor: domains read data through Memory only, not direct imports. Time: ~2–3 days. Cannot proceed until fixed.

---

### Code Smell: Core Imports Domain or Service

**Condition:** Runtime imports Finance, or Brain imports Voice.

**Example:** `from nova.domains.finance import TOOL_HANDLERS`.

**Response:** Core is foundational; it must never depend on Domains/Services. Refactor: inject dependencies. Time: ~2–4 days. Cannot proceed until fixed.

---

### Performance Regression: Turn Latency >15 seconds

**Condition:** Conversation turn takes >15 seconds to complete.

**Example:** Brain API call + tool execution + memory write + event publishing exceeds 15 seconds.

**Response:** Measure each component. Likely culprits: slow Brain API (network latency, prompt bloat), slow Memory queries (missing index), slow tool handlers (inefficient logic). Profile and optimize locally. If unresolvable, escalate to architecture review (might indicate fundamental design issue).

---

### Memory Bloat: Database >100MB with <10K rows

**Condition:** Per-entity size suggests query inefficiency.

**Example:** Each money entry takes 10KB instead of expected 100 bytes.

**Response:** Check for blob data (images, large metadata). Review schema for denormalization gone wrong. This should be impossible; indicates schema mistake. Fix immediately.

---

### Test Coverage Drop: <80% in Core Infrastructure

**Condition:** Core packages (Memory, Brain, Runtime, Contracts) have <80% coverage.

**Example:** After Milestone 2, coverage is 75%.

**Response:** Add missing tests. Core must be bulletproof. Target: >90%. Cannot proceed until restored.

---

### Architectural Debt Accumulation: >5 Blockers

**Condition:** Architecture tests block merge for >1 week.

**Example:** Multiple "this violates Rule 3" violations piling up.

**Response:** Stop feature development. Spend 1 sprint fixing violations. Schedule architecture review. Ensure team understands the rules.

---

### Test Flakiness: >20% of tests are flaky

**Condition:** Tests fail randomly without code changes.

**Example:** Race conditions in background thread tests, or API timeouts.

**Response:** Immediately investigate. Flaky tests hide real bugs. Fix root cause (remove race conditions, increase timeouts, reduce external API dependency). May require refactoring (e.g., remove background thread complexity).

---

### Claude API Failures: >5% of turns fail due to API issues

**Condition:** Rate limiting, timeouts, or errors affect >5% of turns.

**Example:** "Sorry, I couldn't process that" happens 1 in 20 times.

**Response:** Review error boundaries (PR 1.6). Implement request queuing or exponential backoff. May require switching models or reducing context size. This is acceptable short-term (accept degradation); escalate if persistent.

---

### Schema Migration Failure: Migration can't be applied to existing database

**Condition:** `init_db()` fails on a user's existing nova.db (e.g., schema version mismatch).

**Example:** User is on v0.2, tries to upgrade to v0.5; migration v0.3→v0.4 assumes a column that doesn't exist.

**Response:** Migrations must be idempotent. This indicates a bug in migration logic. Fix immediately; write test to prevent recurrence. May require data migration script to fix existing databases.

---

## 10. FINAL CHRONOLOGICAL ROADMAP

### Week 1–2: Milestone 0 (Foundation)
**Effort:** 1 engineer, 80 hours
- PR 0.1: Schema + repo structure
- PR 0.2: Memory public API
- PR 0.3: Brain + Contracts
- PR 0.4: CI/CD setup

**Checkpoint:** All architecture tests pass. Memory can CRUD all entities. Brain can call Claude.

---

### Week 3–6: Milestone 1 (Runtime)
**Effort:** 1 engineer, 160 hours
- PR 1.1: Conversation pipeline
- PR 1.2: Mutation generation
- PR 1.3: Side-effects + event publishing
- PR 1.4: Memory producers
- PR 1.5: Tool dispatch
- PR 1.6: Error boundaries
- PR 1.7: Background threading
- PR 1.8: Integration tests

**Checkpoint:** Full turn works (transcript→reply). Mutations are created and persisted.

---

### Week 7–9: Milestone 2 (Finance)
**Effort:** 1 engineer, 120 hours
- PR 2.1: Domain scaffolding
- PR 2.2: Tasks
- PR 2.3: Money
- PR 2.4: Products
- PR 2.5: Memory producers
- PR 2.6: Integration + golden tests

**Checkpoint:** "Add task", "How much Swiggy?", "Task done" all work. Data persists.

---

### Week 10–12: Milestone 3 (Voice)
**Effort:** 1 engineer, 120 hours
- PR 3.1: Audio I/O
- PR 3.2: Wake word
- PR 3.3: Transcription
- PR 3.4: TTS
- PR 3.5: Voice service integration
- PR 3.6: Main run loop
- PR 3.7: E2E test

**Checkpoint:** User can speak "Rai, add task" and hear confirmation. Hands-free interaction.

---

### Week 13–16: Milestone 4 (Desktop + API)
**Effort:** 1 engineer, 160 hours (or 2 engineers in parallel)
- PR 4.1: REST API scaffolding
- PR 4.2: API routes
- PR 4.3: WebSocket
- PR 4.4: Electron setup
- PR 4.5: React components
- PR 4.6: TypeScript client
- PR 4.7: Real-time hooks
- PR 4.8: API docs + contract tests

**Checkpoint:** Desktop app shows tasks and spending. Real-time updates work.

---

### Week 17–18: Milestone 5 (Wellness)
**Effort:** 1 engineer, 80 hours
- PR 5.1: Domain scaffolding
- PR 5.2: Habit logic
- PR 5.3: Integration tests

**Checkpoint:** Habits can be logged, streaks are calculated, displayed in UI.

---

### Week 19–24: Milestone 6 (Productivity)
**Effort:** 1 engineer, 120 hours
- PR 6.1: Domain scaffolding
- PR 6.2: Progress logging
- PR 6.3: Planning logic
- PR 6.4: Integration tests

**Checkpoint:** Daily briefing includes tasks, habits, weather (if Knowledge service is implemented).

---

### Week 25–27: Milestone 7 (Calendar + Social)
**Effort:** 1 engineer, 120 hours
- PR 7.1: Calendar service
- PR 7.2: Social domain scaffolding
- PR 7.3: Reminders
- PR 7.4: Integration tests

**Checkpoint:** User can create calendar events, set reminders, all synced with Apple Calendar.

---

### Weeks 28–52: Phase 2 Features (Semantic Memory, Graph, Reflection, etc.)
**Effort:** Scales with team (2–4 engineers)

As team grows, add engineers to:
- **Platform team:** Brain context engine, Learning layer, reflection job.
- **Domains teams:** Commerce domain, Analytics domain.
- **Services team:** Background syncing, notification aggregation.
- **QA/DevOps:** E2E testing, production monitoring, release automation.

---

## SUMMARY: Timeline & Team Scale

| Weeks | Phase | Solo Effort | Team Scale | Status |
|---|---|---|---|---|
| 1–2 | Foundation | 80h | 1 engineer | Core infrastructure |
| 3–6 | Runtime | 160h | 1 engineer | Orchestration layer |
| 7–9 | Finance | 120h | 1 engineer | First domain |
| 10–12 | Voice | 120h | 1 engineer | Voice interface |
| 13–16 | Desktop + API | 160h | 2 engineers (parallel) | Product visibility |
| 17–18 | Wellness | 80h | 1 engineer | Second domain |
| 19–24 | Productivity | 120h | 2 engineers (parallel) | Daily planning |
| 25–27 | Calendar + Social | 120h | 2 engineers (parallel) | External integration |
| **Weeks 1–27 Total** | **v1.0 MVP** | **~960 hours (24 weeks)** | **1–2 engineers** | **Production-ready** |
| 28–52 | Phase 2 features | — | 3–4 engineers | Semantic memory, Graph, Learning |

---

## ASSUMPTIONS & CONSTRAINTS

### Assumptions

1. **Single senior engineer initially.** Can make architectural decisions, code review self, iterate fast.
2. **No external dependencies beyond frozen architecture.** Claude API, Whisper, SQLite, FastAPI, Electron only.
3. **macOS only.** AppleScript, Whisper on CPU, Electron native APIs.
4. **Internet available.** Claude API calls, model downloads, but no cloud storage.
5. **User has microphone access.** For voice interaction; graceful degradation if denied.
6. **No multi-user initially.** Single local database, no sync, no cloud backup.

### Constraints

1. **Architecture frozen.** No major redesigns during v1.0 implementation. Bug fixes only.
2. **Feature freeze.** Scope is defined by Milestones 0–7; no new domains added until v1.5.
3. **No optimization.** First-pass implementation prioritizes correctness and simplicity over speed.
4. **No early hardening.** Security and deployment hardening come in v1.2+.
5. **Continuous integration only.** Deploy weekly; no canary or staged rollouts yet.

---

## NEXT STEPS

1. **Approve this roadmap.** (Stakeholder sign-off.)
2. **Start Milestone 0.** (Day 1: repository structure, begin schema design.)
3. **Weekly progress reviews.** (Every Friday: what shipped, what's blocked, adjust plan as needed.)
4. **Monthly architecture reviews.** (Check invariants, architectural debt, risk register.)
5. **Retrospectives at each milestone.** (Learn, adjust estimates, improve team processes.)

---

## DOCUMENT CONTROL

**Version:** 1.0  
**Status:** Master Engineering Roadmap (Frozen with Nova Core v1.0)  
**Last Updated:** July 6, 2026  
**Authority:** Principal Software Architect  
**Audience:** Development team, stakeholders, architects  

**Next Review:** When Milestone 0 is complete (Week 2–3).

**Maintenance:** Update weekly with actual progress, blockers, and revised estimates.

---

**END OF NOVA IMPLEMENTATION ROADMAP v1**

This document is the single source of truth for Nova Core v1.0 implementation. Follow it rigorously, adapt it pragmatically.
