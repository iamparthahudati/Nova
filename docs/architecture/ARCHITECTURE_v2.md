# NOVA — Architecture v2 (Phase 2: The Second Brain)

**Status:** Design only. Nothing in this document is implemented.
**Scope:** This document extends [`ARCHITECTURE_v1.md`](ARCHITECTURE_v1.md), which is frozen. Phase 2 adds new leaves and one new orchestration layer on top of the existing eight — it does not modify the responsibilities, public APIs, or dependency edges already established in Phase 1.
**Author role:** Principal AI Architect. Horizon: this system should still make sense in 10 years, not just pass this quarter's roadmap.

> **Monorepo path note:** Backend code lives under `apps/backend/`. Paths below are relative to that directory unless prefixed with `apps/`. The desktop shell lives at `apps/desktop/` (not `desktop/` at repo root).

---

## 0. Governing Rules for Phase 2

Every section below is constrained by these five rules. Where a design choice below looks unusual, it's usually because one of these rules forced it.

1. **Brain is the only Claude client.** No new service (Vision, DevBrain, Learning, Graph, Agents) ever holds an API key or calls Claude directly. They gather and structure data; they hand it to Brain. This is already the pattern Knowledge uses (`knowledge.reflection` → `brain.run_reflection_job`) — Phase 2 generalizes it into a hard rule instead of a convention.
2. **Memory is the only persistence owner — structured *and* vector.** LanceDB does not become a second "owns its own storage" service. It slots inside `memory/`, exactly as v1 §11 already anticipated. No other service opens `nova.db` or a LanceDB connection directly.
3. **New capability = new leaf, not a widened existing service.** Graph, DevBrain, Vision, Learning are each a new top-level package under `services/`, each with one responsibility, each documented with what it does *not* own — same discipline as Voice/Automation/Calendar in v1.
4. **No new service reaches into another's internals.** Same public-`__all__`-only discipline as Phase 1. Cross-service fusion (e.g. "is this screenshot a build error in this project") happens in Brain, which is allowed to depend on everyone; leaves never depend on each other.
5. **Local-first stays local-first.** Embeddings, OCR, and wake-word-style detection run locally where a local model exists (mirrors the Whisper precedent from Phase 1). Claude is reserved for reasoning that actually needs it. This is a cost and privacy constraint, not a preference.

---

## 1. Overall Phase 2 Architecture

```
                         ┌─────────────────────────────────────────┐
                         │              Future UI (§9)              │
                         │   Electron desktop — separate process    │
                         └───────────────────┬───────────────────────┘
                                              │ HTTP/WebSocket only
                         ┌───────────────────▼───────────────────────┐
                         │         services/api  (read + push)       │
                         └───────────────────┬───────────────────────┘
                                              │
        ┌──────────────┬──────────────┬──────┴───────┬──────────────┬──────────────┐
        ▼              ▼              ▼              ▼              ▼              ▼
  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐
  │  agents   │  │ learning  │  │  graph    │  │ devbrain  │  │  vision   │  │  (Phase 1 │
  │   (§8)    │  │   (§7)    │  │   (§4)    │  │   (§5)    │  │   (§6)    │  │  services │
  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘  │  unchanged│
        │              │              │              │              │        │  — §below)│
        └──────────────┴──────────────┴──────┬───────┴──────────────┘        └─────┬─────┘
                                              ▼                                     │
                                    ┌───────────────────┐                           │
                                    │       brain        │◀─────────────────────────┘
                                    │ (only Claude client)│
                                    └──────────┬──────────┘
                                              ▼
                                    ┌───────────────────┐
                                    │       memory        │
                                    │  SQLite + LanceDB   │  ◀── owned exclusively by memory/
                                    │  (§2, §3)            │
                                    └───────────────────┘
```

The eight Phase 1 services (Memory, Voice, Brain, Planner, Calendar, Automation, Knowledge, Bootstrap/`nova.py`) sit unchanged at the base. Phase 2 adds:

