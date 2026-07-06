# NOVA CORE RUNTIME SPECIFICATION v1

**Status:** Architecture Specification — Frozen Nova Core v1.0  
**Scope:** Runtime behavior, lifecycle, and invariants for Nova Core's execution engine  
**Abstraction Level:** Kernel-level documentation — no marketing, no philosophy  
**Authority:** This document is the authoritative reference for how Nova Core executes

---

## 0. Executive Summary

Nova Core is a single-process, event-driven architecture organized around **MutationEvents** — immutable records of successful business mutations. The runtime lifecycle consists of five phases: Cold Boot, Model Load, Memory Initialization, Context Initialization, and Ready State. All user interaction flows through a single synchronous conversation pipeline that routes to Brain, executes tools, persists mutations, and fires async cleanup jobs.

Key runtime principle: **No mutation without an event. No event without a mutation.**

---

## 1. RUNTIME LIFECYCLE

### 1.1 Cold Boot Phase

**Trigger:** `AssistantApp.start()` called from `nova.py` main.

**Steps:**

1. **Environment:** `load_dotenv()` reads `.env` into `os.environ`. Failure here is fatal — no recovery.
2. **API Config Check:** `brain.check_api_config()` verifies `NOVA_CLAUDE_API_KEY` or legacy `RAI_CLAUDE_API_KEY` exists. Fatal on absence.
3. **Database Initialization:** `memory.init_db()` runs schema migration. Creates tables if absent; adds missing columns if schema version has incremented. Idempotent — safe to call multiple times.
   - Schema version tracked in `schema_version` table (one row, immutable after first run).
   - All Phase 2+ migrations applied in dependency order (semantic embeddings before learning tier computations).
   - **Blocking call:** SQLite synchronous write-lock held until schema complete.
4. **Calendar Injection:** `brain.set_calendar_source(calendar.get_events)` wires the Calendar service's read function into Brain's context engine as a dependency. This is the only dependency injection point in the composition root. Done once, never again.
5. **Reflection Gate Check:** `knowledge.should_run_reflection()` queries `last_reflection_date` from profile. If >7 days old (or never run), schedules `knowledge.run_reflection()` synchronously. Blocks startup by ~2–5 seconds on first run or after 7+ days offline.
   - Reflection failure does not halt startup (try/except with print).
   - Stale reflection is not retried; the gate remains open until next startup cycle.
6. **Entity Extraction Sweep:** `_extract_entities_async()` spawns a background daemon thread to run `brain.run_entity_extraction()`.
   - Returns immediately (non-blocking).
   - Failure silently logged (exception printed, not re-raised).
7. **Model Load:** `voice.load_model()` loads Whisper weights into memory (CPU or GPU). First run downloads ~140MB. **Blocking call** — startup stalls here 5–30 seconds depending on hardware and network.
8. **Ready State Reached:** Run loop begins.

**State after Cold Boot:**

- Memory: Database ready, all tables present, schema migrated.
- Brain: Claude API key validated, Calendar dependency injected, conversation history loaded from memory.
- Voice: Whisper model in memory, ready to transcribe.
- All other services: Stateless (leaf services have no initialization step).
- Threading: One background thread (entity extraction) active; main thread owns the run loop.

**Total startup time:** 5–30 seconds (dominated by Whisper download on first run, reflection job on day 8+).

---

### 1.2 Model Loading Phase

**Part of Cold Boot.** Synchronized in `voice.load_model()`.

**Steps:**

1. Check if local Whisper weights exist at `$NOVA_CACHE_DIR/whisper-*.pt`.
2. If absent, download from Hugging Face (~140MB, ~60–120 seconds on typical internet).
3. Load model into process memory.
4. Return model object to `AssistantApp`.

**Failure modes:**

- Network down: Raises exception, startup halts.
- Disk full: Raises exception, startup halts.
- Corrupted weights file: Raises exception, retried by deleting cache and re-downloading (not automatic — user must retry app launch).

**Immutability:** Once loaded, Whisper model is never reloaded — it lives in process memory for the entire run.

---

### 1.3 Memory Initialization Phase

**Part of Cold Boot.** Synchronized in `memory.init_db()`.

**Database state machine:**

1. Connect to `nova.db` (create if absent).
2. Check `schema_version` table existence.
   - If absent: First run. Create all Phase 1 tables (`tasks`, `money`, `progress`, `products`, `reminders`, `habits`, `profile`, `graph`).
   - If present: Check stored version against code version.
3. For each pending schema migration (from stored version → code version):
   - Apply ALTER TABLE statements (idempotent by checking column existence first).
   - Increment stored version.
4. Load all tables into memory (no materialization; just validate structure).

**Tables created/migrated:**

| Table | Phase | Rows on startup | Mutability | Index strategy |
|---|---|---|---|---|
| `schema_version` | 1 | 1 | Immutable | (single row) |
| `tasks` | 1 | ~50–200 typical | Insert/update only | task_name (unique), due_date |
| `money` | 1 | ~100–1000 | Insert only | date, type |
| `progress` | 1 | ~50–200 | Insert only | area, created_at |
| `products` | 1 | ~10–50 | Insert/update/delete | product_name (unique) |
| `reminders` | 1 | ~20–100 | Insert/update | remind_date, remind_time |
| `habits` | 1 | ~5–20 | Insert only | name, created_at |
| `profile` | 1 | 1 (single row) | Update only | (single row, no index) |
| `conversation_history` | 2.3+ | ~500–5000 | Insert only | conversation_id, created_at |
| `memories` | 2.1+ | ~1000–10000 | Insert only; supersede via `supersedes_id` | id (UUID), tier, created_at, access_count |
| `entities` | 2.6+ | ~100–500 | Insert/update | entity_id, type, canonical_name |
| `edges` | 2.6+ | ~500–2000 | Insert/delete | from_entity_id, to_entity_id, relation_type |

**Read state at startup:**

- Brain loads `conversation_history` last ~20 turns (or ~5KB) into `brain.history` (in-process, immutable copy).
- Profile loads single `profile` row into runtime cache (`profile.current_observations`).
- No other tables are pre-loaded; queries are on-demand and synchronous.

**Connection pooling:** No connection pool. Each query opens a new connection, executes in a transaction, commits/rolls back, closes. Transaction lifetime: ~1–10ms per operation.

---

### 1.4 Context Initialization Phase

**After model and memory ready.** Happens in `brain.set_calendar_source()` and implicit Brain initialization.

**Brain context engine (`services/brain/context_engine/`) initializes:**

1. Create provider registry (dependencies injected by composition root):
   - Recent activity provider
   - Semantic memory provider (if LanceDB available, else disabled)
   - Knowledge graph provider (if entities table exists, else disabled)
   - Open tasks provider
   - Calendar provider (injected here)
   - User profile provider
   - Conversation history provider
2. Load all providers (no I/O; just wire up callables).
3. Set token budget: `NOVA_CONTEXT_TOKEN_BUDGET` (default 4000 tokens).
4. Set trim order (lowest priority → highest priority):
   - Conversation history (trimmed first if budget overrun)
   - Semantic memory results
   - Activity summaries
   - Calendar events
   - Open tasks
   - Profile (never trimmed)

**No actual context assembly** happens until first `brain.route()` call.

---

### 1.5 Ready State

**Reached after all above complete.** Run loop begins.

**Invariant:** Application is in Ready State if and only if:
- `memory.init_db()` completed successfully
- Whisper model loaded
- `brain.check_api_config()` passed
- Brain's calendar source injected

**Observable:** `AssistantApp._run_loop()` prints `"Nova is listening for the wake word…"` when Ready State reached.

---

## 2. MUTATIONEVENT ARRIVAL AND PROPAGATION

### 2.1 MutationEvent Definition

A `MutationEvent` is an immutable record of one successful business operation:

```python
@dataclass(frozen=True)
class MutationEvent:
    event_type: str          # "task.created" | "money.logged" | "" (empty for non-WS events)
    entity_type: str         # "task" | "money" | "habit" | "journal" | …
    operation: str           # "create" | "update" | "complete" | …
    entity: dict             # {"text": "Buy milk", "due": "2026-07-07", …}
    metadata: dict = {}      # optional: {"source": "voice", "conversation_id": "uuid", …}
```

**Immutability:** Once created, a MutationEvent cannot be modified. Mutation is by construction, not mutation.

**Invariant:** No MutationEvent is created without a corresponding successful domain operation. Conversely, all domain-layer writes must produce a MutationEvent record.

---

### 2.2 MutationEvent Sources

| Source | Producer | Trigger | MutationEvent fields |
|---|---|---|---|
| **Voice command** | `conversation.py` | User speaks, Brain routes to tool | `conversation_id`, `source="voice"` |
| **Pomodoro completion** | `automation.start_pomodoro` | Timer expires, callback fires | `operation="complete"`, metadata `{minutes: 25}` |
| **Journal entry** | `knowledge.handle_journal` | User dictates journal text | `event_type=""` (memory-only, no WS event) |
| **Profile observation** | `brain.run_reflection_job` | Weekly reflection runs | `event_type="profile.updated"`, operation `"supersede"` |
| **Entity extraction** | `brain.run_entity_extraction` | Batch extraction completes | Event published via `publish_graph_updated` |

**Only source:** These are the exhaustive sources. Mutations never originate elsewhere.

---

### 2.3 MutationEvent Arrival Flow

**Synchronization point:** `finalize_mutations(events)` in `side_effects.py`. Called exactly once per event source.

**Steps (in order, all synchronous except entity extraction):**

1. **Validation:** Each event's `event_type`, `entity_type`, `operation` fields validated against a schema (not yet code-canonical; see debt in AI_CONTRACTS.md).
   - Invalid field values do not raise; events with invalid fields are logged but processed (lenient).

2. **WebSocket Publication:** `publish_mutation_events(events)` emits each event to all subscribers.
   - Event published under `channel="events"`, `event_type=event.event_type`.
   - Payload: `{"entity_type": "…", "operation": "…", **event.metadata}`.
   - Subscriber exception handling: Best-effort; no exception propagates (try/except with silent fail).
   - **No blocking:** Publishing is fire-and-forget to in-memory subscriber list.

3. **Memory Production:** `apply_memory_producers(events)` runs local pre-filters and writes semantic memories.
   - Calls `memory_producers.memories_from_mutations(events)` — a deterministic function that maps domain mutations to semantic memory records.
   - For each produced memory: `memory.remember(**record)`.
   - Success: `publish_memory_created(source=…)` emitted.
   - Failure: Exception caught, logged, processing continues for remaining events.
   - **Blocking call:** Synchronous SQLite writes until all memories committed.

4. **Entity Extraction:** `schedule_entity_extraction()` spawns a daemon thread to run `brain.run_entity_extraction()`.
   - Returns immediately (non-blocking).
   - Extraction happens in background; extraction failures are logged but do not interrupt the conversation pipeline.

5. **Return:** `finalize_mutations()` returns. Conversation pipeline resumes or completes.

---

### 2.4 MutationEvent Processing Guarantees

**Atomicity:** All mutations for one turn are committed together — no half-applied state.

**Idempotency:** Running `finalize_mutations(same_events)` twice produces the same outcome (entity extraction is idempotent via `extraction_attempts` tracking).

**Order preservation:** Multiple events in one list are processed in order.

**No rollback:** A memory producer failure does not roll back prior successes. Mutation is best-effort, logged on exception.

**Ordering invariant:** WebSocket publication happens *before* memory writes. This means the WebSocket client sees the event before the backend's semantic memory catches up (intentional — WS events are real-time, memory writes are batch-optimized).

---

## 3. QUERY EXECUTION: "How much did I spend on Swiggy this month?"

**Example flow:** A user asks this via voice. Trace every hop.

### 3.1 Observation Layer: Voice Capture

1. User speaks: `"How much did I spend on Swiggy this month?"`
2. `voice.poll_wake_word()` detects wake word (running continuously in main loop).
3. `voice.record_command()` captures ~5–30 seconds of audio, returns as WAV bytes.

---

### 3.2 Learning Layer: Transcription

1. Whisper model transcribes audio → text: `"How much did I spend on Swiggy this month?"`
2. Transcription confidence score computed (internal to Whisper; not exposed).
3. Returned to `nova.py` run loop.

---

### 3.3 Understanding Layer: Brain Routing

1. **Conversation pipeline entry:** `process_transcript("How much did I spend on Swiggy this month?")`
   - Generates `conversation_id = uuid.uuid4()`.
   - Emits WebSocket: `chat.started`.

2. **Context assembly:** `brain.route()` called.
   - Calls all registered context providers in priority order.
   - Recent activity: Queries `memory.get_recent_money()` (last 20 entries). Returns ~5 entries.
   - Semantic memory: Calls `memory.recall("Swiggy spending this month", k=5)` if LanceDB available. Embeds query, searches LanceDB, ranks by similarity. Returns top-5 memories. _Or_ no-op if LanceDB unavailable.
   - Calendar: Calls `brain._calendar_source()` (injected `calendar.get_events`) — gets today's events + next 3 days. Returns ~3 entries.
   - Profile: Queries `memory.get_profile_observations()`. Returns static profile text (~100 words).
   - Conversation history: Last 10 turns from `brain.history`.
   - All context assembled into one system prompt (see budget logic below).

3. **Token budget enforcement:** Sum all context. If >4000 tokens, trim in reverse priority order (drop conversation history first, then semantic results, then activity, keep calendar/profile always).

4. **System prompt construction:** `brain._build_system_prompt(context)` formats all assembled context into one markdown string (no tool descriptions here; they come separately).

5. **Tool schema preparation:** `ASSISTANT_TOOLS` list serialized to JSON. One tool per supported operation: `get_spending_summary`, `add_task`, `send_whatsapp_message`, etc.

6. **Claude API call:** `brain.client.send_message(system_prompt, [conversation_history], tools=[ASSISTANT_TOOLS])`.
   - Request: `{"model": "claude-3-5-sonnet-20241022", "system": "…", "messages": […], "tools": […], "max_tokens": 1024}`.
   - Response waits (synchronous, non-blocking on main thread).
   - Response: Either `["text": "…", "tool_use": {"name": "get_spending_summary", "input": {"period": "this month"}}]` or just text.

---

### 3.4 Reasoning Layer: Tool Execution

1. **Tool parsing:** Brain detects one `tool_use` block: `get_spending_summary(period="this month")`.

2. **Handler lookup:** `INSTRUMENTED_HANDLERS["get_spending_summary"]({"period": "this month"})` called.

3. **Instrumentation:** Wrapper records `("get_spending_summary", {"period": "this month"}, result)` in `_tool_events`.

4. **Handler execution:** `planner.get_spending_summary("this month")`.
   - Calls `memory.get_money_since()` with date cutoff (start of month).
   - Filters rows where `type` contains "Swiggy" (case-insensitive pattern match).
   - Aggregates amount by type.
   - Formats response: `"You spent ₹2400 on Swiggy so far this month."`
   - Returns formatted string.

5. **Result passed back to Brain:** Claude receives tool result as one `tool_result` message, re-iterates with updated context.

6. **Claude synthesis:** Claude formulates final response: `"Based on your spending records, you've spent ₹2400 on Swiggy this month. Would you like me to track a specific category or set a budget?"`

---

### 3.5 Decision Layer: Mutation Generation

