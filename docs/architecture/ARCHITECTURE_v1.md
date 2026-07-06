# NOVA — Architecture v1

**Status:** Phase 1 (Architecture Foundation) complete — Milestones 1–8.
**Scope:** This document describes the system as it exists after Bootstrap. It is the canonical reference until Phase 2 changes it.

> **Monorepo path note:** Backend code lives under `apps/backend/`. Paths below are relative to that directory (e.g. `nova.py` → `apps/backend/nova.py`, `memory/` → `apps/backend/memory/`).

---

## 1. High-Level Architecture

```
                              ┌─────────────┐
                              │   nova.py    │  composition root
                              │ (lifecycle) │
                              └──────┬──────┘
        ┌───────────┬───────────┬───┴───────┬───────────┬───────────┐
        ▼           ▼           ▼           ▼           ▼           ▼
   ┌────────┐  ┌─────────┐ ┌────────┐  ┌────────┐  ┌───────────┐┌─────────┐
   │ voice  │  │automation│ │ brain  │  │calendar │  │ knowledge ││ planner │
   └────────┘  └─────────┘ └───┬────┘  └────────┘  └─────┬─────┘└────┬────┘
                                │                          │           │
                                └──────────┬───────────────┴───────────┘
                                           ▼
                                      ┌─────────┐
                                      │ memory  │  (nova.db, SQLite)
                                      └─────────┘

   dashboard.py ──────────────────────────▶ memory   (separate process, read-only)
```

Seven independent services plus one storage layer (Memory), wired together by a single composition root (`nova.py`). `dashboard.py` is a second, independent consumer of Memory — it never imports `nova.py` or any service module that touches audio/AppleScript/Claude.

---

## 2. Folder Structure

```
rai/
├── nova.py                 # composition root: DI wiring, startup, run loop, shutdown
├── dashboard.py            # separate FastAPI process, reads nova.db only
├── nova.db                 # SQLite, owned exclusively by memory/
├── requirements.txt
├── .env / .env.example
│
├── memory/                 # Milestone 1 — the only module that touches nova.db
│   ├── _connection.py      # connection helper (private)
│   ├── schema.py           # init_db()
│   ├── tasks.py  money.py  progress.py  products.py
│   ├── reminders.py  habits.py  profile.py
│   └── __init__.py         # public API surface
│
└── services/
    ├── voice/               # Milestone 2 — mic, wake word, Whisper, TTS
    │   ├── config.py  audio.py  wake_word.py  transcription.py  tts.py  session.py
    ├── brain/                # Milestone 3 — Claude, prompts, history, tool routing
    │   ├── config.py  client.py  prompts.py  history.py  tools.py  reflection.py
    ├── planner/              # Milestone 4 — briefing/plan/schedule + write-commands
    │   ├── config.py  schedule.py  priorities.py
    │   ├── briefing.py  daily.py  evening.py
    │   └── commands.py       # log_task, save_reminder, log_money, get_spending_summary, …
    ├── calendar/              # Milestone 5 — Apple Calendar + NL date/time parsing
    │   ├── applescript.py  parsing.py
    │   └── commands.py       # create_event, describe_events
    ├── automation/           # Milestone 6 — app/URL launch, WhatsApp, notifications
    │   ├── commands.py  whatsapp.py  notifications.py  applescript.py
    │   └── pomodoro.py
    └── knowledge/            # Milestone 7 — weather, RSS, GitHub, reflection, journal
        ├── weather.py  rss.py  github.py  reflection.py  journal.py
```

---

## 3. Service Responsibilities