| New unit | Kind | Depends on | Depended on by |
|---|---|---|---|
| `memory/semantic.py` | extension of existing Memory service, not a new service | (SQLite, LanceDB — internal) | brain, learning, graph, vision |
| `services/graph` | new leaf-ish service | memory | brain, learning, devbrain (read) |
| `services/devbrain` | new leaf service | (filesystem, git — external) | brain |
| `services/vision` | new leaf service | memory (to store OCR text) | brain |
| `services/learning` | new service | memory, graph, brain | agents, planner (read) |
| `services/agents` | new orchestration service | learning, planner, knowledge, memory, automation | `nova.py` (one call, see §8) |
| `services/api` | new read/push facade | memory, graph, planner, devbrain, agents | desktop UI only |
| `desktop/` | new external process (Electron) | `services/api` over the network | nothing (leaf consumer) |

`nova.py` gains exactly one new line in its run loop (`agents.run_due_jobs()`) — everything else is additive at the service layer, so the "no business logic in `nova.py`" rule from Phase 1 is never violated.

---

## 2. Semantic Memory

### Split of responsibility

| Belongs in SQLite | Belongs in LanceDB |
|---|---|
| Existence, lifecycle, and scoring of a memory (id, source, tier, importance, access stats, timestamps, `deleted_at`, `supersedes_id`) | The embedding vector itself |
| Everything that needs a transactional write (a single UPDATE to bump `access_count`) | A denormalized copy of the memory text + minimal metadata (source_type, tier, created_at) needed to render a result *without* a round-trip to SQLite on the hot path |
| Relationships to other rows (task/product/profile ids the memory references) | Nothing that is ever the sole source of truth — LanceDB is a derived index, rebuildable from SQLite |

Concretely, Memory gains one new SQLite table, `memories`, which is the **ledger**: one row per memory, holding everything needed to rank and manage it. LanceDB holds one table, keyed by the same UUID as `memories.id`, holding the vector + the searchable payload. If LanceDB were deleted entirely, it could be fully rebuilt by re-embedding every row in `memories` — that rebuildability is the test for "did we put the right thing in the right store."

### Embedding generation

A local embedding model (small sentence-transformer class, CPU-friendly) runs inside `memory/semantic.py`, behind an `EmbeddingProvider` interface so the model is swappable without touching callers. This mirrors the Whisper precedent: local, no per-call cost, no network dependency, no second API key. Embeddings are generated synchronously at write time for now (memory volume is personal-scale, not enterprise-scale) — if write latency ever becomes a problem, this is the one place a background queue would go, not a reason to redesign the boundary today.

### Who writes memories

Any Phase 1 or Phase 2 service that produces something worth remembering calls one new Memory API function — `memory.remember(text, source_type, source_id, metadata)`. Candidate producers: Brain (conversation turns), Knowledge (journal entries), Vision (OCR text), DevBrain (session summaries), Learning (weekly insights). Memory is the only thing that decides *how* it's stored (embedding, tiering, table writes) — producers never touch SQLite or LanceDB directly, same discipline v1 established for the original six tables.

### Retrieval

`memory.recall(query, k, filters=None)` embeds the query, runs ANN search in LanceDB for a candidate set, joins each candidate against its `memories` row in SQLite for tier/importance/access stats, applies the ranking formula from §3, and returns the top-k. This is the concrete integration point v1 §11 already flagged: `brain/prompts.py`'s `build_system_prompt()` moves from "always dump the 5 most recent rows of each table" toward "recall what's relevant to *this* turn," with the existing flat queries kept as a fallback for cheap, always-relevant context (today's open tasks) that doesn't benefit from semantic search.

### Updates, deletion, versioning

- **Updates are supersession, not mutation.** A "changed" memory (e.g. a corrected profile observation) is written as a new row with `supersedes_id` pointing at the old one. The old row's tier moves toward `archived` rather than being overwritten. This is what lets the Learning Engine (§7) diff this week's understanding against last week's — mutating in place would destroy that signal.
- **Deletion is two-phase.** A `deleted_at` timestamp on the SQLite row makes a memory invisible to `recall()` immediately — this is the correctness-critical half, and it's a single SQLite UPDATE. The matching LanceDB vector is removed in batches by the nightly maintenance job (§8), since LanceDB is more efficient compacted than deleted-one-row-at-a-time. Until that sweep runs, the vector is orphaned but unreachable (recall always joins back to SQLite and filters `deleted_at IS NULL`), so there's no correctness gap, only a temporary storage cost.
- **Versioning is the `supersedes_id` chain**, not a separate version table. Walking the chain reconstructs history for any memory; the current tip is whichever row in the chain has no successor.