1. **Tool-to-mutation mapping:** `tool_calls_to_mutations(tools_called)` examines all tools executed.
   - This tool (`get_spending_summary`) is a *read-only* tool. No mutation generated.
   - No MutationEvent created.

2. **Journal check:** No journal entry in response, so no journal event.

3. **Fallback memory producer:** Since no mutations, conversation exchange is persisted via `memory_producers.memories_from_exchange(transcript, reply, conversation_id)`.
   - Creates one memory record: `{"text": "User: How much did I spend on Swiggy?\nAssistant: ₹2400", "source_type": "conversation", "tier": "short_term"}`.
   - Passed to `memory.remember()`.

4. **Entity extraction:** `schedule_entity_extraction()` spawns background thread to scan the new conversation memory for entities.
   - Extraction detects: entity_type="product", canonical_name="Swiggy", relation: "mentioned_in" → conversation memory.
   - Writes to `entities` and `edges` tables.

---

### 3.6 Application Layer: Output and Events

1. **Voice output:** `voice.speak("Based on your spending records, you've spent ₹2400 on Swiggy this month. Would you like me to track a specific category or set a budget?")`.
   - Synthesizes audio on-device (if available) or via cloud TTS.

2. **WebSocket events published (in order):**
   - `chat.routing`
   - `chat.tool_called(tool="get_spending_summary", args={…}, result="You spent ₹2400…")`
   - `chat.reply(reply="Based on your spending records…")`
   - `chat.finished`
   - `memory.created(source="conversation")`
   - (Later, async) `entity_extraction.completed(summary="…")`

3. **Conversation history updated:** `brain.history.add_turn(transcript, reply)`.

4. **Return to run loop:** `process_transcript()` completes. Run loop resumes polling for next wake word.

---

## 4. RUNTIME RESPONSIBILITY OF EACH LAYER

### 4.1 Observation Layer

**Components:** `voice.poll_wake_word()`, `voice.record_command()`.

**Sole responsibility:** Capture physical audio from microphone and return as structured data (text or bytes). No interpretation.

**What it does NOT do:**
- Never understands meaning (no NLP in Voice).
- Never stores anything (no database connection).
- Never calls Claude.
- Never triggers domain operations.

**Concurrency:** Runs in main loop as a blocking poll (yields ~50ms per iteration). Wake word detection is local, CPU-bound, no I/O.

---

### 4.2 Learning Layer

**Components:** `services/learning/` (Phase 2+), `brain/context_engine/` (Phase 2.8+).

**Sole responsibility:** Learn patterns from historical data and prepare structured context for reasoning.

**Subcomponents:**

- **Context Engine:** Gather, deduplicate, rank, budget, and format data for Claude's system prompt. No reasoning of its own.
- **Learning Engine (Phase 2.9):** Detect behavioral patterns locally (streak counts, frequency deltas, correlations). Delegate synthesis to Brain.

**What it does NOT do:**
- Never makes decisions (no conditionals based on learned patterns).
- Never modifies storage directly (writes only through Brain/Memory public APIs).
- Never persists patterns as mutable state (only immutable, superseding memories).

**Concurrency:** All learning happens on-demand during `brain.route()`. No background learning jobs exist in v1.0.

---

### 4.3 Understanding Layer

**Components:** `services/brain/`, specifically `brain.route()`, `brain.history`.

**Sole responsibility:** Convert raw transcription + context into Claude API calls. Own conversation history and API interaction.

**Subcomponents:**

- **Routing:** `brain.route(transcript, handlers, history)` — calls Claude once per turn.
- **History:** `brain.history.add_turn(transcript, reply)` — maintains last 20 turns in memory.
- **Context injection:** `brain.set_calendar_source()` — accepts external data sources as dependencies.
- **Reflection:** `brain.run_reflection_job()` — weekly introspection (calls Claude again with different system prompt).
- **Extraction:** `brain.run_entity_extraction()` — batch entity/relationship labeling (calls Claude with structured extraction prompt).

**What it does NOT do:**
- Never executes domain tools directly (handlers are injected, Brain only calls them).
- Never touches storage (Memory is the only storage layer; Brain accesses it via public API only, read-only except for conversation history).
- Never decides what to do (decisions are Claude's to make, not Brain's).

**Concurrency:** Runs in main thread. Claude API calls block (synchronous). Extraction runs async via daemon thread.

---

### 4.4 Reasoning Layer

**Components:** Claude API (external), via `brain.route()`.

**Sole responsibility:** Make semantic decisions on structured input and produce actions.

**Interface:**
- **Input:** System prompt + conversation history + available tools + tool results.
- **Output:** Text reply + zero or more tool calls.

**What it does NOT do:**
- Never sees raw storage (only summaries/context assembled by Understanding Layer).
- Never executes tools (Understanding Layer dispatches).
- Never persists anything (Understanding Layer and below handle persistence).

**Guarantees:** Claude's response is determined by input state; same input always produces same output (deterministic within a model version).

---

### 4.5 Decision Layer

**Components:** `runtime/conversation.py` (tool dispatch), `runtime/mutation_builders.py`, `runtime/mutation_chat.py`.

**Sole responsibility:** Convert tool results into MutationEvents. Orchestrate side-effect persistence.

**Subcomponents:**

- **Tool dispatch:** Execute each tool_use block returned by Claude. Wrap results.
- **Mutation mapping:** `tool_calls_to_mutations()` and `_journal_mutations()` — deterministic, pure functions that map tool results to domain mutations.
- **Memory production:** `apply_memory_producers()` — extract memories from mutations via pattern matching.
- **Event publication:** `publish_mutation_events()` — emit WebSocket events for frontend consumption.

**What it does NOT do:**
- Never changes which tools Claude can call (tool schema is owned by Understanding Layer).
- Never creates a MutationEvent without a domain operation (tools and memory producers only source).
- Never modifies a MutationEvent after creation (frozen dataclass).

**Concurrency:** All decision layer work is synchronous except entity extraction (spawned async).

---

### 4.6 Application Layer

**Components:** `services/` (Voice, Planner, Calendar, Automation, Knowledge), `memory/`.

**Sole responsibility:** Execute domain operations and persist results.

**Subcomponents by service:**

| Service | Operation | Persistence |
|---|---|---|
| Voice | Transcription, TTS | None (ephemeral audio) |
| Planner | Task/money/progress/habit logging; read-side briefings | `memory.add_task()`, `memory.add_money()`, etc. |
| Calendar | Event create/read via AppleScript | macOS Calendar (external) |
| Automation | App launch, WhatsApp, notifications, Pomodoro | None (side effects on macOS) |
| Knowledge | Weather, RSS, GitHub, reflection | `memory.replace_profile_observations()` (reflection only) |
| Memory | All storage operations | SQLite + LanceDB |

**Each service's invariant:** Reads its own domain data; never reaches into another service's tables or business logic.

**What they do NOT do:**
- Never call Claude directly (only via Brain).
- Never publish events directly (Decision Layer does).
- Never import each other (dependencies flow toward Memory/Brain only).

---

## 5. OBJECT LIFETIMES

### 5.1 Long-Lived Objects (Singleton, process lifetime)

| Object | Type | Initialized | Accessed from | Mutability |
|---|---|---|---|---|
| **Whisper model** | `transformers.AutoModelForSpeechSeq2Seq` | `voice.load_model()` at startup | `voice.record_command()` per turn | Immutable (frozen after load) |
| **Brain history** | `list[dict]` of last ~20 turns | `memory.__init__` loads from DB | `brain.route()`, `brain.history.add()` | Append-only (max 20 items, oldest dropped) |
| **Profile cache** | `list[str]` of observations | `memory.__init__` loads from DB | `context_engine/profile_provider` | Replace-only (full rewrite, not mutation) |
| **Calendar source** | `Callable[[], list]` (injected) | `brain.set_calendar_source()` at startup | `context_engine/calendar_provider` | Immutable after injection |
| **Tool handlers map** | `dict[str, Callable]` | `nova.py` startup | `brain.route()` dispatch | Immutable (constructed once) |
| **Event subscribers** | `list[Callable]` | Empty at startup | API server registers on startup | Append-only (never removed) |
| **Memory connection pool** | `sqlite3` connection context manager | Lazy (first query creates) | Every query | Stateless (open/commit/close per query) |
| **LanceDB connection** | `lancedb.DBConnection` | Lazy (first embedding query) | Semantic recall only | Stateless after init |

