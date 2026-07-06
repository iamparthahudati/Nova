# NOVA ENGINEERING SPECIFICATION v1

**Status:** Engineering Organization Standard — Frozen Nova Core v1.0  
**Scope:** Codebase organization, package boundaries, and growth strategy for 5+ years  
**Abstraction Level:** Architecture — how code should be organized, not how it executes  
**Audience:** All engineers; read before writing code in Nova  
**Authority:** Principal Software Architect (Codebase Organization)

---

## 0. Executive Summary

Nova's codebase is organized around five tiers: **Core Infrastructure** (runtime, memory, LLM interface), **Services** (leaf behaviors like Voice, Calendar), **Domains** (business logic like Finance, Wellness), **Tools** (developer experience), and **Tests** (quality gates by layer).

**Core principle:** Clear ownership. Every package has one responsibility. Packages never depend sideways; only upward through public interfaces.

**Growth strategy:** New domains are added as packages without modifying existing code. No core framework changes needed. Services are stable and reused.

---

## 1. PACKAGE BOUNDARIES

### 1.1 Package Taxonomy

Nova's codebase has **three kinds of packages**:

| Kind | Definition | Examples | Depends on | May be depended on by |
|---|---|---|---|---|
| **Core Infrastructure** | Foundation systems (event bus, database abstraction, LLM interface) | `nova.core.runtime`, `nova.core.memory`, `nova.core.brain`, `nova.core.contracts` | Python stdlib, third-party libs (sqlite3, lancedb, anthropic) | Services, Domains, Tests |
| **Services** (Leaf) | Reusable behaviors that own their own domain (Voice, Calendar, Weather) | `nova.services.voice`, `nova.services.calendar`, `nova.services.automation` | Core Infrastructure only (via dependency injection) | Core Infrastructure (injected), Tests, Composition Root |
| **Domains** | Business logic + persistence for a user-facing capability (Finance, Wellness, Productivity) | `nova.domains.finance`, `nova.domains.wellness`, `nova.domains.productivity` | Core Infrastructure, Services (injected), Domains (constrained) | Tests, Composition Root, API facade |

### 1.2 Core Infrastructure Packages

**nova.core.runtime** — Conversation pipeline orchestration

- Owns: MutationEvent definition, conversation turn execution, tool dispatch.
- Does not own: Any service behavior, any domain logic.
- Public API: `process_message(transcript) → ConversationResult`, `publish(channel, event_type, payload)`.
- Callers: `nova.main` (composition root), API server, tests.
- Never calls: Any service or domain directly (services injected via TOOL_HANDLERS dict).

**nova.core.memory** — Storage abstraction layer

- Owns: All database I/O, schema management, query patterns for all entities.
- Does not own: Business logic, persistence decisions (domains decide what to persist, memory executes).
- Public API: `add_task()`, `get_task_by_id()`, `add_money()`, `get_money_since()`, `create_entity()`, `link_entities()`, etc.
- Callers: All domains, services, tools, tests.
- Never calls: Any domain or service (receives data from callers, returns data; pure query/command interface).

**nova.core.brain** — Claude API and reasoning interface