---

## 3. Memory Ranking

### Tiers

| Tier | Meaning | Typical residency |
|---|---|---|
| Short-term | This conversation / today | Hours |
| Medium-term | This week's active context | Days to ~2 weeks |
| Long-term | Durable — promoted because it keeps proving useful | Indefinite |
| Archived | Superseded or stale, but kept for history/audit | Indefinite, cold |
| Forgotten | Soft-deleted, pending hard purge | Until next maintenance sweep |

Tiers are not set once at write time — they're recomputed by the nightly maintenance job in §8, based on the composite score below. A memory only reaches `long-term` by *earning* it (repeated relevance), not by being written with high initial importance.

### Score components

- **Importance** (0–1, set at write time): a cheap heuristic score based on source type and signal strength — e.g. an explicit profile/goal statement scores higher than a passing remark in casual conversation; a journal entry scores higher than a routine task log. This is a starting prior, not a final judgment.
- **Recency**: exponential decay, with a *different half-life per tier* — short-term decays in hours, long-term decays over months. A memory that's aging out of its current tier's half-life is a candidate for demotion; one that keeps getting recalled despite decay is a candidate for promotion.
- **Retrieval score**: reinforcement from actually being useful — every time `recall()` returns a memory and it's used (i.e. survives into a Brain response), `access_count` increments and `last_accessed_at` updates. This is the spaced-repetition-like signal: memories that keep getting pulled back into relevance earn their way to `long-term`; memories nobody ever recalls decay toward `archived` regardless of their initial importance score.

### Composite score (conceptual)

At query time: `similarity` (from ANN search) is blended with `importance`, `recency_decay`, and `log(access_count + 1)` to rank candidates. At maintenance time (no active query), the same importance/recency/access signal — *without* the similarity term — decides tier transitions: below a threshold and unaccessed past its tier's window → demote; consistently above threshold → promote; below the floor for long enough → forgotten.

The exact weights are a tuning problem, not an architecture problem — they're a config value the Learning Engine (§7) is explicitly allowed to adjust over time as it observes what actually turns out to matter to the user, which is the beginning of Nova "getting better every week" rather than being hand-tuned once.

---

## 4. Knowledge Graph

> **Amendment (2026-07-05, Milestone 2.7 — Entity Extraction):** the "extraction is a Brain job" sentence below is now implemented. The output contract is code-canonical in `services/brain/extraction_contract.py` (schema + validator + parser; registered in `AI_CONTRACTS.md` §2.4); the Claude call and persistence live in `services/brain/extraction.py`, which writes only through Memory's public verbs (`create_entity`, `link_entities(source_memory_id=…)`) — same precedent as reflection. Extraction runs as an idempotent, batched *pending-sweep*, not inline in `remember()`: the `memories` ledger gained `entities_extracted_at` + `extraction_attempts` (Memory tracks *which rows were processed*; Brain owns *what the text means*), so failures retry automatically, a poison-pill row is abandoned after a bounded number of attempts, and pre-2.7 history backfills through the same path. The composition root fires the sweep on a background thread after each turn and once at startup — wiring only, no judgment. One numbering note: this document's §11 table predates the shipped milestone stream (2.4 conversation memory, 2.5 memory producers, 2.6 knowledge graph, 2.7 entity extraction); `AI_CONTRACTS.md`'s registry is the milestone-numbering source of truth from 2.6 onward.