**Lifetime guarantee:** These objects live from startup to shutdown (Ctrl+C or crash). No recreation mid-session.

---

### 5.2 Request-Scoped Objects (One per turn / API call)

| Object | Scope | Created | Destroyed | Mutability |
|---|---|---|---|---|
| **Conversation ID** | One turn | `process_message()` start | Return from `process_message()` | Immutable (UUID) |
| **System prompt** | One turn | `brain._build_system_prompt()` | After Claude API call | Immutable string |
| **Claude API request** | One turn | `brain.client.send_message()` | After response received | Immutable (JSON) |
| **Tool events list** | One turn | Cleared at turn start: `_tool_events.clear()` | After `tool_calls_to_mutations()` | Append-only during turn |
| **MutationEvents list** | One turn | Built by `tool_calls_to_mutations()` | After `finalize_mutations()` | Immutable (frozen dataclass) |
| **Memory records** | Per memory write | `memory_producers.memories_from_mutations()` | After `memory.remember()` completes | Immutable dict (passed to insert) |
| **Extraction pending batch** | Per extraction job | `brain.run_entity_extraction()` start | After batch processes | Immutable (list of memory IDs) |

**Lifetime guarantee:** Created fresh per turn, garbage-collected after turn completes. No residual state.

---

### 5.3 Immutable Objects

These objects are constructed once and never modified:

- `MutationEvent` (frozen dataclass).
- `ASSISTANT_TOOLS` list (defined once in `brain/tools.py`).
- Conversation context (assembled fresh each turn, never mutated in-place).
- Tool schema JSON.
- Whisper model weights.

**Pattern:** Whenever immutability is required, use `@dataclass(frozen=True)` or module-level constants (`TOOL_HANDLERS`).

---

### 5.4 Cached Objects (Mutable, but caching is transparent)

| Object | Cache strategy | Invalidation | Scope |
|---|---|---|---|
| **Profile observations** | Load once at startup, reload on `replace_profile_observations()` | Manual replace (weekly reflection) | Process lifetime |
| **Conversation history** | Keep last 20 turns in memory | Append new, drop oldest | Process lifetime |
| **Brain context** | Assembled fresh each turn | New providers called per turn | One turn |
| **Task list** | Queried on demand, not cached | No caching (queries live DB) | Per query |

**Principle:** If the cache can become stale (and staleness matters), don't cache. If the data is updated through a known channel (like `replace_profile_observations`), cache is fine. Tasks are queried live because they change too frequently between turns.

---

### 5.5 Recreated Every Request

These are rebuilt from scratch per turn with no state from prior turns:

- System prompt (assembled from live context).
- Claude API request body.
- Tool event recording (list cleared at turn start).
- Mutation event generation (fresh list built per turn).
- WebSocket event payloads.
- Conversation context (gathered from Memory on each `brain.route()` call).

**Rationale:** This design prevents accumulation of stale state and makes each turn independent and debuggable.

---

## 6. THREADING AND ASYNC BOUNDARIES

### 6.1 Main Thread (Run Loop)

**Runs continuously:**

```python
while True:
    # Wake word polling (blocks ~50ms per iteration)
    transcript = voice.record_command()
    
    # Conversation pipeline (blocks ~2-10 seconds)
    process_transcript(transcript)
    
    # Scheduled jobs check (instant)
    check_scheduled_jobs()
```

**Synchronous responsibilities:**

- Wake word polling (polling, not async).
- Whisper transcription (CPU-bound, local).
- Brain API call (network-bound but synchronous).
- Tool execution (each tool runs to completion).
- Memory writes (SQLite synchronous).
- WebSocket publishing (fire-and-forget).

**No blocking I/O outside main thread:** Main thread runs all I/O sequentially. This keeps the state model simple (no race conditions, no locks needed for most data structures).

---

### 6.2 Background Thread #1: Entity Extraction

**Spawned:** Every turn, after `finalize_mutations()`.

**Target:** `brain.run_entity_extraction()`.

**Characteristics:**

- **Daemon thread:** Dies on main thread exit (no wait).
- **Non-blocking:** Spawned with `.start()` and immediately returns.
- **Failure isolated:** Exceptions caught and logged; main thread unaffected.
- **No synchronization:** Does not communicate back to main thread (publishes WebSocket events, but no join).
- **Frequency:** Bounded by main thread (roughly once per turn).

**Why async:** Entity extraction is expensive (calls Claude, network I/O, multiple database writes). If done synchronously, would block voice interactions by 2–5 seconds per turn. Background thread allows extraction to happen while user is speaking next command.

---

### 6.3 Background Thread #2: Reflection Job (Startup only)

**Spawned:** During `AssistantApp.start()` if `should_run_reflection()` is true.

**Target:** `knowledge.run_reflection()`.

**Characteristics:**

- **Blocking startup:** `reflection()` is called synchronously in startup sequence, before run loop begins. This is intentional — run loop should not start until first reflection completes (if needed).
- **Timeout:** No timeout; can block for 30+ seconds if reflection job is large.
- **Frequency:** Once per week (gated by `last_reflection_date`).

**Why synchronous:** Reflection is foundational — it updates the profile, which is loaded into context engine. Running it in background while run loop is active could cause race conditions (rule: profile is read-only during run loop).

---

### 6.4 No Thread for Memory Writes

**SQLite connection:** Each query opens/closes a connection synchronously on main thread.

**Why:** Memory volume is personal-scale (~10K rows). SQLite can handle single-threaded writes at 100–1000 ops/sec. Background queue is overkill and would complicate state machine (where do you queue when queue fills?).

---

### 6.5 Async Boundaries (Hard sync boundaries)

| Boundary | Type | Rule |
|---|---|---|
| Brain → Claude API | Network I/O, async but handled synchronously | Main thread waits for response (no request queueing) |
| Voice → Whisper | CPU I/O, local, synchronous | Main thread blocks until transcription done |
| Conversation → Memory producer | SQLite write, synchronous | All writes done before `process_message()` returns |
| Memory producer → Entity extraction | Background thread spawn | Main thread never waits (async) |
| Entity extraction → Brain API | Network I/O, async but handled synchronously in background | Extraction thread waits for response; main thread independent |

**Golden rule:** Main thread never waits for a network call except to Claude (which is the core interaction). All other network calls (GitHub notifications, weather, RSS) happen in extraction thread or explicitly during scheduled jobs.

---

## 7. LOGGING, TRACING, METRICS, ERROR BOUNDARIES, RECOVERY

### 7.1 Logging Locations

| Layer | What | Where | Format |
|---|---|---|---|
| **Voice** | Transcription confidence, wake word events | Print to stdout | `[voice] heard: "…"` |
| **Brain** | Claude API calls, tool dispatch, errors | Print to stdout | `[brain] routing…` |
| **Memory** | Database writes, schema migrations | Print to stdout | `[memory] created task…` |
| **Extraction** | Entity extraction progress, batches | Print to stdout | `[extraction] processed 20 memories` |
| **Reflection** | Weekly reflection start/end | Print to stdout | `[reflection] running…` |
| **Tools** | Tool execution results | Print to stdout via handler result string | Tool handler returns human-readable confirmation |
| **Errors** | All exceptions | Print to stdout | `[error] routing failed: {exc}` |