| Service | Owns | Does not own |
|---|---|---|
| **Memory** | SQLite schema and all CRUD for tasks, money, progress, products, reminders, habits, profile | Any interpretation of the data — no formatting, no NL parsing |
| **Voice** | Microphone, RMS gating, wake-word detection, Whisper STT, TTS, wake/follow-up session loop primitives | What to do with a transcript — it returns plain strings |
| **Brain** | Claude API calls, system prompt construction, conversation history, tool schema + dispatch, weekly reflection reasoning | Any concrete action (WhatsApp, calendar, weather) — it calls whatever handler it's given |
| **Planner** | Morning briefing, evening wrap-up, daily plan, schedule assembly, task prioritization, and the write-commands that combine Memory (+ optionally Calendar): task/money/progress/product/reminder/habit logging, spending summaries | Claude calls (routes through Brain if ever needed — none yet), AppleScript, storage internals |
| **Calendar** | Apple Calendar event create/read via AppleScript, natural-language date/time parsing, and the spoken-confirmation commands built on those two (`create_event`, `describe_events`) | Memory access, Claude |
| **Automation** | macOS app/URL launching, WhatsApp send, notifications, the pomodoro timer | Voice (pomodoro takes `speak` injected rather than importing Voice) |
| **Knowledge** | Weather, RSS, GitHub notifications, the reflection trigger (delegates reasoning to Brain), journal handling (writes to Memory, asks Brain for a reply) | Any Claude *logic* of its own — it's a thin facade for Brain's reflection job |

---

## 4. Public APIs

Each service exposes its contract via `__init__.py`'s `__all__`. Nothing outside a service package should import a submodule directly (e.g. `services.planner.commands` — always go through `services.planner`).

- **memory**: `init_db`, `add_task/complete_task/get_open_tasks/...`, `add_money/get_money_totals_between/...`, `add_progress/...`, `add_product/ship_product/log_sale/get_products`, `add_reminder/get_due_reminders/...`, `log_habit/get_habits_today/...`, `get_profile_observations/replace_profile_observations/...`
- **voice**: `load_model`, `speak`, `new_listener_state`, `poll_wake_word`, `record_command`, `wait_for_followup`
- **brain**: `history` (submodule: `get/add_turn/clear`), `ask`, `route`, `check_api_config`, `build_system_prompt`, `run_reflection_job`, `should_run_reflection`, `ASSISTANT_TOOLS`, `execute_tool`
- **planner**: `build_morning_briefing`, `build_evening_wrapup`, `build_daily_plan`, `prioritize_tasks`, `generate_schedule`, `log_task`, `complete_task`, `log_money`, `log_progress`, `add_product`, `ship_product`, `log_sale`, `save_reminder`, `log_habit`, `describe_habits_today`, `get_spending_summary`, `BRIEFING_TIME`, `EVENING_WRAPUP_TIME`
- **calendar**: `add_calendar_event`, `get_events`, `parse_date`, `parse_time`, `create_event`, `describe_events`
- **automation**: `COMMANDS`, `match_command`, `run_command`, `open_app`, `send_whatsapp_message`, `notify`, `start_pomodoro`
- **knowledge**: `get_weather`, `get_rss_updates`, `get_github_notifications`, `run_reflection`, `should_run_reflection`, `handle_journal`

---

## 5. Dependency Graph

```
memory      — leaf
voice       — leaf
automation  — leaf
calendar     — leaf
brain       → memory
knowledge   → brain, memory
planner     → memory, calendar
nova.py      → voice, automation, brain, calendar, knowledge, planner, memory
```

Acyclic. No service imports `nova.py`. No service reaches into another's internal submodules. `automation.start_pomodoro` takes `speak` as a parameter specifically to avoid an `automation → voice` edge.

---

## 6. Data Flow (voice command example)

```
mic audio
  → voice.poll_wake_word()            [wake word detected]
  → voice.record_command()            → transcript string
  → nova.process_transcript(transcript)
      → brain.route(transcript, TOOL_HANDLERS, history)
          → Claude picks a tool, e.g. add_calendar_event
          → TOOL_HANDLERS["add_calendar_event"](args)
              → calendar.create_event(title, date, time)
                  → calendar.parse_date / parse_time
                  → calendar.add_calendar_event()  [AppleScript]
              → returns spoken confirmation string
      → brain.history.add_turn(transcript, reply)
      → voice.speak(reply)
```

Dashboard's read path is separate and simpler: `dashboard.py → memory.get_*() → HTML template`, polled every ~15s, never touching any other service.

---

## 7. Startup Sequence