> **Amendment (2026-07-04, Milestone 2.6):** implemented as `memory/graph/`, not `services/graph`. Rationale: Rule 2 forbids a graph service from owning persistence and Rule 1 forbids it from reasoning, so a `services/graph` package would have been an empty pass-through around Memory calls. Edges also reference `memories.id` (provenance) — an intra-database relationship that belongs with the tables' owner. The graph is an *extension of Memory*, exactly like `memory/semantic/`: two SQLite tables in `nova.db`, public verbs re-exported through `memory/__init__.py` (`create_entity`, `get_entity`, `find_entity`, `delete_entity`, `link_entities`, `entity_edges`, `delete_edge`, `related_entities`). Everything else in this section (schema shape, SQLite-not-Neo4j, extraction is a Brain job, `brain → memory(graph)` dependency direction) stands as written; references to "services/graph" elsewhere in this document should be read as "memory/graph".

### Why not a dedicated graph database

At personal scale — thousands of entities and edges, not billions — a dedicated graph engine (Neo4j, Kuzu, etc.) is a new infrastructure dependency for a problem SQLite's recursive CTEs already solve. Two tables, inside the same `nova.db` Memory already owns, are enough. This can be revisited if traversal complexity or edge volume genuinely outgrows SQLite — that's a concrete, observable trigger, not a hypothetical one.

### Schema (conceptual)

`entities`: id, type, canonical name, free-form attributes, created_at.
`edges`: id, from_entity_id, to_entity_id, relation_type, weight, created_at, and provenance (which memory/conversation/source produced this edge).

### Entity types

Person, Project, Task, Goal, Habit, Meeting, Document, Conversation, Product — the nouns already implicit in Phase 1's tables (tasks, products, profile) plus the ones Phase 1 never modeled relationally (people, projects, meetings, documents).

### Example relations

`person —WORKS_ON→ project`, `task —BELONGS_TO→ project`, `meeting —INVOLVES→ person`, `document —RELATES_TO→ project`, `conversation —MENTIONS→ person | project`, `habit —SUPPORTS→ goal`, `product —PART_OF→ project`.

### Population and dependency direction

`services/graph` is a **leaf**, like Memory — it stores and queries entities/edges but does not itself decide what's an entity or a relation (that's an extraction judgment, which is a Brain job per Rule 1). The direction is: Brain (or a cheap local heuristic pass for unambiguous cases, e.g. an `@mention`-style pattern) extracts entities/relations from conversation, journal, and calendar text, then calls `graph.link(...)` to persist them. Graph never calls Brain — this keeps `brain → graph → memory` acyclic, matching the existing `brain → memory` pattern from Phase 1.

### Query surface

`graph.related(entity, relation_type=None, depth=1–2)` — used by Brain to enrich context ("who else is on this project," "what's this document about") and by Planner/DevBrain for cross-referencing project ↔ task ↔ person.

---

## 5. Developer Brain

`services/devbrain` is a new leaf, same tier as Calendar/Automation: it reads external state and exposes structured facts. It does not import Brain, Memory, or Planner directly, and nothing it does is destructive — this is a read-only observation service.

### Avoiding stack coupling

DevBrain never hardcodes "this is a React Native project" logic inline. It defines one normalized shape — a `ProjectContext` (name, language/stack, package manager, last commit, dirty files, detected build tool) — and a set of small, independent detectors that each know how to recognize *one* stack from its marker files (`package.json` → Node, `build.gradle`/`AndroidManifest.xml` → Android, `metro.config.js` → React Native, `.git` → repo-level facts common to all). This is the same plugin-shape Roadmap v4 already mandates for Automation ("new automation can be added without modifying existing plugins") — reused here rather than invented fresh, so a sixth stack later is a new detector, not a rewrite.

### Scope