- Owns: Claude routing, system prompt assembly, conversation history, entity extraction, reflection reasoning.
- Does not own: Any service (services don't import Brain).
- Public API: `route(transcript, handlers, history)`, `run_entity_extraction()`, `run_reflection_job()`, `set_calendar_source()`.
- Callers: Runtime (via `process_message`), Services (via injected reasoning calls), Domains (read-only reflection), Tests.
- Dependency injection contract: Callers inject `calendar.get_events`, `context_providers`, tool handlers. Brain never imports those modules.

**nova.core.contracts** — Type definitions, schema validators, AI contracts

- Owns: Immutable data structures (MutationEvent, ConversationResult, ContextProvider), JSON schemas for Claude input/output, enum definitions (entity types, operation types, domain codes).
- Does not own: Implementation, business logic.
- Public API: Type definitions, constants, validators, serialization helpers.
- Callers: All packages (common vocabulary).
- Never calls: Anything (pure data definitions).

---

### 1.3 Service Packages (Leaves)

Services are **leaves** — they depend on Core Infrastructure only, never on Domains or other Services.

**nova.services.voice** — Microphone, wake word, transcription, TTS

- Owns: Audio I/O, Whisper model lifecycle, RMS gating, TTS synthesis.
- Does not own: What to do with transcription, any domain logic.
- Public API: `load_model()`, `speak(text)`, `poll_wake_word()`, `record_command()`.
- Callers: Runtime (voice command path), Tests.
- Depends on: Core Infrastructure (only for dependency injection if needed), Python audio libs (pyaudio, scipy).
- Never calls: Memory, Brain, Domains (receives handlers/callbacks injected).

**nova.services.calendar** — Apple Calendar read/write via AppleScript

- Owns: Calendar event CRUD, NL date/time parsing, AppleScript interaction.
- Does not own: Any scheduling logic, any domain decision about what events mean.
- Public API: `create_event(title, date, time)`, `get_events(day)`, `parse_date(text)`, `parse_time(text)`.
- Callers: Runtime tool dispatch, Brain (context provider, injected), Tests.
- Depends on: Core Infrastructure, pyobjc (macOS-specific).
- Never calls: Memory (no persistence), Brain, Domains.

**nova.services.automation** — App launching, notifications, WhatsApp, Pomodoro

- Owns: macOS app control, notification display, WhatsApp API interaction, Pomodoro timer.
- Does not own: Decision of what to automate (domains decide).
- Public API: `open_app(name)`, `notify(title, message)`, `send_whatsapp_message(contact, text)`, `start_pomodoro(minutes, speak_callback, on_complete_callback)`.
- Callers: Runtime tool dispatch, Domains (via tool handlers), Tests.
- Depends on: Core Infrastructure, whatsapp-web.py, macOS APIs.
- Never calls: Memory (immutable), Brain (reasoning), Calendar (no cross-service calls).

**nova.services.knowledge** — Weather, RSS, GitHub, reflection trigger

- Owns: Weather API reads, RSS feed parsing, GitHub notification polling, reflection job orchestration (not reasoning — Brain owns that).
- Does not own: Profile updates, entity extraction (Brain owns both).
- Public API: `get_weather(location)`, `get_rss_updates()`, `get_github_notifications()`, `run_reflection()`, `should_run_reflection()`, `handle_journal(text)`.
- Callers: Runtime (scheduled checks), Tests, Domains (journal entry handler).
- Depends on: Core Infrastructure, external APIs (OpenWeatherMap, GitHub).
- Never calls: Memory persistence (journal writes go through Domain), Brain reasoning (reflection calls Brain, not vice versa).

---

### 1.4 Domain Packages

Domains own **business logic + persistence** for a capability. Each domain defines its entities, mutations, and tools.

**nova.domains.finance** — Tasks, money, products, spending analysis

- Owns: Task entity (create, update, complete), Money entity (expense logging, summaries), Product entity (idea tracking, shipping, sales logging).
- Persists via: `nova.core.memory` public API (`add_task()`, `add_money()`, etc.) — Finance never opens database directly.
- Public API: `log_task(text, due)`, `complete_task(task_id)`, `log_money(type, amount, note)`, `log_product(name, store, price)`, `ship_product(id)`, `log_sale(id)`, `get_spending_summary(period)`.
- Callers: Runtime tool dispatch, Tests, API facade.
- Depends on: Core Infrastructure (Memory, Contracts, Runtime for event publishing).
- Never calls: Other Domains, Services directly. (Calendar is injected by composition root as a tool handler input, not imported.)

**nova.domains.wellness** — Habits, health tracking

- Owns: Habit entity (logging, streak tracking, today's summary).
- Persists via: `nova.core.memory` public API.
- Public API: `log_habit(name)`, `get_habits_today()`, `get_habit_streak(habit_name)`.
- Callers: Runtime tool dispatch, Tests, API facade.
- Depends on: Core Infrastructure.
- Never calls: Finance, Productivity, or other Domains directly.

**nova.domains.productivity** — Task progress, planning, prioritization

- Owns: Progress entity (work summaries), daily/weekly planning, task prioritization logic.
- Persists via: `nova.core.memory` public API.
- Public API: `log_progress(note, area)`, `build_daily_plan()`, `build_morning_briefing()`, `build_evening_wrapup()`, `prioritize_tasks()`.
- Callers: Runtime (scheduled briefings), tool dispatch, Tests, API facade.
- Depends on: Core Infrastructure, `nova.services.knowledge` (injected weather provider).
- Never calls: Finance, Wellness directly. (Knowledge is injected as a parameter, not imported.)

**nova.domains.social** — Reminders, events, people tracking

- Owns: Reminder entity (creation, due checking), Event entity (linked to Calendar), Person entity (contact tracking).
- Persists via: `nova.core.memory` public API.
- Public API: `save_reminder(text, remind_date, remind_time)`, `get_due_reminders()`, `create_event(title, date, time)`, `get_events(day)`.
- Callers: Runtime tool dispatch, Tests, API facade.
- Depends on: Core Infrastructure, `nova.services.calendar` (injected as tool handler context).
- Never calls: Finance, Wellness, Productivity directly.

**nova.domains.ai_context** — Profile observations, learning signals

- Owns: Profile entity (user understanding), learning-driven insights and nudges (Phase 2.9+).
- Persists via: `nova.core.memory` public API (`replace_profile_observations()`, `remember(source_type="insight")`).
- Public API: `get_profile_observations()`, `update_profile_from_reflection(observations)` (called by Brain after reflection), `get_insights()` (called by Productivity/API).
- Callers: Brain (reflection, context assembly), Productivity (briefings), Tests, API facade.
- Depends on: Core Infrastructure.
- Never calls: Other Domains directly (context is derived from their data, not requested).

---

### 1.5 Data Ownership Matrix

| Entity | Package | Persistence | Who creates | Who reads | Who deletes |
|---|---|---|---|---|
| Task | Finance | `memory.tasks` table | Finance (user command via tool) | Finance, Productivity, Tests | Finance (user explicit) |
| Money | Finance | `memory.money` table | Finance | Finance, API, Tests | (never; append-only) |
| Product | Finance | `memory.products` table | Finance | Finance, API, Tests | Finance (user explicit) |
| Habit | Wellness | `memory.habits` table | Wellness | Wellness, Productivity, API, Tests | (never; append-only) |
| Progress | Productivity | `memory.progress` table | Productivity | Productivity, API, Tests | (never; append-only) |
| Reminder | Social | `memory.reminders` table | Social | Social, Runtime (due checks), Tests | Social (acknowledged) |
| Profile | AI Context | `memory.profile` table | Brain (via reflection), AI Context | Brain (context), Productivity, API, Tests | AI Context (explicit replace) |
| Conversation | Brain | `memory.conversation_history` table | Brain (after tool execution) | Brain (history assembly), Tests | (never; append-only) |
| Memory | Memory infra | `memory.memories` table (Phase 2.1+) | Runtime (memory producers) | Brain (recall), all Domains (indirectly via recall), Tests | Memory infra (soft delete) |
| Entity | Memory infra | `memory.entities` + `memory.edges` (Phase 2.6+) | Brain (extraction) | Brain (context), API, Tests | (never in v1.0; only soft delete in future) |

---

### 1.6 Dependency Graph (Complete)

```
                        ┌──────────────────────────────┐
                        │    Composition Root          │
                        │    (nova/main.py)            │
                        │  (Wires all dependencies)    │
                        └───────────────┬──────────────┘
                                        │
                ┌───────────────────────┼───────────────────────┐
                │                       │                       │
                │                       │                       │
        ┌───────▼────────┐     ┌────────▼────────┐    ┌─────────▼──────┐
        │ Runtime        │     │ Services        │    │ Domains        │
        │ (orchestration)│     │ (leaves)        │    │ (business logic│
        └────┬──────┬────┘     └──────┬──────┬───┘    │  + persistence)│
             │      │                 │      │        └──┬──┬──┬──┬────┘
             │      │                 │      │           │  │  │  │
        ┌────▼──┬───▼──────────────┐  │      │      ┌────┘  │  │  └──────┐
        │       │                  │  │      │      │       │  │         │
        │       │                  │  │      │      ▼       ▼  ▼         ▼
        │       │                  │  │      │   Finance Wellness Productivity Social
        │       │                  │  │      │
    ┌───▼──┬───▼──┬────────┬──────▼──┘   ┌───▼──┬────────┬──────────┐
    │      │      │        │            │      │        │          │
    │      │      │        │            │      │        │          │
    ▼      ▼      ▼        ▼            ▼      ▼        ▼          ▼
  Brain Memory Contracts Events      Voice Calendar Automation Knowledge
  (LLM)  (DB)   (types)   (bus)      (audio)(macOS)  (apps)      (web)

  ───────────────────────────────────────────────────────────────────────
  Core Infrastructure Layer
  ───────────────────────────────────────────────────────────────────────
```

**Edge annotations:**

- **Runtime → Memory:** Direct calls to queries (not through Domain).
- **Runtime → Brain:** Direct routing call.
- **Runtime → Contracts:** Type definitions.
- **Domains → Memory:** Public API only (never internal modules).
- **Domains → Brain:** Reflection call only (AI Context → Brain).
- **Brain → Services:** Via dependency injection (never direct import).
- **Services → Core:** One-way (never import back).
- **Services → Services:** NEVER (no horizontal calls).
- **Domains → Domains:** NEVER (no cross-domain calls).

---

## 2. MODULE OWNERSHIP

### 2.1 nova.core.runtime

**File structure:**
```
nova/core/runtime/
├── __init__.py                    [public API exports]
├── conversation.py                [turn pipeline: process_message()]
├── mutation_event.py              [MutationEvent dataclass definition]
├── mutation_builders.py           [deterministic: mutations ← tool calls]
├── mutation_chat.py               [deterministic: mutations ← tool execution]
├── side_effects.py                [finalize_mutations(), entity extraction spawn]
├── domain_events.py               [mutation → WebSocket event mapping]
├── events.py                      [event bus implementation]
└── (internal) _tool_instrumentation.py  [tool execution recording]
```

**Responsibilities (public):**

1. **Conversation turn execution.** `process_message(transcript)` is the single entry point for all user input.
2. **Tool dispatch wiring.** Accepts `TOOL_HANDLERS` dict (dependency injection) and routes Claude's tool calls.
3. **Mutation production.** Converts tool results to MutationEvent records deterministically.
4. **Side-effect orchestration.** Publishes WebSocket events, kicks off entity extraction, coordinates memory production.
5. **Event publishing.** Central event bus for all domain events.

**Responsibilities (internal):**

1. Tool execution instrumentation (recording what was called).
2. Mutation mapping logic (deterministic transformation).
3. Background thread spawning (extraction, reflection).

**Public interfaces:**

```python
def process_message(
    transcript: str,
    conversation_id: Optional[str] = None,
    *,
    speak_output: bool = False,
    emit_events: bool = True,
) -> ConversationResult:
    """Execute one conversation turn. Returns reply + tool calls + errors."""

def publish(channel: Literal["chat", "events"], event_type: str, payload: dict) -> None:
    """Emit event to all subscribers. Fire-and-forget, best-effort."""

def subscribe(handler: EventHandler) -> None:
    """Register callback for all publish() calls."""
```

**Private internals:**

- `_tool_events: list` — Turn-scoped recording buffer.
- `_instrument(name, handler)` — Wrapper for tool execution recording.
- `tool_calls_to_mutations(tools_called)` — Pure function, could be public but implementation detail.
- `_journal_mutations(tools_called)` — Domain-specific mutation logic (could move to `nova.domains.ai_context`).

**What other packages may call:**

- `nova.main` (composition root) — creates the event bus, wires handlers.
- `nova.services.voice` — calls `process_message()` with voice transcript.
- `nova.infra.api_server` — calls `process_message()` with chat API input, subscribes to events for WebSocket push.
- Tests — direct calls to `process_message()`, event subscription.

**What it may call:**

- `nova.core.memory` — no direct calls in runtime (decisions call memory via tool handlers).
- `nova.core.brain` — yes, one direct call: `brain.route()` inside `process_message()`.
- `nova.core.contracts` — yes, imports `MutationEvent`.
- Domain tools — no direct calls (injected via `TOOL_HANDLERS` dict).
- Services — no direct calls (injected via `TOOL_HANDLERS` dict).

**What it absolutely cannot call:**

- Any domain module directly (domains are injected as tool handlers).
- Any service module directly (services are injected).
- Database queries (only through Memory public API, not directly).

---

### 2.2 nova.core.memory

**File structure:**
```
nova/core/memory/
├── __init__.py                    [public API: add_task, get_task_by_id, ...]
├── schema.py                      [init_db(), schema definitions]
├── _connection.py                 [SQLite connection context manager]
│
├── finance/
│   ├── tasks.py                   [add_task, get_task_by_id, complete_task, ...]
│   ├── money.py                   [add_money, get_money_since, get_totals, ...]
│   └── products.py                [add_product, ship_product, log_sale, ...]
├── wellness/
│   └── habits.py                  [log_habit, get_habits_today, ...]
├── productivity/
│   └── progress.py                [add_progress, get_progress_since, ...]
├── social/
│   └── reminders.py               [add_reminder, get_due_reminders, ...]
├── ai_context/
│   ├── profile.py                 [get_profile_observations, replace_profile_observations]
│   └── conversation.py            [add_turn, get_history, ...]
│
├── semantic/
│   ├── memories.py                [remember(), recall() — Phase 2.1+]
│   └── embeddings.py              [EmbeddingProvider — Phase 2.1+]
├── graph/
│   ├── entities.py                [create_entity, get_entity, ...  — Phase 2.6+]
│   └── edges.py                   [link_entities, related_entities, ...]
│
└── (internal)
    └── _utils.py                  [query helpers, connection pooling stubs]
```

**Responsibilities (public):**

1. **Persistence abstraction.** Only module that opens `nova.db`. Public API hides SQLite complexity.
2. **Schema versioning.** `init_db()` handles migrations; all schema changes are here.
3. **Entity CRUD.** Every domain has query functions (tasks, money, habits, etc.).
4. **Semantic storage.** Memories, embeddings, graph tables (Phase 2+).

**Responsibilities (internal):**

1. Connection management (context manager pattern).
2. Query optimization (indexes, prepared statements).
3. Schema migration logic.

**Public interfaces (by domain):**

```python
# Finance
def add_task(text: str, due: Optional[str]) -> dict: ...
def complete_task(task_id: int) -> None: ...
def get_task_by_id(task_id: int) -> dict: ...
def get_open_tasks() -> list[dict]: ...
def get_done_tasks_since(date: str) -> list[dict]: ...

# Wellness
def log_habit(name: str) -> dict: ...
def get_habits_today() -> list[dict]: ...
def get_habit_streak(habit_name: str) -> int: ...

# Semantic (Phase 2.1+)
def remember(text: str, source_type: str, tier: str, metadata: dict) -> None: ...
def recall(query: str, k: int, filters: dict) -> list[dict]: ...

# Graph (Phase 2.6+)
def create_entity(entity_type: str, name: str, attributes: dict) -> str: ...
def link_entities(from_id: str, to_id: str, relation_type: str, weight: float) -> None: ...
def related_entities(entity_id: str, relation_type: Optional[str], depth: int) -> list[dict]: ...
```

**Private internals:**

- `_connection.connect()` — SQLite context manager.
- `_utils.query_builder()` — Common query patterns.
- All raw SQL (never exposed; only through domain-specific functions).

**What other packages may call:**

- All Domains — directly (Memory is infrastructure, not a domain).
- Brain — for conversation history, profile reads (read-only).
- Tests — direct API calls.
- API facade — for data retrieval (read-only).

**What it may call:**

- SQLite3 (Python stdlib).
- LanceDB (Phase 2.1+, semantic index).
- Python utilities (dataclasses, json).

**What it absolutely cannot call:**

- Any domain module (receives data from callers, not the reverse).
- Brain (Memory is read-only; no reasoning).
- Services (Memory has no dependencies on Voice, Calendar, etc.).
- Runtime (Memory is called from Runtime, not vice versa; would create cycle).

---

### 2.3 nova.core.brain

**File structure:**
```
nova/core/brain/
├── __init__.py                    [public API: route, run_entity_extraction, ...]
├── client.py                      [Anthropic API wrapper]
├── prompts.py                     [system prompt construction — pre-Phase 2.8]
│
├── context_engine/                [Phase 2.8+ — context assembly]
│   ├── __init__.py
│   ├── providers/
│   │   ├── recent_activity.py
│   │   ├── semantic_memory.py    [Phase 2.1+]
│   │   ├── knowledge_graph.py    [Phase 2.6+]
│   │   ├── open_tasks.py
│   │   ├── calendar.py           [injected calendar.get_events]
│   │   ├── profile.py
│   │   └── conversation.py
│   ├── assembler.py              [ranking, budgeting, formatting]
│   └── _deduplication.py         [remove duplicate context]
│
├── history.py                     [conversation history management]
├── reflection.py                  [weekly reflection job]
├── extraction.py                  [entity/relationship extraction — Phase 2.7+]
├── extraction_contract.py         [extraction output schema — Phase 2.7+]
├── reinforcement.py               [memory access count updates — Phase 2.8+]
├── tools.py                       [ASSISTANT_TOOLS definition]
│
└── (internal)
    ├── _anthropic_wrapper.py      [API call error handling]
    └── _response_parser.py        [Claude output parsing]
```

**Responsibilities (public):**

1. **Claude routing.** `route(transcript, handlers, history)` is the single Claude API call point.
2. **Conversation history.** Management of last N turns (loaded from Memory at startup).
3. **Reflection and extraction.** Domain reasoning jobs that call Claude.
4. **Context assembly.** (Phase 2.8+) Gather, rank, format context for system prompt.
5. **Dependency injection.** Accept external data sources (Calendar, Memory queries, context providers).

**Responsibilities (internal):**

1. API error handling and retries.
2. Response parsing (tool calls, text extraction).
3. Token budgeting and context trimming.
4. Entity extraction batch management.

**Public interfaces:**

```python
def route(
    transcript: str,
    handlers: dict[str, Callable],
    history: list[dict],
) -> str:
    """Call Claude API with context, return reply. Dispatch tools via handlers."""

def run_reflection_job() -> str:
    """Weekly reflection. Returns summary string."""

def run_entity_extraction() -> str:
    """Batch extract entities/relationships. Returns summary string."""

def set_calendar_source(getter: Callable[[], list]) -> None:
    """Inject Calendar service's read function into context engine."""

class History:
    def add_turn(self, transcript: str, reply: str) -> None: ...
    def get(self) -> list[dict]: ...
    def clear(self) -> None: ...
```

**Private internals:**

- `_build_system_prompt()` — Pre-Phase 2.8; replaced by context_engine in 2.8+.
- `_call_claude_api()` — Raw API wrapper.
- `_parse_tool_use()` — Extract tool blocks from Claude response.
- Context providers (Phase 2.8+) — implementations of specific data gathering.

**What other packages may call:**

- Runtime — `route()` from `process_message()`.
- Domains (AI Context) — `run_reflection_job()` (read-only; Brain updates profile via Memory API, not direct Domain call).
- Background jobs — `run_entity_extraction()`.
- Tests — direct API calls.

**What it may call:**

- `nova.core.memory` — no direct calls in v1.0. Phase 2.8+ context engine will call through injected providers.
- `nova.core.contracts` — tool definitions.
- `anthropic.Anthropic()` — ONLY service that calls Claude API.

**What it absolutely cannot call:**

- Any domain module (decision making is Claude's, not Brain's logic).
- Services directly (services are injected via tool handlers or dependency injection, never imported).
- Runtime (would create circular dependency).
- Database queries directly (only through injected Memory methods or context providers that call Memory).

---

### 2.4 nova.core.contracts

**File structure:**
```
nova/core/contracts/
├── __init__.py                    [exports all types below]
├── mutation_event.py              [MutationEvent dataclass]
├── conversation.py                [ConversationResult, ContextProvider types]
├── ai_contracts.py                [JSON schemas for Claude input/output]
│
├── entities.py                    [Entity types: Task, Money, Habit, ...]
├── operations.py                  [Operation enums: "create", "update", "complete"]
├── domain_codes.py                [Domain identifiers, entity type enums]
├── error_codes.py                 [Error code enum for standardized errors]
│
└── validators/
    ├── __init__.py
    ├── mutation_validator.py      [MutationEvent.event_type validation]
    ├── extraction_validator.py    [Entity extraction output validation — Phase 2.7+]
    └── reflection_validator.py    [Reflection output validation]
```

**Responsibilities (public):**

1. **Type definitions.** Immutable dataclasses, enums, TypedDicts for all domain objects.
2. **Validation schemas.** JSON schemas for Claude I/O contracts.
3. **Constants.** Shared enums (domains, operations, error codes).

**Responsibilities (internal):**

1. Validator implementations (for contract checking).

**Public interfaces:**

```python
# From mutation_event.py
@dataclass(frozen=True)
class MutationEvent:
    event_type: str
    entity_type: str
    operation: str
    entity: dict
    metadata: dict = field(default_factory=dict)

# From entities.py
@dataclass
class Task:
    id: int
    text: str
    due: Optional[str]
    completed: bool
    created_at: str

# From operations.py
class Operation(Enum):
    CREATE = "create"
    UPDATE = "update"
    COMPLETE = "complete"
    DELETE = "delete"
```

**Private internals:**

- Validator logic.
- Schema builder functions.

**What other packages may call:**

- Every package (common vocabulary).

**What it may call:**

- Python stdlib (dataclasses, enum, json).

**What it absolutely cannot call:**

- Any other Nova package (would create circular dependency).
- External libraries (except Python stdlib).

---

## 3. DEPENDENCY RULES (50+)

### 3.1 Fundamental Rules (Never Broken)

**Rule 1:** No package may contain multiple responsibilities.
- Finance owns Tasks, Money, Products only — not Progress, Habits, or Reminders.
- Violation: Finance imports Wellness module or vice versa.

**Rule 2:** Services never import Domains.
- Voice never imports Finance, Wellness, Productivity.
- Violation: `from nova.domains.finance import log_money` inside Voice module.

**Rule 3:** Domains never import other Domains.
- Finance never imports Wellness, Productivity, or Social.
- Violation: Finance queries Wellness habit streaks directly (must go through shared context, not direct).

**Rule 4:** No sideways dependencies between Services.
- Voice never imports Calendar or Automation.
- Violation: Voice calls `automation.start_pomodoro()` directly (if Pomodoro were a service).
- Exception: All services may import Core Infrastructure.

**Rule 5:** Domains never import Services directly.
- Productivity never imports Calendar or Weather services.
- Violation: `from nova.services.calendar import create_event`.
- Rationale: Services are injected as tool handlers or dependency-injected functions.

**Rule 6:** Brain is the only module that imports `anthropic` package.
- No domain imports `anthropic`.
- No service imports `anthropic` (Claude calls go through Brain).
- Violation: Finance module calls Claude directly to analyze spending trends.

**Rule 7:** Memory is the only module that imports `sqlite3`.
- No domain writes directly to database.
- No service touches the database.
- Violation: Finance module opens `nova.db` connection directly.

**Rule 8:** No package may import Runtime directly except composition root.
- Domains don't import `nova.core.runtime`.
- Services don't import `nova.core.runtime`.
- Violation: Finance module calls `publish_mutation_event()` directly.
- Rationale: Mutations are created, then passed to Runtime. Runtime orchestrates publication.

**Rule 9:** Runtime never imports Domains or Services.
- Runtime does not contain domain logic (conversions, formatting, calculations).
- Violation: Runtime imports Finance to do spending analysis.
- Rationale: Runtime is orchestration only; logic lives in Domains.

**Rule 10:** Contracts is the common vocabulary; every package may import it.
- Contracts never imports any other Nova package.
- Violation: Contracts imports Finance to re-export entity types.
- Rationale: Contracts is a leaf; it's the foundation everyone stands on.

### 3.2 Caller/Callee Relationships (By Package)

**nova.core.runtime may call:**

11. `nova.core.memory` (queries, history add).
12. `nova.core.brain` (`route()` call).
13. `nova.core.contracts` (types).
14. `nova.infra.events` (publish).

**nova.core.runtime may NOT call:**

15. Any `nova.domains.*` module.
16. Any `nova.services.*` module.
17. `nova.infra.api_server` (one-way: API calls Runtime, not vice versa).

**nova.core.memory may call:**

18. Python stdlib (sqlite3, json, dataclasses).
19. `nova.core.contracts` (types).
20. Third-party libs (lancedb, numpy for embeddings).

**nova.core.memory may NOT call:**

21. Any `nova.domains.*` module.
22. Any `nova.services.*` module.
23. `nova.core.brain` (Brain reads Memory, not vice versa).
24. `nova.core.runtime`.
25. Any package beyond Core Infrastructure + vendors.

**nova.core.brain may call:**

26. `nova.core.memory` (Phase 2.8+ context engine calls Memory via injected providers).
27. `nova.core.contracts` (types).
28. `anthropic` SDK (ONLY package that does).

**nova.core.brain may NOT call:**

29. Any `nova.domains.*` module directly.
30. Any `nova.services.*` module directly (injected via dependency injection, never imported).
31. `nova.core.runtime` (would create circular dependency).

**Domains may call:**

32. `nova.core.memory` (public API only: `add_task()`, `get_task_by_id()`, etc.).
33. `nova.core.contracts` (types).
34. `nova.core.runtime` for publishing events? NO — Rule 8.

**Domains may NOT call:**

35. Other Domains directly (cross-domain queries go through Memory, not direct imports).
36. Services directly (injected as tool handlers).
37. `nova.core.brain` (except AI Context, which calls Brain's reflection job via public API).
38. `nova.core.runtime` (events propagate up, not down).
39. Database directly (`nova.core.memory` is the boundary).

**Services may call:**

40. `nova.core.contracts` (types).
41. Python stdlib + third-party libs (audio, macOS APIs, HTTP clients).

**Services may NOT call:**

42. Any `nova.domains.*` module.
43. Other Services.
44. `nova.core.brain` (calls go through injection).
45. `nova.core.memory` (if a service needs to persist, it's not really a leaf service).
46. `nova.core.runtime` (orchestration is upward, not downward).

**Composition Root (`nova.main`) may call:**

47. All Core Infrastructure packages.
48. All Services (to inject them).
49. All Domains (to wire them).
50. Runtime (to start the app).

### 3.3 Data Flow Rules

**Rule 51:** Tool results are always strings, never structured objects.
- Tool handlers return a confirmation string spoken to the user.
- Structured data (what was created, what changed) is captured in MutationEvent.

**Rule 52:** Domains persist only through Memory public APIs.
- No domain has its own database file.
- No domain uses LanceDB directly (Memory manages embeddings).

**Rule 53:** Context assembly is read-only.
- Context providers never modify state.
- Context providers return data for Claude; Claude changes are not auto-saved.

**Rule 54:** Events flow from Services/Domains upward to Runtime, never downward.
- A Domain publishes a MutationEvent (upward).
- Runtime publishes a WebSocket event (to subscribers).
- A subscriber (API) calls domains (downward), but domains don't spontaneously call API.

**Rule 55:** Injection points are documented in public API.
- When a package accepts a callback or function, it's explicitly named a parameter.
- Runtime's `process_message(…, handlers: dict)` documents that handlers are injected.
- Brain's `set_calendar_source(getter)` documents the injected dependency.

### 3.4 New Package Rules

**Rule 56:** When a new Domain is added, zero existing code must change.
- Composition root wires the domain (change allowed).
- Tool handlers are registered (change allowed).
- No existing domain/service/runtime code is modified.

**Rule 57:** When a new Service is added, it must be a leaf (no other services depend on it).

**Rule 58:** When an existing package grows beyond one responsibility, it must be split.
- If a package owns both Business Logic AND Persistence, separate them (logic in Domain, persistence in Memory).
- If a package owns Query Logic AND Rendering, separate them (query in Memory, rendering in API/UI).

### 3.5 Architectural Debt Rules

**Rule 59:** No package may use a "quick shortcut" to bypass architectural boundaries.
- If a Domain really needs to call another Domain, the dependency must be explicit (added to the dependency graph).
- No `import` statements hidden in functions or conditional blocks to "sneak around" the graph.

**Rule 60:** Circular dependencies are a code smell that forces redesign.
- If A → B and B → A (even transitively), the architecture is broken.
- Fix: Introduce a third package C that both A and B depend on (usually contracts or common logic).

---

## 4. FOLDER STRUCTURE

### 4.1 Directory Layout (Complete)

```
nova/
├── README.md                                  [quick start, link to docs]
├── .env.example                              [template for environment variables]
├── .gitignore
│
├── docs/
│   ├── architecture/
│   │   ├── ARCHITECTURE_v1.md                [frozen: Phase 1 service definitions]
│   │   ├── ARCHITECTURE_v2.md                [design: Phase 2 additions]
│   │   ├── AI_CONTRACTS.md                   [Claude I/O contracts]
│   │   ├── NOVA_CORE_RUNTIME_SPECIFICATION_v1.md  [runtime behavior]
│   │   └── NOVA_ENGINEERING_SPECIFICATION_v1.md   [this file]
│   ├── design/
│   │   ├── ROADMAP.md                        [5-year vision, phases]
│   │   └── DESIGN_DECISIONS.md               [ADRs and justifications]
│   ├── operations/
│   │   ├── DEPLOYMENT.md                     [deployment, configuration]
│   │   ├── MONITORING.md                     [observability, logging]
│   │   └── TROUBLESHOOTING.md                [common issues and fixes]
│   └── developer/
│       ├── GETTING_STARTED.md                [dev environment setup]
│       ├── TESTING_GUIDE.md                  [how to write tests]
│       ├── PACKAGE_TEMPLATE.md               [template for new packages]
│       └── DEPENDENCY_GRAPH.md               [visual dependency diagram]
│
├── apps/
│   ├── backend/                              [Python backend, all services/domains]
│   │   ├── nova.py                           [entry point, composition root]
│   │   ├── nova.db                           [SQLite database (git-ignored)]
│   │   │
│   │   ├── nova/
│   │   │   ├── __init__.py
│   │   │   │
│   │   │   ├── core/
│   │   │   │   ├── __init__.py               [exports: runtime, memory, brain, contracts]
│   │   │   │   ├── runtime/                  [conversation pipeline + event bus]
│   │   │   │   │   ├── __init__.py           [public: process_message, publish, subscribe]
│   │   │   │   │   ├── conversation.py       [turn execution]
│   │   │   │   │   ├── mutation_event.py     [MutationEvent dataclass]
│   │   │   │   │   ├── mutation_builders.py  [deterministic: mutations ← tool calls]
│   │   │   │   │   ├── side_effects.py       [post-mutation orchestration]
│   │   │   │   │   ├── domain_events.py      [mutation → WebSocket event mapping]
│   │   │   │   │   └── events.py             [event bus]
│   │   │   │   │
│   │   │   │   ├── memory/                   [storage abstraction: only DB access]
│   │   │   │   │   ├── __init__.py           [public API: add_task, get_task_by_id, ...]
│   │   │   │   │   ├── schema.py             [init_db(), schema migrations]
│   │   │   │   │   ├── _connection.py        [SQLite context manager (private)]
│   │   │   │   │   ├── finance/              [Tasks, Money, Products queries]
│   │   │   │   │   │   ├── tasks.py
│   │   │   │   │   │   ├── money.py
│   │   │   │   │   │   └── products.py
│   │   │   │   │   ├── wellness/             [Habits queries]
│   │   │   │   │   │   └── habits.py
│   │   │   │   │   ├── productivity/         [Progress queries]
│   │   │   │   │   │   └── progress.py
│   │   │   │   │   ├── social/               [Reminders queries]
│   │   │   │   │   │   └── reminders.py
│   │   │   │   │   ├── ai_context/           [Profile, Conversation queries]
│   │   │   │   │   │   ├── profile.py
│   │   │   │   │   │   └── conversation.py
│   │   │   │   │   ├── semantic/             [Memories, Embeddings — Phase 2.1+]
│   │   │   │   │   │   ├── memories.py
│   │   │   │   │   │   └── embeddings.py
│   │   │   │   │   └── graph/                [Entities, Edges — Phase 2.6+]
│   │   │   │   │       ├── entities.py
│   │   │   │   │       └── edges.py
│   │   │   │   │
│   │   │   │   ├── brain/                    [Claude interface + reasoning]
│   │   │   │   │   ├── __init__.py           [public: route, run_entity_extraction, ...]
│   │   │   │   │   ├── client.py             [Anthropic API wrapper]
│   │   │   │   │   ├── tools.py              [ASSISTANT_TOOLS definition]
│   │   │   │   │   ├── history.py            [conversation history management]
│   │   │   │   │   ├── prompts.py            [system prompt (pre-Phase 2.8)]
│   │   │   │   │   │
│   │   │   │   │   ├── context_engine/       [Phase 2.8+: context assembly]
│   │   │   │   │   │   ├── __init__.py
│   │   │   │   │   │   ├── assembler.py      [ranking, budgeting, formatting]
│   │   │   │   │   │   ├── providers/        [independent data sources]
│   │   │   │   │   │   │   ├── recent_activity.py
│   │   │   │   │   │   │   ├── semantic_memory.py
│   │   │   │   │   │   │   ├── knowledge_graph.py
│   │   │   │   │   │   │   ├── open_tasks.py
│   │   │   │   │   │   │   ├── calendar.py
│   │   │   │   │   │   │   ├── profile.py
│   │   │   │   │   │   │   └── conversation.py
│   │   │   │   │   │   └── _deduplication.py
│   │   │   │   │   │
│   │   │   │   │   ├── reflection.py         [weekly reflection job]
│   │   │   │   │   ├── extraction.py         [entity extraction — Phase 2.7+]
│   │   │   │   │   ├── extraction_contract.py [extraction schema — Phase 2.7+]
│   │   │   │   │   └── reinforcement.py      [memory access tracking — Phase 2.8+]
│   │   │   │   │
│   │   │   │   └── contracts/                [type definitions & schemas]
│   │   │   │       ├── __init__.py
│   │   │   │       ├── mutation_event.py     [MutationEvent]
│   │   │   │       ├── conversation.py       [ConversationResult, types]
│   │   │   │       ├── ai_contracts.py       [Claude I/O schemas]
│   │   │   │       ├── entities.py           [Task, Money, Habit dataclasses]
│   │   │   │       ├── operations.py         [Operation enum]
│   │   │   │       ├── domain_codes.py       [Domain, EntityType enums]
│   │   │   │       ├── error_codes.py        [ErrorCode enum]
│   │   │   │       └── validators/
│   │   │   │           ├── mutation_validator.py
│   │   │   │           ├── extraction_validator.py
│   │   │   │           └── reflection_validator.py
│   │   │   │
│   │   │   ├── services/                     [Leaf services: behavior, no persistence]
│   │   │   │   ├── __init__.py
│   │   │   │   │
│   │   │   │   ├── voice/                    [Microphone, Whisper, TTS]
│   │   │   │   │   ├── __init__.py           [public: load_model, speak, poll_wake_word, ...]
│   │   │   │   │   ├── config.py
│   │   │   │   │   ├── audio.py              [RMS, gating, microphone]
│   │   │   │   │   ├── wake_word.py          [wake word detection]
│   │   │   │   │   ├── transcription.py      [Whisper model]
│   │   │   │   │   └── tts.py                [text-to-speech]
│   │   │   │   │
│   │   │   │   ├── calendar/                 [Apple Calendar via AppleScript]
│   │   │   │   │   ├── __init__.py           [public: create_event, get_events, ...]
│   │   │   │   │   ├── applescript.py        [AppleScript execution]
│   │   │   │   │   └── parsing.py            [NL date/time parsing]
│   │   │   │   │
│   │   │   │   ├── automation/               [App launch, notifications, WhatsApp, Pomodoro]
│   │   │   │   │   ├── __init__.py           [public: open_app, notify, ...]
│   │   │   │   │   ├── apps.py               [macOS app control]
│   │   │   │   │   ├── notifications.py      [notification display]
│   │   │   │   │   ├── whatsapp.py           [WhatsApp API]
│   │   │   │   │   └── pomodoro.py           [Pomodoro timer]
│   │   │   │   │
│   │   │   │   └── knowledge/                [Weather, RSS, GitHub, reflection]
│   │   │   │       ├── __init__.py           [public: get_weather, get_rss_updates, ...]
│   │   │   │       ├── weather.py            [OpenWeatherMap API]
│   │   │   │       ├── rss.py                [RSS feed parsing]
│   │   │   │       ├── github.py             [GitHub notifications]
│   │   │   │       ├── reflection.py         [reflection trigger]
│   │   │   │       └── journal.py            [journal entry handling]
│   │   │   │
│   │   │   ├── domains/                      [Business logic + persistence decisions]
│   │   │   │   ├── __init__.py
│   │   │   │   │
│   │   │   │   ├── finance/                  [Tasks, Money, Products]
│   │   │   │   │   ├── __init__.py           [public: log_task, log_money, ...]
│   │   │   │   │   ├── tasks.py              [task logic: create, complete, due checking]
│   │   │   │   │   ├── money.py              [money logic: logging, summaries]
│   │   │   │   │   ├── products.py           [product logic: shipping, sales]
│   │   │   │   │   └── tools.py              [tool handlers exported to runtime]
│   │   │   │   │
│   │   │   │   ├── wellness/                 [Habits]
│   │   │   │   │   ├── __init__.py           [public: log_habit, get_habits_today, ...]
│   │   │   │   │   ├── habits.py             [habit logic: logging, streaks]
│   │   │   │   │   └── tools.py
│   │   │   │   │
│   │   │   │   ├── productivity/             [Progress, Planning, Briefings]
│   │   │   │   │   ├── __init__.py           [public: log_progress, build_daily_plan, ...]
│   │   │   │   │   ├── progress.py           [progress logging]
│   │   │   │   │   ├── planner.py            [planning logic: daily, weekly, priority]
│   │   │   │   │   ├── briefing.py           [morning/evening briefing assembly]
│   │   │   │   │   └── tools.py
│   │   │   │   │
│   │   │   │   ├── social/                   [Reminders, Events, People]
│   │   │   │   │   ├── __init__.py           [public: save_reminder, get_due_reminders, ...]
│   │   │   │   │   ├── reminders.py          [reminder logic]
│   │   │   │   │   ├── events.py             [event logic]
│   │   │   │   │   └── tools.py
│   │   │   │   │
│   │   │   │   └── ai_context/               [Profile, Learning, Context]
│   │   │   │       ├── __init__.py           [public: get_profile_observations, ...]
│   │   │   │       ├── profile.py            [profile observation logic]
│   │   │   │       ├── reflection_consumer.py [consumes Brain's reflection output]
│   │   │   │       └── tools.py
│   │   │   │
│   │   │   └── infra/                        [Infrastructure: API, Events, Persistence]
│   │   │       ├── __init__.py
│   │   │       ├── api/                      [REST API + WebSocket facade]
│   │   │       │   ├── __init__.py
│   │   │       │   ├── main.py               [FastAPI app]
│   │   │       │   ├── routes/               [API endpoints by domain]
│   │   │       │   │   ├── finance.py
│   │   │       │   │   ├── wellness.py
│   │   │       │   │   ├── productivity.py
│   │   │       │   │   ├── social.py
│   │   │       │   │   └── ai_context.py
│   │   │       │   └── websocket/            [WebSocket event pushing]
│   │   │       │       ├── __init__.py
│   │   │       │       └── manager.py
│   │   │       │
│   │   │       └── health/                   [Database health checks, metrics]
│   │   │           ├── __init__.py
│   │   │           ├── db_health.py
│   │   │           └── metrics.py
│   │   │
│   │   ├── tests/                            [All test suites]
│   │   │   ├── conftest.py                   [pytest fixtures, shared setup]
│   │   │   │
│   │   │   ├── unit/                         [Unit tests: one package in isolation]
│   │   │   │   ├── core/
│   │   │   │   │   ├── test_runtime.py
│   │   │   │   │   ├── test_memory_finance.py
│   │   │   │   │   ├── test_memory_wellness.py
│   │   │   │   │   ├── test_brain_routing.py
│   │   │   │   │   └── test_contracts.py
│   │   │   │   ├── services/
│   │   │   │   │   ├── test_voice.py         [mock audio]
│   │   │   │   │   ├── test_calendar.py      [mock AppleScript]
│   │   │   │   │   └── test_automation.py
│   │   │   │   └── domains/
│   │   │   │       ├── test_finance_logic.py
│   │   │   │       ├── test_wellness_logic.py
│   │   │   │       └── test_productivity_logic.py
│   │   │   │
│   │   │   ├── integration/                  [Integration tests: multiple packages]
│   │   │   │   ├── test_conversation_pipeline.py  [full turn: transcript → reply]
│   │   │   │   ├── test_tool_dispatch.py          [tools → mutations → memory writes]
│   │   │   │   ├── test_memory_persistence.py     [database reads/writes]
│   │   │   │   └── test_reflection_job.py         [reflection + profile update]
│   │   │   │
│   │   │   ├── contracts/                    [Contract tests: cross-package boundaries]
│   │   │   │   ├── test_runtime_memory_contract.py      [Runtime may call Memory public API]
│   │   │   │   ├── test_brain_memory_contract.py        [Brain reads Memory]
│   │   │   │   ├── test_domain_dependency_contract.py   [Domains don't call each other]
│   │   │   │   └── test_service_dependency_contract.py  [Services are leaves]
│   │   │   │
│   │   │   ├── architecture/                 [Architecture tests: enforce invariants]
│   │   │   │   ├── test_no_circular_deps.py
│   │   │   │   ├── test_core_isolation.py    [Core doesn't import Services/Domains]
│   │   │   │   ├── test_claude_client_single.py [only Brain imports anthropic]
│   │   │   │   ├── test_storage_single.py    [only Memory imports sqlite3]
│   │   │   │   └── test_module_imports.py    [validate import statements]
│   │   │   │
│   │   │   ├── golden/                       [Golden tests: behavior snapshots]
│   │   │   │   ├── test_spending_summary_output.py   [tool output format]
│   │   │   │   ├── test_briefing_format.py
│   │   │   │   └── test_mutation_event_shape.py      [MutationEvent structure]
│   │   │   │
│   │   │   └── e2e/                          [End-to-end tests: full scenarios]
│   │   │       ├── test_voice_to_task.py     [user: "add task", verify in DB]
│   │   │       ├── test_spending_query.py    [user: "how much Swiggy", verify answer]
│   │   │       └── test_reflection_cycle.py  [weekly reflection end-to-end]
│   │   │
│   │   ├── scripts/                          [Developer scripts]
│   │   │   ├── reset_db.py                   [delete nova.db, re-init schema]
│   │   │   ├── seed_test_data.py             [populate DB with fixtures]
│   │   │   ├── validate_imports.py           [check dependency rules]
│   │   │   ├── format_code.py                [black, isort]
│   │   │   └── check_types.py                [mypy]
│   │   │
│   │   ├── requirements.txt                  [Python dependencies]
│   │   ├── pyproject.toml                    [project metadata, tool config]
│   │   └── .flake8 / .mypy.ini               [linter config]
│   │
│   └── desktop/                              [Electron + React UI (separate process)]
│       ├── src/
│       │   ├── main.ts                       [Electron main]
│       │   ├── preload.ts
│       │   ├── renderer/                     [React components]
│       │   │   ├── App.tsx
│       │   │   ├── pages/
│       │   │   ├── components/
│       │   │   └── hooks/
│       │   └── api/                          [API client (calls backend via REST/WebSocket)]
│       │       └── client.ts
│       ├── package.json
│       ├── vite.config.ts
│       └── tsconfig.json
│
└── .github/
    ├── workflows/
    │   ├── test.yml                          [CI: run all tests]
    │   ├── lint.yml                          [CI: import validation, type checking]
    │   └── deploy.yml                        [release build]
    └── PULL_REQUEST_TEMPLATE.md              [PR checklist: architecture review]
```

### 4.2 Why Each Folder Exists

| Folder | Purpose | Constraint |
|---|---|---|
| `docs/architecture/` | Canonical architecture reference | Read-only after freeze; updated only on phase transition |
| `docs/design/` | Design decisions and justification | Living document; ADRs for non-obvious choices |
| `docs/developer/` | Engineer onboarding and guidance | Updated as dev experience improves |
| `nova/core/` | Foundation (runtime, memory, brain, contracts) | Only infrastructure; no domain logic |
| `nova/services/` | Reusable behaviors (voice, calendar, etc.) | Leaf packages; no persistence, no cross-calls |
| `nova/domains/` | Business logic + persistence decisions | Non-leaf; owns entities and tools |
| `nova/infra/` | Infrastructure not in core (API, health) | Depends on everything; depended on by nothing |
| `tests/unit/` | Isolated package testing | Mock external dependencies |
| `tests/integration/` | Multiple packages together | Use real database, real file I/O where safe |
| `tests/contracts/` | Cross-package boundary verification | Catch architecture violations automatically |
| `tests/architecture/` | Enforce invariants (no circular deps, etc.) | Run on every PR |
| `tests/golden/` | Snapshot tests (output format stability) | Catch unintended changes in output |
| `tests/e2e/` | End-to-end scenarios | Full system tests with realistic data |
| `scripts/` | Developer tools (reset DB, validate, etc.) | Not part of app; run manually |

---

## 5. PACKAGE LIFECYCLE

### 5.1 Adding a New Package

**Scenario:** Add `nova.domains.finance.invoicing` (invoice tracking + generation).

**Steps:**

1. **Create folder structure:**
   ```
   nova/domains/finance/invoicing/
   ├── __init__.py           [public API: create_invoice, generate_pdf, ...]
   ├── models.py             [Invoice dataclass]
   ├── logic.py              [invoice creation, PDF generation logic]
   └── tools.py              [tool handlers for CLI/Brain]
   ```

2. **Define public API (in `__init__.py`):**
   ```python
   __all__ = ["create_invoice", "generate_invoice_pdf", "get_invoices_since"]
   ```

3. **Add to Memory if persistence needed:**
   ```
   nova/core/memory/finance/invoicing.py  [add_invoice, get_invoice_by_id, ...]
   ```
   Update `nova/core/memory/__init__.py` to export new functions.
   Create schema migration in `nova/core/memory/schema.py`.

4. **Register tools in Runtime (if user-facing):**
   In `nova.py` composition root:
   ```python
   from nova.domains.finance.invoicing import tools as invoicing_tools
   TOOL_HANDLERS.update({
       "create_invoice": invoicing_tools.create_invoice_handler,
       "generate_invoice_pdf": invoicing_tools.generate_handler,
   })
   ```

5. **Add API routes (if external access needed):**
   ```
   nova/infra/api/routes/finance_invoicing.py  [/invoices endpoints]
   ```

6. **Write tests:**
   - `tests/unit/domains/test_finance_invoicing.py` — logic in isolation.
   - `tests/integration/test_invoicing_pipeline.py` — full tool → mutation → memory flow.

7. **Update documentation:**
   - Add to `docs/architecture/` describing the new domain.
   - Update `NOVA_ENGINEERING_SPECIFICATION_v1.md` if dependencies changed.

8. **Verification:** No existing code should be modified (except composition root and Memory schema).

---

### 5.2 Adding a New Domain (Large Feature)

**Scenario:** Add `nova.domains.commerce` (marketplace integrations, selling across platforms).

**Steps:**

1. **Create domain package:**
   ```
   nova/domains/commerce/
   ├── __init__.py                [public API]
   ├── listings.py                [listing logic: create, sync, archive]
   ├── orders.py                  [order logic: track, fulfill]
   ├── platforms/                 [platform integrations]
   │   ├── amazon.py
   │   ├── ebay.py
   │   └── etsy.py
   └── tools.py                   [tool handlers]
   ```

2. **Extend Memory:**
   ```
   nova/core/memory/commerce/
   ├── listings.py
   ├── orders.py
   └── platform_sync.py
   ```
   Update schema version, add tables (`listings`, `orders`, `platform_accounts`).

3. **Identify dependencies (dependency injection points):**
   - Does this domain need Calendar? → inject `calendar.get_events`.
   - Does this domain need Weather? → inject `knowledge.get_weather`.
   - Does this domain need to call another domain? **NO** (violates Rule 3).

4. **Register with Runtime:**
   Update `nova.py` composition root:
   ```python
   from nova.domains.commerce import tools as commerce_tools
   TOOL_HANDLERS.update(commerce_tools.HANDLERS)
   ```

5. **If this domain needs service-level behavior:**
   Create a new Service package (e.g., `nova.services.ecommerce_sync` for background syncing).
   - Service owns: polling marketplaces, retrying failed syncs.
   - Service does NOT own: parsing marketplace data (Commerce domain owns that).

6. **No changes to existing packages** (except composition root + Memory schema).

---

### 5.3 Adding a New Service

**Scenario:** Add `nova.services.notification_aggregator` (centralize alerts from multiple sources).

**Constraint:** Services are leaves (no other services depend on them).

**Steps:**

1. **Create service package:**
   ```
   nova/services/notification_aggregator/
   ├── __init__.py                [public: aggregate(), subscribe_to_source()]
   ├── sources.py                 [handlers for each notification source]
   └── deduplication.py           [filter duplicate notifications]
   ```

2. **Determine if persistence is needed.**
   - If yes, this isn't a Service — it's a Domain (reconsider design).
   - If no, proceed.

3. **Define public API:**
   - No database operations.
   - Only pure functions (transform input → output).

4. **Inject dependencies, never import other services:**
   ```python
   def aggregate(event_handlers: dict[str, Callable]) -> None:
       """Aggregate notifications. Event handlers are injected."""
       pass
   ```

5. **Register in composition root:**
   ```python
   from nova.services.notification_aggregator import aggregate
   # In run loop or initialization:
   aggregate(event_handlers={
       "slack": slack_handler,
       "email": email_handler,
   })
   ```

6. **Tests:**
   - Mock all inputs.
   - No database needed.

---

### 5.4 Deprecating a Package

**Scenario:** `nova.domains.old_crm` is being replaced by `nova.domains.social`.

**Strategy:**

1. **Phase 1: Soft deprecation (2 releases)**
   - Mark public API functions with `@deprecated("Use social.handle_contact() instead")`.
   - Update documentation to recommend the new package.
   - No existing callers are forced to change.

2. **Phase 2: Redirect (1 release)**
   - Old package functions delegate to new package:
     ```python
     def get_contacts():
         """Deprecated. Use nova.domains.social.get_contacts()."""
         from nova.domains.social import get_contacts as get_social_contacts
         return get_social_contacts()
     ```
   - Run a migration script to move old data to new table.

3. **Phase 3: Removal (1 release later)**
   - Delete the old package.
   - Ensure no remaining imports.

**Rationale:** Give teams time to migrate code; no surprise breakages.

---

### 5.5 Schema Migrations

**Rule:** Migrations are applied automatically on startup via `memory.init_db()`.

**Steps to add a new column:**

1. **Identify the table:** `tasks`, `money`, `habits`, etc.

2. **Create migration script in `nova/core/memory/schema.py`:**
   ```python
   # Version 1.1 migration
   def migrate_to_1_1(conn):
       conn.execute("""
           ALTER TABLE tasks
           ADD COLUMN priority TEXT DEFAULT 'medium' NOT NULL
       """)
       conn.execute("UPDATE schema_version SET version = '1.1'")
       conn.commit()
   ```

3. **Register in `init_db()`:**
   ```python
   MIGRATIONS = {
       "1.1": migrate_to_1_1,
   }
   
   def init_db():
       current_version = get_schema_version()  # e.g., "1.0"
       pending = [v for v in MIGRATIONS if v > current_version]
       for version in sorted(pending):
           MIGRATIONS[version](conn)
   ```

4. **Make migration idempotent:**
   ```python
   # Check if column exists before adding
   cursor = conn.execute("PRAGMA table_info(tasks)")
   columns = {row[1] for row in cursor.fetchall()}
   if "priority" not in columns:
       conn.execute("ALTER TABLE tasks ADD COLUMN priority ...")
   ```

**Constraint:** No schema changes allowed on frozen packages (Core Infrastructure, Contracts). Only expand (add columns), never contract (remove columns) during a version cycle.

---

## 6. TESTING OWNERSHIP

### 6.1 Who Owns Each Test Level

| Test Type | Owner | Trigger | Failure = |
|---|---|---|---|
| **Unit (one package)** | Package author | Every PR | Code review should catch |
| **Integration (multiple packages)** | Integration team (if >5 engineers) | Every PR | Design review + integration test |
| **Contract (boundary tests)** | Architecture team | Every PR | Dependency violation (blocker) |
| **Architecture (invariants)** | CI automated | Every PR | Invariant violation (blocker) |
| **Golden (output snapshot)** | Package author | Every change to output | Needs approval (intentional change?) |
| **E2E (full scenario)** | QA / product team | Before release | Regression (blocks ship) |

---

### 6.2 Unit Tests

**Goal:** One package in isolation, all dependencies mocked.

**Owned by:** Package author.

**Example: `tests/unit/domains/test_finance_logic.py`**

```python
import pytest
from unittest.mock import Mock, patch
from nova.domains.finance import tasks

@pytest.fixture
def mock_memory():
    return Mock()

def test_log_task_with_due_date(mock_memory):
    """Test task creation with due date parsing."""
    with patch("nova.domains.finance.tasks.memory", mock_memory):
        result = tasks.log_task("Buy milk", due="tomorrow")
        mock_memory.add_task.assert_called_once()
        assert result["text"] == "Buy milk"
```

**Constraints:**

- No real database access (mock Memory).
- No real external APIs (mock Services).
- No file I/O (mock filesystem).

**Ownership rule:** If a test touches the real database, it's not a unit test (it's integration).

---

### 6.3 Integration Tests

**Goal:** Multiple packages together, real database and file I/O.

**Owned by:** Integration team (or designated owner).

**Example: `tests/integration/test_conversation_pipeline.py`**

```python
def test_full_turn_from_transcript_to_memory(db_session, api_key):
    """Test complete turn: transcript → Brain → tool → Memory write."""
    transcript = "Add task: buy milk"
    
    result = process_message(transcript)
    
    assert result.reply.lower().contains("added task")
    task = memory.find_task_by_text("buy milk")
    assert task is not None
```

**Constraints:**

- Uses real (test) database.
- Real external APIs mocked (Claude API).
- Cleans up after itself (reset database, delete files).

**Ownership rule:** Integration tests are slower and harder to maintain; only test critical paths and boundaries.

---

### 6.4 Contract Tests (Architecture Enforcement)

**Goal:** Verify cross-package boundaries are respected.

**Owned by:** Architecture team (automated, CI).

**Example: `tests/contracts/test_domain_dependency_contract.py`**

```python
def test_domains_dont_import_each_other():
    """Verify no domain imports another domain."""
    import ast
    import os
    
    domains = ["finance", "wellness", "productivity", "social", "ai_context"]
    for domain in domains:
        path = f"nova/domains/{domain}/__init__.py"
        with open(path) as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("nova.domains."):
                    other_domain = node.module.split(".")[2]
                    assert other_domain == domain, \
                        f"{domain} imports {other_domain} — violates Rule 3"
```

**Constraints:**

- Automated (run on every PR).
- Blocks merge if violated.
- No exceptions allowed (rule violations indicate architecture problems).

**Ownership rule:** Contract tests are non-negotiable; if they're failing, the architecture isn't right.

---

### 6.5 Architecture Tests (Invariant Enforcement)

**Goal:** Ensure 60+ runtime invariants are enforced in code.

**Owned by:** CI automated (run on every PR).

**Example: `tests/architecture/test_no_circular_deps.py`**

```python
def test_no_circular_dependencies():
    """Verify dependency graph is acyclic."""
    import importlib
    from collections import defaultdict
    
    # Build dependency graph
    graph = defaultdict(set)
    for package in ALL_PACKAGES:
        for dependency in get_imports(package):
            graph[package].add(dependency)
    
    # Check for cycles
    for package in graph:
        assert not has_cycle(graph, package), \
            f"Cycle detected: {package} has circular dependency"
```

**Constraints:**

- Catches violations of Fundamental Rules (1–10, 51–60).
- Automated, no manual exemptions.
- Failure blocks PR merge.

---

### 6.6 Golden Tests (Snapshot Stability)

**Goal:** Verify output format doesn't change unintentionally.

**Owned by:** Package author.

**Example: `tests/golden/test_spending_summary_output.py`**

```python
def test_spending_summary_format(db_with_sample_data):
    """Verify spending summary text format hasn't changed."""
    summary = planner.get_spending_summary("this month")
    
    # Expected format:
    # "You spent ₹X on Y this month."
    expected_pattern = r"You spent ₹\d+ on \w+ this month\."
    assert re.match(expected_pattern, summary)
```

**Constraints:**

- Shallow assertions (format only, not logic).
- Approved snapshot can be updated intentionally (explicit review).

---

### 6.7 End-to-End Tests

**Goal:** Full realistic scenarios from user action to database state.

**Owned by:** QA / Product team.

**Example: `tests/e2e/test_voice_to_task.py`**

```python
def test_voice_command_add_task_end_to_end(app, db):
    """User says 'add task buy milk', verify it appears in open tasks."""
    # Simulate voice input
    audio_bytes = record_sample_audio("add task buy milk")
    
    # Process through full app
    result = app.process_audio(audio_bytes)
    
    # Verify end result
    assert "added task" in result.reply.lower()
    tasks = memory.get_open_tasks()
    assert any(t["text"].lower() == "buy milk" for t in tasks)
```

**Constraints:**

- Slowest test category (5–30 seconds per test).
- Only critical user journeys (not every edge case).
- Run before every release.

---

## 7. ENGINEERING OWNERSHIP (Multi-Team Organization)

### 7.1 Team Structure for 20+ Engineers

Assume Nova scales to 20 engineers. How should teams own code?

**Option 1: By Layer (Recommended)**

```
┌─────────────────────────────────────────────────────────────┐
│ Platform Team (5 engineers)                                 │
│ Owns: Core Infrastructure, Tests/CI                         │
│ - nova.core.runtime                                         │
│ - nova.core.memory                                          │
│ - nova.core.brain                                           │
│ - nova.core.contracts                                       │
│ - tests/unit, tests/contracts, tests/architecture           │
│ - CI/CD pipelines                                           │
└─────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────┐   ┌─────────────────┐
│ Services Team (3 engineers)          │   │ API Team (2)    │
│ Owns: Leaf services                  │   │ Owns: REST/WS   │
│ - nova.services.voice                │   │ - nova.infra.api│
│ - nova.services.calendar             │   │ - Desktop app   │
│ - nova.services.automation           │   │   (co-owned)    │
│ - nova.services.knowledge            │   │                 │
│ Stable; changes 1-2x per quarter     │   │ Evolves with    │
│                                      │   │ API contracts   │
└──────────────────────────────────────┘   └─────────────────┘

┌────────────────────────────────────────────────────────────┐
│ Domain Teams (3 teams × 2–3 engineers = 6–9 engineers)     │
│ Each team owns ONE domain                                   │
│                                                             │
│ Finance Team              │ Wellness Team      │ Productivity Team
│ - nova.domains.finance    │ - nova.domains.wellness  │ - nova.domains.productivity
│ - Memory finance tables   │ - Memory wellness tables │ - Memory productivity tables
│ - Tests (unit + integration)                               │
│                                                             │
│ Social Team               │ AI Context Team                │
│ - nova.domains.social     │ - nova.domains.ai_context     │
│ - Memory social tables    │ - Memory profile + learning   │
└────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ QA / DevOps (2–3 engineers)             │
│ Owns: E2E testing, deployment           │
│ - tests/e2e                             │
│ - Production monitoring                 │
│ - Release coordination                  │
└─────────────────────────────────────────┘
```

**Advantages:**

- Platform team can move fast (core infra is stable).
- Service team changes are rare (services are leaf).
- Domain teams can work in parallel (no cross-domain dependencies).
- Clear ownership (no ambiguity about who owns what).

**Disadvantages:**

- Requires discipline (Core team must maintain API stability).
- Domain teams need to understand Memory contracts.

**Decision rule:** A team owns a package and its tests. Changes to a package must be reviewed by the team that owns it.

### 7.2 Stable vs. Evolving Packages

| Package | Stability | Team | Change frequency | Approval process |
|---|---|---|---|---|
| nova.core.runtime | 🔒 Frozen | Platform | <1/quarter | Architecture review + unit tests |
| nova.core.memory | 🔒 Frozen (schema change = migration) | Platform | <1/month | Schema review + migration test |
| nova.core.brain | 🟠 Stable (context providers grow) | Platform | 1/month | Unit tests + golden tests |
| nova.core.contracts | 🔒 Frozen (types grow, don't shrink) | Platform | <1/quarter | Architecture review |
| nova.services.* | 🔒 Frozen (public API) | Services | <1/quarter | Backwards compatibility required |
| nova.domains.* | 🟡 Active (logic, not interfaces) | Domain teams | 1-2/week | Unit + integration tests |
| nova.infra.api | 🟡 Active (endpoints evolve) | API team | 1/week | Contract tests (must not break clients) |

**Contract:** If a package is Frozen (🔒), breaking changes require Architecture approval. Stable (🟠) packages can have internal changes. Active (🟡) packages can iterate freely within their boundary.

---

### 7.3 Code Review Process

**For Core Infrastructure changes:**
1. Author: write code + unit tests.
2. Peer review (Platform team): check logic, tests.
3. Architecture review (Principal Architect): check invariants, contract compliance.
4. Merge.

**For Domain changes:**
1. Author (Domain team): write code + unit tests.
2. Peer review (Domain team): check logic, tests.
3. Integration review (if Memory schema changed): verify migration is idempotent.
4. Merge.

**For API/Infrastructure changes:**
1. Author: write code + tests.
2. Peer review (same team).
3. Contract test verification (automated in CI).
4. Merge.

**Blocker conditions:**
- Any architecture invariant violation (contract tests fail).
- Any memory schema issue without migration.
- Circular dependency introduced.

---

## 8. TECHNICAL DEBT POLICY

### 8.1 What Shortcuts Are Acceptable

**Acceptable (short-term only):**

1. **Duplicate code (max 2 instances):** If the same logic appears twice, copy-paste is OK temporarily. On third instance, refactor into shared function.

2. **Incomplete error handling:** If all error paths aren't handled, log a TODO + open an issue. Don't ship with unhandled exceptions, but don't spend a day perfecting error messages.

3. **Temporary mocks in tests:** If an external API is flaky, mock it for now. But open an issue to fix it (retry logic, timeout, etc.).

4. **TODO comments:** Link to issue. No orphaned TODOs.

5. **Stubbed functionality:** Return sensible defaults for now (e.g., empty list if not implemented). Issue required.

### 8.2 What Shortcuts Are Forbidden

**Forbidden (never acceptable):**

1. **Architecture violations:** No domain imports another domain "just for this turn". No service imports another service. No Core imports Domain. These shortcuts propagate and become permanent.

2. **Direct database access outside Memory:** Even if it's "just a quick query", it's forbidden. Use Memory public API (add it if needed).

3. **Circular dependencies:** No `A → B → A` even transitively. Violates core principle.

4. **Untraced mutations:** Every state change must produce a MutationEvent (or be a read operation). No silent writes.

5. **Injection bypassing:** If something should be injected, don't import it directly. Violates leaf-service principle.

6. **Unlogged errors:** Every exception must be caught and logged somewhere. Silent failures are forbidden.

7. **Type violations:** If a function expects `str`, don't pass `int`. Use type hints; run mypy.

8. **Global mutable state:** Singleton patterns are OK (Whisper model, Brain history), but new global state requires architecture review.

### 8.3 Debt Tracking

**Process:**

1. **When discovered:** Open an issue with `tech-debt` label.
   - Title: "Debt: [component] [issue]"
   - Example: "Debt: Memory schema migration not idempotent"
   - Description: What's the debt, why it matters, how to fix it.

2. **Prioritization:** 
   - Critical (blocks shipping): Must fix before release.
   - High (slows team down): Fix in next sprint.
   - Medium (nice to have): Fix when roadmap allows.
   - Low (future work): Track but don't prioritize.

3. **Tracking:** Maintain a `/docs/architecture/TECHNICAL_DEBT.md` file.
   ```markdown
   | Item | Component | Priority | Fix time | Issue |
   |---|---|---|---|---|
   | Logging not structured | nova.core.runtime | Medium | 2 days | #123 |
   | Metrics not implemented | nova.core.* | Low | 3 days | #124 |
   ```

4. **Review:** Once per quarter, prioritize debt. Never accumulate >10 critical items.

---

## 9. VERSIONING POLICY

### 9.1 Version Scheme: vM.N.P

- **M (Major):** Architecture change (Phase transitions). Rare (every 1–2 years).
- **N (Minor):** Feature additions, new domains (quarterly).
- **P (Patch):** Bug fixes, small improvements (weekly).

### 9.2 v1.0 → v1.5 (Same Architecture)

**Allowed changes (no breaking changes):**

1. **New domains:** `nova.domains.commerce`, `nova.domains.analytics`. Zero changes to existing code.
2. **New services:** `nova.services.calendar_sync`. Zero changes to existing code.
3. **New Memory tables:** Add columns, new tables. Old schema still works (migration applied on startup).
4. **New Brain capabilities:** Context providers, extraction features. Old API still works.
5. **Bug fixes:** No API changes.
6. **Performance optimizations:** No API changes.

**Forbidden (would require v2.0):**

- Remove a service (would break composition root).
- Rename a table (would break existing queries).
- Remove a tool (would break Brain routing).
- Change MutationEvent structure (would break runtime).
- Make Memory persistence different (would break storage contract).

### 9.3 v1.5 → v2.0 (Architecture Evolution)

When to declare v2.0:

1. **A core principle is violated or changed.** E.g., "Memory now handles reasoning too" (would break Brain-only Claude rule).
2. **A major layer is added or removed.** E.g., "Runtime is no longer the orchestrator".
3. **A frozen package's responsibility changes.** E.g., "Core now contains domain logic".

**v2.0 migration path:**

1. Parallel run (v1 and v2 coexist for 1–2 releases).
2. Data migration scripts.
3. Compatibility layer (v1 APIs delegate to v2).
4. Sunset v1 over time.

**Example:** v2.0 adds Learning Engine (Phase 2.9). This is a new Domain + Service, not an architecture change, so it's v1.5 (not v2.0).

---

## 10. NOVA ENGINEERING SPECIFICATION v1 (FORMAL)

---

**TITLE:** Nova Engineering Specification v1

**VERSION:** 1.0

**FROZEN:** July 6, 2026

**AUTHORITY:** Principal Software Architect (Codebase Organization)

---

### 10.1 Objective

Define how Nova's codebase should be organized and extended over 5+ years such that:

1. **Clear ownership.** Every package has exactly one responsibility and one owning team.
2. **Independent evolution.** New domains can be added without changing existing code.
3. **Architectural integrity.** 60+ invariants enforce structure (not style).
4. **Team scalability.** Grows from 1 engineer to 20+ without chaos.
5. **Continuous delivery.** Features ship independently; no monolithic releases needed.

---

### 10.2 Core Structures

**Nova has three tiers:**

1. **Core Infrastructure** (4 packages): Runtime, Memory, Brain, Contracts. Frozen; changes rare.
2. **Services & Domains** (11 packages): Reusable behaviors (Voice, Calendar, etc.) and business logic (Finance, Wellness, etc.). Stable public APIs; evolving implementations.
3. **Tools & Infrastructure** (API, testing, CI). Supporting layer; evolves with needs.

**Dependency rule (one-way arrow):**
```
Domain     →  Core Infrastructure
Service    →  Core Infrastructure
Tools      →  Core Infrastructure, Services, Domains (read-only)
Domains    ↯  Never import other domains
Services   ↯  Never import other services
```

---

### 10.3 Packages and Ownership

| Package | Responsibility | Team | Stability | Growth model |
|---|---|---|---|---|
| nova.core.runtime | Conversation pipeline, event bus | Platform | Frozen | Providers added (not new layers) |
| nova.core.memory | Storage abstraction, all queries | Platform | Stable | New tables, new domains read through public API |
| nova.core.brain | Claude interface, reasoning jobs | Platform | Stable | Context providers grow, new reasoning jobs |
| nova.core.contracts | Type defs, schemas, enums | Platform | Frozen | Types grow, never shrink |
| nova.services.voice | Audio I/O, transcription, TTS | Services | Frozen | Transcription model upgraded; API unchanged |
| nova.services.calendar | Calendar read/write, date parsing | Services | Frozen | Date parser enhanced; API unchanged |
| nova.services.automation | App launch, notifications, Pomodoro | Services | Frozen | New automations; API unchanged |
| nova.services.knowledge | Weather, RSS, GitHub, reflection | Services | Frozen | New data sources; API unchanged |
| nova.domains.finance | Tasks, money, products | Finance team | Active | Logic iterations; API stable |
| nova.domains.wellness | Habits, health | Wellness team | Active | Tracking enhancements; API stable |
| nova.domains.productivity | Progress, planning, briefings | Productivity team | Active | Planning algorithms; API stable |
| nova.domains.social | Reminders, events, people | Social team | Active | Event tracking; API stable |
| nova.domains.ai_context | Profile, learning signals | AI team | Active | Learning algorithms; API stable |
| nova.infra.api | REST API, WebSocket push | API team | Active | New endpoints; contract tests required |

---

### 10.4 Dependency Graph (Formal)

```
nova.core.contracts
  ↑
  └── imported by ALL packages (common vocabulary)

nova.core.runtime
  ← nova.core.memory        [queries]
  ← nova.core.brain         [routing]
  ← nova.core.contracts     [types]

nova.core.memory
  ← nova.core.contracts     [types]
  ← all domains             [persistence API only]
  ← nova.core.brain         [read-only: history, profile]

nova.core.brain
  ← nova.core.memory        [Phase 2.8+ context engine]
  ← nova.core.contracts     [types]
  ← anthropic SDK           [ONLY package]

nova.services.*  (all leaves)
  ← nova.core.contracts     [types]
  ← python stdlib + vendors [no nova dependencies except contracts]

nova.domains.*  (all leaves in v1.0; cross-domain reads via Memory)
  ← nova.core.memory        [persistence]
  ← nova.core.contracts     [types]
  ← nova.core.brain         [ai_context only: reflection call]

nova.infra.api
  ← nova.core.memory        [read]
  ← all domains             [read]
  ← nova.core.contracts     [types]

nova.main (composition root)
  ← all packages            [wires them together]
```

---

### 10.5 Invariants (Summary)

**60 invariants** (detailed in Section 3) enforce this structure. Violations are caught by:

- **Architecture tests** (automated, CI): No circular deps, only Brain imports anthropic, only Memory imports sqlite3.
- **Contract tests** (automated, CI): Domains don't call domains, Services don't call Services.
- **Code review** (human): No dependency violations, no untraced mutations, no shortcuts.

---

### 10.6 Adding Code

**New domain:** 1 folder + Memory tables + tool registration. Zero changes to existing packages.

**New service:** 1 folder. Must be a leaf (no new dependencies on existing services).

**New feature in existing domain:** Change only that domain's package. Tests must pass locally and in CI.

**Change to core infrastructure:** Requires Architecture review + contract tests pass + all dependent tests pass.

**Forbidden:** Architecture violations (Rules 1–60), circular dependencies, direct DB access outside Memory, silent state mutations.

---

### 10.7 Governance

**Architecture keeper:** Principal Architect. Approves:
- Changes to Core Infrastructure.
- New Services (must be leaves).
- Any dependency rule exceptions (never given; indicates redesign needed).

**Team leads:** Own their package. Approve:
- Changes to their domain/service.
- Unit + integration tests.
- API design (for public methods).

**QA/Product:** Own E2E tests. Approve release quality.

---

### 10.8 Growth Phases (5-year plan)

| Year | Phase | Scale | Changes |
|---|---|---|---|
| 1 | v1.0 (today) | 1–5 engineers | 7 services, 5 domains, Core + Platform |
| 1.5 | v1.5 | 5–10 engineers | +2 domains (Commerce, Analytics), semantic memory |
| 2 | v2.0 | 10–15 engineers | Agent system, desktop UI, multi-user (TBD) |
| 2.5 | v2.5 | 15–20 engineers | Collaboration features (TBD) |
| 3+ | v3.x | 20+ engineers | Modularity (allow loading/unloading domains) |

**Each phase maintains architectural integrity.** New code always flows downward (toward Core), never upward.

---

## DOCUMENT CONTROL

**Version:** 1.0

**Status:** Engineering Standard (Frozen with Nova Core v1.0)

**Last Updated:** July 6, 2026

**Authority:** Principal Software Architect (Codebase Organization)

**Next Review:** When v2.0 architecture is approved (expected year 2).

---

## APPENDIX: Checklist for New Code

Before committing code, ask:

- [ ] Does this code belong in an existing package, or is a new package needed?
- [ ] Does this package have exactly one responsibility?
- [ ] Are all dependencies one-way (never circular)?
- [ ] Does this code import only packages it's allowed to import?
- [ ] Are all mutations represented as MutationEvents?
- [ ] Are all database writes through Memory public API?
- [ ] If this is a Service, is it a leaf (no persistence, no cross-service calls)?
- [ ] If this is a Domain, does it only call Memory (never other Domains)?
- [ ] Are unit tests mocking all external dependencies?
- [ ] Are integration tests using real database + mocked APIs?
- [ ] Do contract tests pass (no violations caught)?
- [ ] Does this code introduce any new architectural debt? (if yes, open issue)

---

**END OF SPECIFICATION**

This document defines how Nova's codebase should grow. Follow it, and chaos remains an option. Ignore it, and chaos becomes a guarantee.