**Current logging strategy:** Print-based (stdout). No structured logging (JSON), no log levels (INFO/ERROR/DEBUG), no log files.

**Debt:** Structured logging with levels would improve observability. Deferred to a future iteration.

---

### 7.2 Tracing Points

**Turn tracing:**

1. User speaks → Wake word detected (timestamped).
2. Transcription starts → Transcription ends (duration recorded).
3. Brain routing starts → Brain routing ends (duration recorded).
4. Each tool execution (name, args, result).
5. Memory writes (count, duration).
6. Entity extraction starts (async).
7. Turn complete → WebSocket event published.

**Explicit trace instrumentation:**

- `_tool_events` list captures `(tool_name, args, result)` for each tool — this is the trace buffer for one turn.
- Available to decision layer via `tool_calls_to_mutations()`.
- Optionally published to WebSocket via `chat.tool_called` events.

**Trace retention:** In-memory only (per-turn, garbage-collected after turn completes).

---

### 7.3 Metrics (Not implemented; listed for clarity)

**Missing metrics in v1.0:**

- Turn latency (Brain API call duration).
- Tool execution breakdown (which tools take longest).
- Memory production volume (memories written per turn).
- Extraction batch sizes (entities extracted per job).
- Cache hit rate (context engine provider hits vs. misses).
- API error rate (Claude API failures).

**Debt:** Metrics would help identify performance bottlenecks. Deferred.

---

### 7.4 Error Boundaries

| Component | Error type | Boundary behavior | Recovery |
|---|---|---|---|
| **Voice: wake word** | Audio device not found | Exception raised, startup fails | User must fix hardware/permissions |
| **Voice: transcription** | Whisper timeout | Exception raised, turn fails; conversation continues | Retry next turn |
| **Brain: API call** | Claude API network error | Exception caught, conversation fails for this turn | User repeats command (rate-limited retry by caller) |
| **Brain: API call** | Invalid API key | Exception caught at startup; fatal | User fixes .env, restarts app |
| **Tool: execution** | Tool exception (e.g., AppleScript error) | Exception caught; handler returns error string | Brain sees tool result, synthesizes recovery message |
| **Memory: write** | SQLite constraint violation | Exception caught, memory write skipped | No retry; error logged; turn continues |
| **Extraction: batch** | Extraction timeout or Claude error | Exception caught in background thread; logged | Batch retried next extraction window |
| **Calendar: read** | AppleScript failure | Exception caught; context engine returns empty | Brain plans without calendar context |
| **Reflection: run** | Claude call fails | Exception caught at startup; reflection skipped | Reflection gate remains open; retry next startup |

**General pattern:**

1. **At application boundary (startup):** Errors are fatal. Application does not reach Ready State.
2. **During turn:** Errors are caught and logged. Turn continues or returns user-facing error message.
3. **In background threads:** Errors are caught and logged. Background thread exits silently.
4. **Tool execution:** Errors are converted to user-facing strings. No developer-facing exceptions bubble up.

---

### 7.5 Recovery Strategies

| Failure | Recovery |
|---|---|
| **Claude API rate-limited** | Brain catches exception; user hears "sorry, rate limited". Next turn proceeds normally (Claude decides if retry is appropriate). |
| **Network down (Weather/RSS/GitHub)** | Knowledge service catches exception; context engine skips the provider; Brain proceeds with less context. |
| **Whisper model corrupted** | Startup fails. User deletes `$NOVA_CACHE_DIR/whisper-*.pt` and restarts. |
| **Database locked** | SQLite retries with backoff. If still locked after 5 seconds, query fails; turn continues. |
| **Memory producer write fails** | Turn continues; memory write is skipped (logged). No rollback of prior writes. |
| **Extraction thread deadlock** | No detection. Extraction thread hangs silently; extraction stops happening until app restart. _Debt:_ timeout + thread termination needed. |

---

## 8. WHAT CAN CRASH NOVA

### 8.1 Crash Scenarios (Fatal, kills process)

| Trigger | Component | Cause | Recovery |
|---|---|---|---|
| **Missing API key** | Brain startup | `NOVA_CLAUDE_API_KEY` not in `.env` | User adds key, restarts |
| **Database file corrupted** | Memory `init_db()` | SQLite file unreadable or schema invalid | User deletes `nova.db`, accepts data loss, restarts |
| **Whisper weights download fails** | Voice startup | Network down or disk full | User fixes network/disk, restarts |
| **Whisper model oom** | Voice transcription | Model + audio buffer exceed available RAM | User closes other apps, restarts |
| **Unhandled exception in main loop** | Any | Code bug (not caught by error boundaries) | User restarts; exception printed to stdout |
| **Ctrl+C** | Run loop | User interrupt | Graceful shutdown |

### 8.2 Graceful Degradation (No crash, reduced functionality)

| Trigger | Component | Behavior | User sees |
|---|---|---|---|
| **Claude API down** | Brain | API call fails; error caught | "Sorry, I couldn't process that right now" |
| **Network down** | Knowledge | Weather/RSS/GitHub reads fail | Briefing works, but no weather forecast |
| **LanceDB unavailable** | Memory semantic | Semantic recall disabled | Context is shallow (recent rows only) |
| **Entity extraction fails** | Background thread | Extraction skipped | No graph updates; errors logged |
| **Calendar unavailable** | Calendar context provider | Calendar events not included in context | Briefing works, missing event context |
| **Profile outdated** | Brain context | Stale profile until next reflection | Brain operates with week-old understanding |

### 8.3 Unrecoverable Scenarios

These represent state that cannot be recovered without losing data:

| Scenario | Cause | Why unrecoverable | User action |
|---|---|---|---|
| **All task history lost** | Intentional deletion of `nova.db` before backup | No backup maintained by default | Lost forever; no undo |
| **Extraction thread in infinite loop** | Code bug in `brain.run_entity_extraction()` | No timeout, no way to kill background thread | Restart app (kill -9 as last resort) |
| **Semantic index corrupted** | LanceDB file corruption or version mismatch | No validation/repair tool | Delete LanceDB index; lose all embeddings; rebuild on next startup |
| **Conversation history truncated mid-turn** | Crash during `memory.add_turn()` | Transaction not committed | Restart app; history re-read from DB (partial turn lost) |

---

## 9. RUNTIME INVARIANTS

These statements must NEVER be violated. If code violates one, it is a bug and must be fixed.

### 9.1 Data Flow Invariants

1. **No mutation without event.** Every successful domain operation must produce a `MutationEvent` record.
2. **No event without mutation.** Every `MutationEvent` created must correspond to a completed domain operation (no speculative events).
3. **Event immutability.** Once a `MutationEvent` is created and published, its fields are never modified.
4. **Single source of truth per domain.** Each domain object (task, habit, money, reminder, etc.) has exactly one authoritative table in SQLite. No duplication.
5. **Memory only source of persistence.** No other module opens `nova.db` directly. All writes go through `memory/` public APIs.
6. **Context never mutates during turn.** Context assembled for one `brain.route()` call is never modified in-place. Each turn gets fresh context.
7. **Mutations batch-committed.** All mutations for one turn are committed in one database transaction. No partial turns.
8. **WebSocket events before memory writes.** When both happen, events are published first; memory writes follow. Ensures real-time WS clients see state before database catches up.
9. **Tool results always strings.** Tool handlers must return a string (spoken confirmation), never structured data. Structured data is not propagated to Claude.
10. **Brain never reads storage directly.** Brain's only storage reads come through injected dependencies (`calendar`, context engine providers) or `memory.history.get()`. No `SELECT` statements in `brain/`.

### 9.2 Dependency Invariants