- **Git/repo awareness**: current branch, recent commits, dirty/staged files, diff summary — read via `git` CLI calls, no libgit2 dependency needed at this scale.
- **Project awareness**: which `ProjectContext` the user is currently in (inferred from the active terminal/VS Code working directory, surfaced via Automation's existing window/app detection primitives rather than DevBrain reinventing that).
- **Build errors**: DevBrain does not run builds or watch processes in the background — it accepts error text handed to it (from a terminal paste, or from Vision's OCR of a terminal window, §6) and classifies it against the current `ProjectContext` (e.g. "this looks like a Metro bundler error in the RN project" vs. "this is a Gradle error"). Classification of *what the error means* is Brain's job; DevBrain only supplies the stack context that makes Brain's answer specific instead of generic.
- **VS Code**: read via workspace files (`.vscode/settings.json`, open-folder path) and git status — no custom VS Code extension in Phase 2. A live extension that streams editor state is a legitimate future milestone, but it's a new client integration surface, not a service-architecture decision, so it's explicitly deferred (see §11).
- **"Continue yesterday's work"**: DevBrain assembles the `ProjectContext` + recent commits + any DevBrain-tagged memories (session summaries it wrote via `memory.remember`); Brain synthesizes the actual "here's where you left off" narrative.

---

## 6. Vision

`services/vision` is a new leaf. Scope: screenshot capture, OCR, window/app detection, and — as a Brain-mediated capability, not a Vision capability — UI/error understanding.

### Pipeline

```
capture (explicit ask, or low-frequency opt-in snapshot)
  → window/app detection (which app owns this screenshot)
  → local OCR pass (always — cheap, no Claude call)
  → memory.remember(text, source_type="screen", metadata={app, window_title})
  → [only if the user asks, or Agents' periodic desktop-awareness job fires]
      → Brain (Claude vision call) for actual interpretation
      → e.g. "this is a build error in the RN project" (DevBrain context fused in by Brain)
```

The OCR pass is cheap enough to run on every capture and feed straight into Memory — this is what makes "what was I looking at when I had that idea yesterday" answerable via ordinary semantic recall, without needing a Claude vision call for every screenshot. The *expensive* step (an actual Claude vision call to understand layout, diagnose an error, read a chart) is gated behind explicit user request or a deliberately low-frequency Agent job — never continuous — for both cost and privacy reasons.

### Screen memory / desktop awareness

Periodic capture is opt-in and off by default. When enabled, it runs at a low, user-configured frequency, and only while the user is actively at the machine (not while idle/locked). Before any capture leaves the local OCR step, it's checked against a user-configurable app blocklist (password managers, banking apps, anything the user names) — enforced inside Vision, before the text ever reaches `memory.remember`, so blocked content never enters the ledger at all rather than being filtered after the fact.

### Relationship to DevBrain

Vision supplies pixels → text. DevBrain supplies "what stack is this." Neither imports the other — Brain is the fusion point, consistent with Rule 4. This avoids the temptation to let Vision grow a build-error-classification feature of its own, which would duplicate DevBrain's charter.

---

## 7. Learning Engine

`services/learning` is new. It owns *how Nova's understanding of the user changes over time* — the part of the system responsible for "gets better every week."

### Relationship to existing reflection

Phase 1 already has a primitive version of this: `knowledge/reflection.py` triggers a weekly job that calls `brain.run_reflection_job()`, which rewrites `profile` via `replace_profile_observations()`. Learning does not replace this — Knowledge's public API (`run_reflection`, `should_run_reflection`) is untouched, per the "no redesign of Phase 1" constraint. Learning is what the reflection job becomes *deeper*, and it's invoked by Agents (§8) alongside, not instead of, Knowledge's existing trigger.

Two concrete changes Learning brings:

1. **Profile writes become versioned**, using the supersession pattern from §2, instead of `replace_profile_observations`'s delete-and-reinsert. This is the one place Phase 2 asks for a behavior change to existing Phase 1 code — flagged explicitly because it's the exception to "don't touch Phase 1," and it's additive (old behavior still works; supersession just stops throwing away history).
2. **Pattern detection runs on more than raw recent rows.** Learning reads Memory's access/importance signals (what's actually been recalled and relied on), Graph's edges (what's connected to what), and the structured tables (habit streaks, task completion rates, spending trends) to detect: routines (repeated same-time actions → habit candidate), drift (a profile observation increasingly contradicted by recent behavior → confidence should decay), and correlations worth surfacing (e.g. task completion drops in weeks with no logged exercise).

### Cost discipline

Cheap statistical pre-filters (streak counts, frequency, simple deltas) run locally in `services/learning` first. Only the synthesis step — turning "these three patterns co-occurred" into a coaching-quality sentence — goes to Brain, and only for the patterns that cleared the local pre-filter. This follows the same "route routine work locally, save Claude for what needs it" principle already stated in the original roadmap for Phase 3 (the NL brain).