1. `main()` checks for `--chat`; if absent, constructs `AssistantApp()`.
2. `AssistantApp.start()`:
   - `brain.check_api_config()` — exits if `NOVA_CLAUDE_API_KEY` is missing (falls back to legacy `RAI_CLAUDE_API_KEY`).
   - `memory.init_db()` — creates tables if absent.
   - `knowledge.should_run_reflection()` → if 7+ days since last run, `knowledge.run_reflection()`.
   - `voice.load_model()` — loads Whisper (may download weights on first run).
   - `AssistantApp._run_loop()` begins.

---

## 8. Shutdown Sequence

- The run loop is wrapped in `try/except KeyboardInterrupt`.
- On Ctrl+C, `AssistantApp.stop()` prints `"Nova stopped."` and calls `sys.exit(0)`.
- No persistent connections are held open between operations — `memory._connection.connect()` is a context manager that opens/commits/closes per call, so there is nothing else to release on shutdown.

---

## 9. Design Principles

- **One service, one responsibility.** Each service's docstring states what it owns and explicitly what it doesn't import.
- **Leaves stay leaves.** Memory, Voice, Automation, Calendar depend on nothing but the standard library + their own config. Cross-cutting concerns (Planner needing both Memory and Calendar) are concentrated in the one service whose charter calls for it, not spread across leaves.
- **Brain stays agnostic.** Brain never imports a concrete service (WhatsApp, Calendar, etc.) — callers hand it a `handlers` dict, and it only knows how to look a name up and call it. This is what let the tool-handler adapters move without touching Brain at all.
- **Composition root owns wiring, not rules.** `nova.py`'s `TOOL_HANDLERS` map is dependency injection — mapping tool names to service calls — not business logic. Anything with a conditional, a format string, or cross-service sequencing beyond a single call was pushed into a service during Bootstrap.
- **Public API discipline.** Cross-service calls go through `__init__.py`'s `__all__`, never a submodule. Bootstrap fixed the one violation found (`nova.py` reaching into `services.planner.config`).

---

## 10. Known Technical Debt

- **Medium:** `planner/briefing.py`'s `weather_provider` callable-injection docstring is stale — it justifies the pattern by Knowledge not existing yet, but Knowledge (Milestone 7) is now complete. The DI pattern itself is still valid; only the rationale comment needs updating.
- **Low:** Planner's charter has grown from purely read-side planning (briefing/daily/schedule) to also include write-commands (`log_task`, `save_reminder`, `log_money`, …). This was the best fit among the 7 existing services for logic spanning Memory+Calendar under the "no new services" constraint, but is worth revisiting if Planner keeps absorbing unrelated write paths.
- **Low:** `nova.py` is 191 lines, above the roadmap's illustrative <100-line example. The excess is the irreducible `TOOL_HANDLERS` map (22 tools) and the `RaiApplication` lifecycle class — no business logic remains, but it's not literally minimal.

None of these block Phase 2.

---

## 11. Future Extension Points

- **Phase 2 (Semantic Memory):** LanceDB + embeddings slot into `memory/` behind the same repository-pattern boundary; `brain/prompts.py` and `brain/reflection.py` are the two call sites that would start consuming semantic retrieval instead of (or alongside) raw recent-rows queries.
- **Phase 3 (Knowledge Engine):** Document/PDF/OCR indexing extends `services/knowledge/` — it already has the "gather information, let Brain reason over it" shape.
- **Phase 4 (Developer Service):** Would be the first genuinely new service since Phase 1 froze the list at 7 — git/project awareness doesn't fit cleanly into any current charter.
- **Phase 21 (Actionable UI, per Chapter 3 roadmap):** Any future write-path triggered from `dashboard.py` should call the same Planner/Calendar/Automation command functions Bootstrap just centralized (`planner.log_task`, `calendar.create_event`, etc.) rather than duplicating logic in the dashboard process.

---

## 12. Phase 2 Entry Criteria

All met as of this document:

- [x] Memory, Voice, Brain, Planner, Calendar, Automation, Knowledge all extracted and independently testable.
- [x] `nova.py` contains no business logic — only DI wiring and lifecycle.
- [x] No circular dependencies.
- [x] No service reaches past another's public `__all__`.
- [x] No duplicated logic (dead regex-command router removed).
- [x] No behavior regressions (verified: tool-handler set unchanged, relocated functions spot-checked against live `nova.db`).

**Phase 2 (Semantic Memory) may begin.**