11. **Brain is the only Claude client.** No other module ever calls `anthropic.Anthropic()` or makes Claude API requests. Only Brain does.
12. **No circular dependencies.** Dependency graph is acyclic. If A imports B, B never imports A (directly or transitively).
13. **Services never import each other.** Planner never imports Calendar. Calendar never imports Automation. Cross-service calls happen only through injected handlers in Decision Layer.
14. **Memory never imports services.** Memory is a leaf. It imports nothing but `sqlite3` and `lancedb`.
15. **Knowledge never imports Planner.** Knowledge reads via Memory APIs only. No direct Planner calls.
16. **Voice never imports Brain.** Voice is a leaf. Transcription never goes through Brain for routing.
17. **Calendar never imports Automation.** Calendar is a leaf. Event creation never triggers app launches.
18. **Automation never imports Voice directly.** Pomodoro timer takes `speak` as injected dependency, never imports Voice module.
19. **No service owns two storage systems.** Memory owns SQLite and LanceDB. No other service introduces persistence.
20. **Context providers are read-only.** Context engine providers never modify state. They only read and return data.

### 9.3 Concurrency Invariants

21. **Main thread owns the run loop.** No other thread runs the wake-word polling or Brain routing. Main thread is not shared.
22. **No locks on long-lived objects.** Profile cache, history, tool handlers — none use locks. Main thread has exclusive access.
23. **Daemon threads never join.** Background threads (extraction, reflection) run to completion or silently exit. Main thread never `join()` on them.
24. **Background threads never block main.** Extraction thread spawning is non-blocking. Main thread continues immediately.
25. **Extraction thread isolation.** Entity extraction runs independently. If it crashes, main thread is unaffected.
26. **Memory writes are synchronous.** No write queue. Each `memory.remember()` blocks until committed.
27. **Whisper inference blocks main thread.** Transcription is synchronous, not queued. Main thread waits for result.
28. **Claude API calls block main thread.** Brain routing is synchronous. Main thread waits for Claude response.
29. **No thread pool.** No Executor, no thread pool manager. Threads are spawned explicitly, one at a time.
30. **History is append-only from main thread.** `brain.history.add_turn()` is not thread-safe and must be called from main thread only.

### 9.4 API Contract Invariants

31. **Brain tool handlers take dict, return str.** Every tool handler signature: `Callable[[dict], str]`. No exceptions; no structured output.
32. **Tool handler instruments itself.** `_instrument()` wrapper records tool call metadata. Tools do not report themselves.
33. **Memory producer output is memory records.** `memory_producers.memories_from_mutations()` returns `list[dict]` with keys: `text`, `source_type`, `tier`, `metadata`. No other output shape accepted.
34. **Context provider output is strings or lists.** Each context provider returns either a string (formatted text) or a list of structured items (tasks, events, etc.). No arbitrary dicts.
35. **WebSocket payload structure is fixed.** Every `publish()` call publishes `(channel, event_type, payload_dict)`. Payload keys vary by event type, but structure is always a flat dict.
36. **MutationEvent fields are non-null.** `event_type`, `entity_type`, `operation`, `entity` are always present (though `event_type` can be empty string for memory-only events).
37. **Claude response has well-known structure.** Response is either a text message or contains `tool_use` blocks. Brain never invents response shapes.
38. **Tool schemas are static.** `ASSISTANT_TOOLS` list is defined once; Claude sees the same schema every turn. Schema changes are rare (require app restart).
39. **Reflection output is fixed schema.** Reflection response is always `{"observations": [{text, category, confidence}]}`. Brain parser assumes this structure.
40. **Entity extraction output is fixed schema.** Extraction response is always `{"entities": […], "relationships": […]}`. Brain parser assumes this structure.

### 9.5 Failure Invariants

41. **Errors in background threads don't propagate.** If extraction thread crashes, main thread is unaware and unaffected.
42. **Tool exceptions don't interrupt turn.** If a tool handler throws, exception is caught; handler result becomes error string.
43. **Memory producer exceptions don't rollback.** If one memory producer fails, prior producers' writes stand. No all-or-nothing semantics.
44. **Extraction retries are idempotent.** Running extraction twice on the same memories produces the same result (no double-counting).
45. **Reflection runs at most once per day.** Even if started multiple times, `should_run_reflection()` gate prevents duplicate runs within 24h.
46. **Database constraint violations are non-fatal.** If a write violates a unique constraint, exception is caught; turn continues.
47. **Rate-limited API responses are non-fatal.** Claude API 429 returns exception; Brain catches it; turn fails gracefully.
48. **Network timeouts are non-fatal.** Claude API timeout after 30s; Brain catches it; turn fails gracefully.
49. **Whisper model failure is fatal.** If Whisper crashes during inference, exception is not caught; app restarts.
50. **Profile replacement is atomic.** `replace_profile_observations()` is one transaction. No partial updates.

### 9.6 Lifecycle Invariants

51. **Startup is deterministic.** Same startup steps, same order, every time. No optional initialization paths.
52. **Ready state is all-or-nothing.** Either all startup steps complete, or startup fails. No partially-ready state.
53. **Model is never unloaded.** Whisper model lives in memory until Ctrl+C. No reload, no garbage collection.
54. **History is never cleared except on init.** `brain.history` starts empty (or loaded from DB); it only grows. No explicit clear (except initial `_tool_events.clear()` per turn).
55. **Profile is replaced, not patched.** `replace_profile_observations()` replaces entire list, never patches one field.
56. **Shutdown is immediate.** Ctrl+C calls `sys.exit(0)` immediately. No graceful shutdown sequence; background threads die with main thread.
57. **No app restart during runtime.** App does not restart itself. User must manually restart.
58. **Database file never moves.** Path to `nova.db` is fixed for the entire process lifetime.
59. **Schema version never decrements.** Migrations only increase version. No rollback.
60. **Calendar source is set once.** `brain.set_calendar_source()` is called exactly once at startup, never again. Subsequent calls are no-ops (or error).

---

## 10. NOVA CORE RUNTIME SPECIFICATION v1 (FORMAL)

---

**TITLE:** Nova Core Runtime Specification v1

**VERSION:** 1.0

**FROZEN:** July 5, 2026 (Phase 7 Complete — Unified Desktop Architecture & Finance Domain)

**AUTHORITY:** Principal Software Architect (Runtime Definition)

---

### 10.1 Scope

This specification defines the runtime behavior of Nova Core v1.0 — a single-process, event-driven personal AI assistant. It covers:

1. Application lifecycle (startup, run loop, shutdown).
2. Conversation pipeline (wake word → transcript → Brain → tools → mutations → persistence).
3. Threading model (main thread run loop + background extraction thread).
4. Object lifetimes (long-lived singletons vs. request-scoped objects).
5. Data flow (MutationEvents as the atomic unit of state change).
6. Service responsibilities (seven services + Memory layer, acyclic dependency graph).
7. Error handling and recovery (boundaries, graceful degradation, fatal scenarios).
8. Runtime invariants (60 statements that must never be violated).

**Out of scope:**

- UI/frontend behavior (handled by separate Electron app via REST API).
- Phase 2 or later features (semantic memory, graph, DevBrain, Vision, Learning, Agents).
- Deployment, containerization, or cluster operation (single-process, single-machine only).
- Performance tuning or optimization (this spec describes intended behavior, not fast paths).

---

### 10.2 Core Concepts

**MutationEvent:** An immutable record of one successful business domain operation. All persistence is triggered by MutationEvents. Every MutationEvent is published to WebSocket subscribers before memory writes complete.

```python
@dataclass(frozen=True)
class MutationEvent:
    event_type: str          # e.g., "task.created", "money.logged", "" (empty for memory-only)
    entity_type: str         # e.g., "task", "money", "habit"
    operation: str           # e.g., "create", "complete", "update"
    entity: dict             # domain object data
    metadata: dict = {}      # optional: source, conversation_id, timestamp
```