### Output

Learning never speaks to the user directly. It writes structured "insight" memories (via `memory.remember`, tagged `source_type="insight"`) and nudge candidates. Planner's existing morning/evening briefing assembly and Agents' notification jobs are the two consumers that turn insights into something the user actually sees or hears — Learning stays a pure analysis service, with no notification, voice, or UI logic of its own.

---

## 8. Agent System

`services/agents` is new — the background-orchestration layer that Phase 1 never needed because everything before Phase 2 was reactive (triggered by a wake word or a dashboard poll).

### Job catalog

| Job | Cadence | What it does | Reuses |
|---|---|---|---|
| Memory maintenance | Nightly | Recompute tiers/scores (§3), hard-purge soft-deleted memories, compact LanceDB | `memory.semantic` internals |
| Daily review | End of day | Feeds Learning's local pre-filters + today's data into Planner's evening wrap-up | `planner.build_evening_wrapup` |
| Weekly review | Weekly | Triggers Learning's full pattern-detection pass + Knowledge's existing reflection cadence; produces a "week in review" insight memory | `learning`, `knowledge.run_reflection` |
| Monthly review | Monthly | Aggregates the month's weekly insights — mostly reads, minimal new Claude calls | `learning` (read) |
| Notifications | Event-driven | Surfaces due reminders, Learning nudges, and job results via macOS notifications | `automation.notify` (unchanged) |
| Suggestions | Event-driven, rate-limited | Turns high-confidence Learning insights into a single actionable prompt (not a stream of nagging) | `learning`, `automation.notify` |

### Scheduling

No new external scheduler (cron, Celery, etc.) — that would be an infrastructure dependency the single-process, local-first design doesn't need at this scale. Agents generalizes the timestamp-gate pattern Knowledge already uses (`should_run_reflection()`) into a small internal registry of `(job_name, cadence, last_run source)` entries, checked on each tick. `nova.py`'s run loop gains exactly one call — `agents.run_due_jobs()` — alongside its existing loop body. That single call is the entire footprint Phase 2 has in `nova.py`; every cadence rule and every job's logic lives inside `services/agents` and the services it orchestrates.

### Dependency direction

`agents → learning, planner, knowledge, memory, automation` — Agents is allowed to depend on almost everything because it's a pure orchestrator, the same role `nova.py` plays for Phase 1's wiring. It holds no business logic of its own beyond "is job X due, and if so, call it" — identical in spirit to the composition-root discipline already enforced on `nova.py`.

---

## 9. Future UI

### Why an API facade first

`dashboard.py` already proved the shape (a second process, reading Memory, no imports of anything voice/AppleScript-touching) but also already has one architecture violation the review report flagged: it re-implements Calendar's AppleScript fetch instead of calling `calendar.get_events()`. Phase 2 does not repeat that mistake for the Electron app — an Electron/React process is JavaScript, so it *cannot* import Python services directly even if it wanted to. That constraint is actually a forcing function for the right design: a `services/api` facade (FastAPI, extending — not replacing — what `dashboard.py` already runs) becomes the single, enforced boundary. There is no way for the desktop app to duplicate Calendar's AppleScript logic, because it has no Python import path to duplicate it *from*.

### Surface

- **Read endpoints**: memory recall, graph queries, planner briefing, task/habit/product lists — thin wrappers around each service's existing public API, no new logic.
- **WebSocket channel**: live push for voice transcript state, notification events, and agent job status — an upgrade path for `dashboard.py`'s current ~15s polling, not a replacement (`dashboard.py` keeps working unchanged; nothing about it breaks).

### UI surfaces on top of that API

- **Floating assistant** — an always-on-top overlay, the first real visual replacement for "watch the terminal," for quick voice/text interaction.
- **Sidebar** — contextual panel: current project (DevBrain), today's plan (Planner), recent insights (Learning).
- **Dashboard** — the existing metrics view, ported to React, same data it shows today.
- **Widgets** — small composable views (habit tracker, spending, product pipeline) usable inside the floating assistant or a home view.
- **Voice overlay** — visual waveform/transcript feedback while Voice is listening — today's Voice service has zero visual feedback (terminal print statements only); this is purely a UI-side consumer of the WebSocket transcript stream, no change to `services/voice` itself.

The Electron app never talks to SQLite, LanceDB, or any service module directly — network only, through `services/api`. That's the whole point of introducing the facade.

### Desktop scaffold (`apps/desktop/`)

A working Electron + React shell exists today at `apps/desktop/` (not yet wired to `services/api`):

| Piece | Implementation |
|-------|----------------|
| Renderer | React 19, React Router (hash), Zustand, Tailwind 4, shadcn/ui — mock data only |
| Main / preload | TypeScript; preload exposes `window.desktopWindow` for custom title-bar IPC |
| Dev / build | **Vite 8 + `vite-plugin-electron@^1.1.0`** — single `npm run dev` command |
| Output | `dist/` (renderer), `dist-electron/main.js` + `dist-electron/preload.mjs` |
| Packaging entry | `package.json` `"main": "dist-electron/main.js"` |

Development workflow (see [`apps/desktop/README.md`](../../apps/desktop/README.md)):

```bash
cd apps/desktop
npm install
npm run dev      # Vite HMR + Electron hot restart/reload
npm run build    # tsc -b + vite build
npm run start    # electron .
```

The plugin sets `process.env.VITE_DEV_SERVER_URL` during dev; main loads that URL in development and `dist/index.html` in production. API integration is a separate milestone.

---

## 10. Dependency Graph (Complete, Post-Phase-2)

```
Leaves (no Phase 2 service dependencies):
  memory        (SQLite + LanceDB, extended — still owns all persistence)
  voice         (unchanged)
  automation    (unchanged)
  calendar      (unchanged)
  graph         (→ memory only)
  devbrain      (→ filesystem/git only; external, not another service)
  vision        (→ memory only, to store OCR text)

One level up:
  brain         → memory, graph                     (only Claude client — Rule 1)
  knowledge     → brain, memory                      (unchanged from Phase 1)
  planner       → memory, calendar                   (unchanged from Phase 1)
  learning      → memory, graph, brain

Orchestration:
  agents        → learning, planner, knowledge, memory, automation

Facade:
  api           → memory, graph, planner, devbrain, agents   (read-only)

Composition root:
  nova.py        → voice, automation, brain, calendar, knowledge, planner, memory, agents
                  (one new dependency vs. v1: agents — for the single run_due_jobs() tick)

External processes (no Python import edges — network only):
  dashboard.py  → memory (unchanged, direct — legacy path, still valid)
  desktop/      → api    (new — the only way the Electron app touches Nova)
```

Acyclic, same as Phase 1. The only genuinely new *kind* of edge is `desktop/ → api` — a network boundary rather than a Python import — which is intentional: it's the first consumer that architecturally *cannot* cheat by reaching past a public API, because it has no Python import path available to it at all.

---

## 11. Roadmap