**Ready State:** The application is in Ready State if and only if:
- Environment variables loaded (`.env`).
- API credentials validated (`NOVA_CLAUDE_API_KEY` present).
- Database initialized and schema migrated.
- Whisper model loaded into memory.
- Calendar dependency injected into Brain.
- Run loop has begun.

Observable: Application prints `"Nova is listening for the wake word…"`

**Conversation Turn:** One complete user → system → user cycle. Input: transcript. Output: reply + zero or more MutationEvents. Latency: 2–10 seconds (dominated by Claude API call).

---

### 10.3 Lifecycle

#### Cold Boot (Startup)

```
main()
  ├─ load_dotenv()                              [read .env, fatal on missing key]
  ├─ AssistantApp().start()
  │   ├─ brain.check_api_config()               [validate NOVA_CLAUDE_API_KEY, fatal on absent]
  │   ├─ memory.init_db()                       [SQLite schema migration, idempotent]
  │   ├─ brain.set_calendar_source(...)         [dependency injection, idempotent]
  │   ├─ knowledge.should_run_reflection()
  │   │   └─ if True: knowledge.run_reflection()    [sync, blocks 2–5 seconds]
  │   ├─ _extract_entities_async()              [spawn background thread, non-blocking]
  │   ├─ voice.load_model()                     [Whisper weights, blocks 5–30 seconds]
  │   └─ _run_loop()                            [main loop begins]
  │
  └─ Ready State Reached
```

**Total startup time:** 5–30 seconds (first run: slower due to Whisper download; subsequent: faster).

#### Run Loop

```
while True:
  ├─ voice.poll_wake_word()                 [blocks ~50ms per iteration]
  ├─ if wake_word_detected:
  │   ├─ voice.record_command()             [capture audio, blocks until silence]
  │   ├─ process_transcript(audio)          [main conversation pipeline]
  │   │   ├─ brain.route()                  [Claude API call, ~2–5 seconds]
  │   │   ├─ tool execution               [optional, ~0.1–1 second per tool]
  │   │   ├─ finalize_mutations()         [WebSocket + memory writes, ~0.1–0.5 seconds]
  │   │   └─ return reply
  │   └─ voice.speak(reply)                [TTS, ~1–5 seconds]
  └─ check_scheduled_jobs()                [instant check, no blocking]
```

**Loop frequency:** ~10–20 iterations per minute (limited by wake word polling + any active conversation).

#### Shutdown (Graceful)

```
Ctrl+C → KeyboardInterrupt
  → AssistantApp.stop()
    → sys.exit(0)
    → Background threads die with main thread
    → No cleanup (connections/files left as-is)
```

**Total shutdown time:** <100ms.

---

### 10.4 Conversation Pipeline (Detailed)

**Input:** Text transcript from voice or API.

**Output:** `ConversationResult { reply: str, tools_called: list, error: Optional[str] }`.

```
process_message(transcript)
  1. Validate transcript (not empty)          [return early if invalid]
  2. Emit WS: chat.started
  3. Call brain.route(transcript, handlers, history)
     a. Assemble context (all providers)
     b. Trim to token budget
     c. Build system prompt
     d. Call Claude API with tools
     e. Parse response
     f. Execute each tool_use block (via handlers dict)
  4. Brain returns: reply text + list of (tool_name, args, result)
  5. brain.history.add_turn(transcript, reply)
  6. Emit WS: chat.tool_called (for each tool)
  7. Emit WS: chat.reply
  8. Emit WS: chat.finished
  9. tool_calls_to_mutations(tools_called)    [deterministic: same tools → same mutations]
  10. If mutations: finalize_mutations(events)
      else: apply_memory_producers([conversation exchange])
  11. schedule_entity_extraction()             [spawn background thread, non-blocking]
  12. Return ConversationResult
```

**Invariant:** No mutation can be created without corresponding tool execution. Memory production is fallback for non-mutating conversations.

---

### 10.5 Threading Model

**Main Thread:**
- Owns the run loop.
- Runs all synchronous I/O (Voice, Brain API, SQLite).
- Never blocked by background work.
- Reads/writes long-lived objects (history, profile, handlers map).

**Background Thread #1: Entity Extraction**
- Spawned once per turn, after `finalize_mutations()`.
- Runs `brain.run_entity_extraction()` asynchronously.
- Failure isolated; main thread unaware.
- Dies silently on exception.
- No communication back to main thread (uses WebSocket for events).

**Background Thread #2: Reflection (Startup Only)**
- Spawned during startup, runs `knowledge.run_reflection()` synchronously.
- Blocks startup until complete (~2–5 seconds).
- One-time per session (gated by `last_reflection_date` timestamp).
- Failure does not halt startup (exception caught, logged).

**Concurrency rule:** Main thread never waits for background work (except reflection at startup). No `join()` calls.

---

### 10.6 Object Lifetimes

**Long-lived (Process lifetime):**
- Whisper model (loaded once, never reloaded).
- Brain history (last ~20 turns, append-only).
- Profile cache (loaded at startup, replaced on reflection).
- Calendar source (injected once, never changed).
- Tool handlers map (immutable, constructed once).
- Event subscriber list (append-only, never cleared).

**Request-scoped (Per turn):**
- Conversation ID (UUID generated per turn).
- System prompt (assembled fresh per turn).
- Tool events list (cleared at turn start, filled during turn).
- MutationEvents (created per turn, immutable).

**Immutable (Never modified after creation):**
- MutationEvent (frozen dataclass).
- ASSISTANT_TOOLS (module constant).
- Context prompt sections (reconstructed, never patched).
- Claude API request/response (JSON, not modified after parse).

---

### 10.7 Error Handling

**Fatal errors (application crash):**
1. Missing `NOVA_CLAUDE_API_KEY` at startup.
2. Database file corrupted (SQLite parse error).
3. Whisper model download fails (network/disk error).
4. Unhandled exception in main loop.

**Non-fatal errors (turn fails, app continues):**
1. Claude API error → user hears "Sorry, I couldn't process that".
2. Tool execution exception → tool result becomes error string.
3. Memory write failure → write skipped, error logged.
4. Extraction thread exception → silently logged, extraction stops.

**Graceful degradation:**
1. Network down (Weather/RSS) → context provider returns empty; Brain proceeds.
2. LanceDB unavailable → semantic recall disabled; context is shallow.
3. Calendar read fails → calendar events omitted from context.

---

### 10.8 Storage

**Database:** SQLite (`nova.db`), single file, no connection pooling.

**Tables:** 8 core + 4 Phase 2+ (conversation_history, memories, entities, edges).

**Transactions:** One transaction per write operation, synchronous commit.

**Indexes:** Task name (unique), due date; Money date; Reminder remind_date; Memory access_count; Entity canonical_name.

**Connection pattern:**
```python
with memory._connection.connect() as conn:
    conn.execute(query)
    conn.commit()
# Connection closed after block exits
```

**Schema version tracking:** `schema_version` table (one row, immutable after first run).

---

### 10.9 API Contracts

**Tool handler signature:** `Callable[[dict], str]`

- Input: JSON dict of tool arguments (from Claude).
- Output: Single string (spoken confirmation or error message).
- Exceptions: Caught by conversation pipeline; converted to error string.

**Memory producer signature:** `Callable[[MutationEvent], list[dict]]`

- Input: MutationEvent.
- Output: List of memory records (dicts with keys: text, source_type, tier, metadata).
- Zero or more records per event (non-1:1 mapping).

**Context provider signature:** `Callable[[], str | list]`

- Input: None (context assembled on every turn).
- Output: String (formatted text) or list (structured items like tasks, events).

**Claude API call:** Standard Anthropic SDK.

```python
response = anthropic.Anthropic(api_key=KEY).messages.create(
    model="claude-3-5-sonnet-20241022",
    system=system_prompt,
    messages=[{role: "user|assistant", content: "…"}],
    tools=[{name, description, input_schema}],
    max_tokens=1024,
)
```