> **Amendment (2026-07-05, Milestone 2.8 — Context Engine):** prompt assembly is no longer `brain/prompts.py`'s string pipeline — it is `services/brain/context_engine/`, one orchestration pipeline (collect → dedup → rank → budget → format) over independent providers: recent activity, semantic memory, knowledge graph (the first hot-path *reader* of what 2.6/2.7 built), open tasks, calendar, user profile, and recent conversation (which feeds the `messages` channel, never the system string). `prompts.py` is formatting-only; `client.py` consumes one `assemble()` per turn; the reinforcement half of the recall loop moved to `brain/reinforcement.py` unchanged. Two boundary rules were preserved rather than bent: Brain still imports only Memory (the calendar provider's fetch function is **injected by `nova.py`** via `brain.set_calendar_source()` — the same DI shape as `TOOL_HANDLERS`), and the graph stays read-only from Brain (the provider uses only `find_entity`/`entity_edges`/`get_entity`). Every section now has a token budget and there is a global ceiling with a fixed trim order; all knobs are env-tunable (`NOVA_CONTEXT_TOKEN_BUDGET` etc.). Numbering note (same as 2.7's): the table below predates the shipped milestone stream — its "2.8 Learning Engine" row is now a later milestone; `AI_CONTRACTS.md`'s registry remains the numbering source of truth.

Each milestone below is independently testable and independently deployable — it can ship and be verified without any milestone after it existing yet, matching the Definition-of-Done already established in Phase 1 (single responsibility, public API, no circular deps, unit-testable, no regressions).

| # | Milestone | Adds | Testable by |
|---|---|---|---|
| 2.1 | Semantic Memory Core | `memory/semantic.py`: local embedding provider, `remember()`, `recall()`, LanceDB wiring behind Memory's existing boundary. No consumers yet. | Direct unit tests against Memory's API — write memories, recall by query, assert ranking by similarity alone. |
| 2.2 | Memory Ranking & Lifecycle | `memories` ledger table, tier field, composite scoring, soft delete. Still no consumers. | Seed memories with synthetic timestamps/access counts, assert tier transitions and forgetting thresholds. |
| 2.3 | Brain Integration | `brain/prompts.py` starts calling `memory.recall()` for context, alongside existing flat queries. First real behavior change. | Ask Nova about something from weeks ago that was never in "recent rows" — it should now answer correctly. |
| 2.4 | Knowledge Graph | `services/graph`: entities/edges schema, `graph.related()`, a first extraction pass over existing conversation history via Brain. | Query `graph.related()` directly; verify entities/edges match a manually-checked sample of past conversations. |
| 2.5 | Developer Brain | `services/devbrain`: git/project read-only adapters (Node/Android/RN detectors), Brain tool integration. | Ask "what am I working on" in each of the three sample project types; verify correct stack detection. |
| 2.6 | Vision — Capture & OCR | `services/vision`: screenshot capture, window detection, local OCR, `memory.remember()` wiring. No Claude vision calls yet. | Screenshot a terminal error, then semantically recall its text later. |
| 2.7 | Vision — Understanding | Brain-mediated Claude vision calls, fused with DevBrain's `ProjectContext`. | Ask "what's wrong with this screenshot" on a real build error; verify the stack-specific diagnosis. |
| 2.8 | Learning Engine | `services/learning`: local pre-filters, Brain-synthesized insights, versioned (supersede) profile writes replacing `replace_profile_observations`'s delete-and-reinsert. | Run two consecutive weekly cycles on the same data with one deliberate behavior change between them; verify the insight correctly names the drift. |
| 2.9 | Agent System | `services/agents`: job registry, the six jobs in §8, single `run_due_jobs()` hook into `nova.py`. | Fast-forward cadence gates in tests; verify each job fires exactly once per due window and notifications reuse `automation.notify` unchanged. |
| 2.10 | API Facade | `services/api`: FastAPI read endpoints + WebSocket push, wrapping existing service APIs only. `dashboard.py` optionally migrated to consume it (not required to). | `curl`/WebSocket client against each endpoint; verify `dashboard.py`'s existing behavior is unaffected if left unmigrated. |
| 2.11 | Desktop Shell — MVP | `desktop/`: Electron scaffold, floating assistant + voice overlay, consuming `services/api` only. | Manual verification: voice interaction and live transcript render correctly with zero direct Python imports in the Electron codebase. |
| 2.11a | Desktop — Sidebar | Contextual panel (DevBrain project + Planner briefing + Learning insights), same API. | Manual verification against a real working session. |
| 2.11b | Desktop — Dashboard port | React port of `dashboard.py`'s existing views. | Side-by-side comparison against the Flask/FastAPI dashboard for data parity. |
| 2.11c | Desktop — Widgets | Habit/spending/product widgets, composable. | Manual verification; each widget independently removable without breaking the shell. |

Deferred, explicitly out of scope for Phase 2 (named so they aren't silently dropped): a live VS Code extension (§5) beyond static workspace-file reads; a dedicated graph database (§4) unless SQLite's CTEs demonstrably can't keep up; background terminal/process control of any kind (DevBrain and Vision stay read-only observers, never actors, for the whole of Phase 2).