---

### 10.10 Deployment Model

**Single-process, single-machine.**

- No distribution. All services run in one Python process.
- No clustering. No horizontal scaling.
- macOS-only (depends on AppleScript, Whisper on CPU).
- No containerization (references local file paths).

**Future UI (separate Electron process, read-only via REST API):**

- Desktop app communicates with Nova via `services/api` (FastAPI).
- API exposes read endpoints (task lists, memories, graph) + WebSocket push (live events).
- Desktop app never touches `nova.db` directly (all data flows through API).

---

### 10.11 Runtime Invariants (Summary)

**60 invariants stated above** fall into six categories:

1. **Data Flow (10):** MutationEvents, storage exclusivity, context immutability, transactions.
2. **Dependencies (10):** Brain is only Claude client, no circular deps, services are leaves, Memory is exclusive storage.
3. **Concurrency (10):** Main thread owns run loop, no locks, daemon threads, non-blocking spawns.
4. **API Contracts (10):** Tool handlers, memory producers, context providers, Claude response structure.
5. **Failure (10):** Background thread isolation, tool exception handling, database constraints, rate limiting.
6. **Lifecycle (10):** Deterministic startup, Ready state atomicity, model lifetime, history append-only, graceful shutdown.

**Rule:** If any code violates one of these 60 invariants, it is a bug and must be fixed before merge.

---

### 10.12 Known Limitations

These are accepted constraints of v1.0, not bugs:

1. **Single machine only.** No multi-device sync, no backup strategy.
2. **No semantic memory yet.** Embeddings, LanceDB, and semantic recall planned for Phase 2.1.
3. **No knowledge graph yet.** Entity/relationship extraction planned for Phase 2.6.
4. **No background jobs.** Reflection and extraction are ad-hoc, not scheduled. Agents framework deferred to Phase 2.9.
5. **No undo.** Once a mutation is committed, there is no undo mechanism.
6. **No conflict resolution.** If two services try to update the same row, last-write-wins (SQLite default).
7. **No graceful profile degradation.** If reflection fails, profile stays stale until next startup.
8. **No metrics/tracing.** No structured logging, no performance dashboards, no distributed tracing.
9. **No rate limiting on Claude calls.** App will hit rate limits if used heavily; no retry queue.
10. **Entity extraction can deadlock.** If extraction thread gets stuck, no timeout; restart required.

---

### 10.13 Design Principles (Inherited from Roadmap)

1. **One service, one responsibility.** Voice owns audio. Brain owns Claude. Memory owns storage.
2. **Leaves stay leaves.** Services depend on Memory/Brain only, never on each other sideways.
3. **Brain stays agnostic.** Brain never imports a concrete service (tool handlers injected).
4. **Composition root owns wiring.** `nova.py` contains no business logic; only DI and lifecycle.
5. **Public API discipline.** Cross-service calls go through `__init__.py`'s `__all__`, never internal modules.
6. **MutationEvents are the source of truth.** All state changes are recorded as events, persisted asynchronously.
7. **Local-first.** Whisper (not cloud STT), on-device embeddings (when added), no cloud persistence.
8. **Synchronous by default.** Async only where it doesn't block user interaction (entity extraction).

---

### 10.14 Verification Checklist

Before declaring a change "ready to ship":

- [ ] New code does not violate any of the 60 runtime invariants.
- [ ] No new circular dependencies introduced.
- [ ] All public APIs documented in service `__init__.py`.
- [ ] All external service calls go through Brain or injected handlers.
- [ ] All storage writes produce a MutationEvent.
- [ ] No new background threads without explicit approval (background threads complicate reasoning).
- [ ] Error handling has been tested (exception caught, user sees sensible message, app continues).
- [ ] Startup sequence follows the documented steps (no new optional paths).
- [ ] Schema migrations are idempotent (can run multiple times safely).
- [ ] Threading assumptions have been reviewed (no race conditions, no locks needed for new data).

---

### 10.15 References

**Canonical architecture documents:**

- `docs/architecture/ARCHITECTURE_v1.md` — Phase 1 service definitions (frozen).
- `docs/architecture/ARCHITECTURE_v2.md` — Phase 2 design (design-only, not implemented in v1.0).
- `docs/architecture/AI_CONTRACTS.md` — Claude I/O contracts (growing document).
- `apps/backend/runtime/` — Runtime orchestration code.
- `apps/backend/services/brain/` — Brain service (only Claude client).
- `apps/backend/memory/` — Memory service (only persistence owner).

**Code locations (relative to `apps/backend/`):**

- Startup: `nova.py:AssistantApp.start()`.
- Conversation pipeline: `runtime/conversation.py:process_message()`.
- Tool dispatch: `runtime/conversation.py:TOOL_HANDLERS`.
- Mutation pipeline: `runtime/side_effects.py:finalize_mutations()`.
- Event publishing: `runtime/events.py:publish()`.
- Memory production: `memory_producers.py`.
- Brain context engine: `services/brain/context_engine/`.

---

## 11. DOCUMENT CONTROL

**Version:** 1.0

**Status:** Architecture Specification (Frozen)

**Last Updated:** July 6, 2026

**Authority:** Principal Software Architect (Runtime)

**Review Cycle:** This document is frozen with Nova Core v1.0. Updates require explicit new phase approval.

**Debt Tracker:** See §7.1 (logging), §8 (metrics), §9 (invariant enforcement).

---

## 12. APPENDIX: GLOSSARY

| Term | Definition |
|---|---|
| **Ready State** | Application has completed startup and run loop has begun. Observable: "Nova is listening…" message. |
| **MutationEvent** | Immutable record of one successful business operation. All persistence is driven by these events. |
| **Conversation Turn** | One complete user-system cycle (input transcript → output reply). Latency: 2–10 seconds. |
| **Daemon Thread** | Background thread that exits silently when main thread exits. No join(). |
| **Leaf Service** | Service that depends only on Memory (and/or external systems like files/network), never on other services. |
| **Context Assembly** | Process of gathering data for Claude's system prompt (recent activities, profile, calendar, etc.). Happens fresh per turn. |
| **Tool Handler** | Function that executes one domain operation, returns confirmation string. Injected into Brain. |
| **Memory Producer** | Deterministic function that maps MutationEvents to semantic memory records. |
| **Semantic Recall** | Embedding query in LanceDB to find relevant past memories (Phase 2.1+, not in v1.0). |
| **Entity Extraction** | Background job to label entities and relationships from conversation text (Phase 2.7+, basic version in v1.0). |
| **Entity-to-Mutation Mapping** | Deterministic function (`tool_calls_to_mutations()`) that converts tool results into domain MutationEvents. |
| **Schema Migration** | Idempotent SQL steps to upgrade database from one version to next (ALTER TABLE, etc.). |
| **Transaction** | SQLite atomic unit; one turn's writes are one transaction; all commit or all rollback. |
| **WebSocket Event** | Asynchronous message published to all connected clients (API, Electron app, etc.). |
| **Extraction Gate** | Timestamp check (`last_reflection_date`) that prevents reflection from running more than once per 7 days. |

---

**END OF SPECIFICATION**

---

## CERTIFICATIONS

This specification is:

✓ **Authoritative** — Defines the intended runtime behavior of Nova Core v1.0.

✓ **Complete** — Covers lifecycle, threading, data flow, dependencies, errors, and invariants.

✓ **Frozen** — No changes without explicit new phase approval.

✓ **Enforceable** — 60 invariants provide clear boundaries for code review.

✓ **Debuggable** — Developers can trace any issue to a specific layer and invariant violation.

---

**Frozen July 6, 2026 by Principal Software Architect**

**This specification stands until Nova Core v2.0 is approved.**
