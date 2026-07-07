# Nova WorkOS — Product & Architecture Specification v1

**Status:** Design only. Nothing in this document is implemented. No tables, no
screens, no code exist for WorkOS yet.
**Type:** Product design + architecture. This is the foundational document for
Nova's next several years of work-and-life management. It defines *what* to build
and *how it fits the frozen architecture* — it does not implement anything.
**Authority:** Subordinate to `docs/adr/*`, the two frozen specs, and the
Handbook (see `CLAUDE.md`). Where this document proposes anything that touches a
package boundary, the dependency graph, `MutationEvent`, a Claude tool schema, or
the database schema, it is a **draft for human review** — a new ADR is required
before implementation (Handbook §11.4). Section 4 names the ADRs this milestone
needs.
**Precedent:** WorkOS is Nova's **second fully-built domain**, after Finance. It
inherits every pattern Finance established as the template
([ADR 0017](adr/0017-finance-as-the-first-domain.md)): integer minor-unit money,
`occurred_at`/`created_at` separation, `deleted_at` soft-delete, projections as
read models, the gate ladder, and chat/voice parity per gate. Where a choice
below looks constrained, it is usually because a governing rule
([§0](#0-governing-rules)) or a Finance-established pattern forced it.

---

## 0. Governing Rules

Every design choice below is bound by these. They are not restated per section.

1. **Brain is the only Claude client** ([ADR 0003](adr/0003-brain-is-the-only-claude-client.md)).
   Every AI feature in [§8](#8-ai-features) — planning, prioritization, health
   scoring, forecasting, briefings — is a Brain job. WorkOS gathers and
   structures data; Brain reasons over it. WorkOS never holds an API key.
2. **Memory is the only persistence owner** ([ADR 0004](adr/0004-memory-is-the-only-storage-owner.md)).
   WorkOS persists through `memory/work/` and nothing else. It never opens a
   sqlite3 or lancedb connection.
3. **Domains never call domains** ([ADR 0011](adr/0011-domain-isolation.md)).
   WorkOS does not import Finance, and Finance does not import WorkOS.
   Cross-domain data (revenue for a project, a calendar block for a task) flows
   through Memory, the event stream, injected tool-handlers at the composition
   root, or Brain — never a direct import.
4. **No mutation without a `MutationEvent`** ([ADR 0005](adr/0005-mutationevent-as-atomic-state-change.md)).
   Every write goes through `runtime/mutation_builders.py` →
   `finalize_mutations()`. `MutationEvent`'s shape is untouched.
5. **New capability = new package, single responsibility, documented non-ownership.**
   WorkOS is one new domain package with internal bounded contexts
   ([§4](#4-bounded-contexts)) — see the deliberate single-domain decision there.
6. **Explainable and uncertain by default**
   ([ADR 0015](adr/0015-explainable-decision-making.md),
   [ADR 0016](adr/0016-explicit-uncertainty.md)). Every AI ranking, estimate, or
   forecast carries its *reasons* and its *confidence*. WorkOS never shows a
   priority or a completion date without being able to answer "why?".
7. **Local-first** ([ADR 0001](adr/0001-local-first-architecture.md)). All work
   data lives in the local SQLite system of record. No cloud project tracker, no
   external sync as a dependency. External integrations (GitHub, calendars) are
   optional enrichers, never the source of truth.

---

## 1. Overall Vision

### Mission

**Nova WorkOS turns everything I am working toward — companies, freelance
clients, side projects, skills, and life goals — into one explainable system that
tells me what to do next and why.**

It is the executive-function layer over a founder's whole life: the place that
holds every commitment, understands how they trade off against each other, and
every morning produces a single, defensible answer to *"what should I work on
today, and why is that the highest-leverage thing I can do?"*

### The one-sentence test

> Every morning I open Nova and, in thirty seconds, know exactly what to work on,
> why it matters more than everything else, what is at risk, and what I am on the
> hook for — across all my projects and my life.

Every feature in this document earns its place by making that sentence more true.
If a feature does not change what shows up in the morning briefing, the weekly
review, or the founder dashboard, it is a candidate for cutting.

### Philosophy

1. **Decision support, not data entry.** Jira/Notion make you *maintain* a
   system; they are a tax. WorkOS's job is to *reduce* the maintenance burden —
   capture by voice and chat, infer structure, and pay the user back in
   decisions. Nova already logs finance "by hand, chat, or voice"; WorkOS extends
   the same capture surface to work.
2. **One priority queue across all of life.** A freelance deadline, a personal
   learning goal, and a company milestone compete for the *same* 16 waking
   hours. WorkOS's central act is ranking them against each other — not managing
   three separate silos that each think they own your day.
3. **Explainable prioritization.** Every ranking is a defensible argument
   (deadline proximity × revenue × strategic weight × blocking-others × decay),
   never a black box. You can always ask "why is this #1?" and get a real answer
   (ADR 0015).
4. **Time is the real currency.** Tasks are cheap; hours are not. WorkOS is
   organized around *capacity* — what fits in the time you actually have — not
   around an infinite backlog. Estimation, time-blocking, and ROI-per-hour are
   first-class, not add-ons.
5. **Projects are investments.** Each project has expected revenue, time
   invested, and therefore an ROI and a health trajectory. A founder's portfolio
   should be legible the way a finance portfolio is — which is exactly why WorkOS
   is built *after* Finance and reads from it.
6. **The system degrades gracefully.** With zero AI, WorkOS is still a clean,
   fast, local task+project tracker. AI makes it a chief-of-staff; its absence
   makes it merely excellent software. Nothing critical *requires* a model to be
   available.
7. **Structure is emergent, not imposed.** You should be able to dump a thought
   ("build the export feature for client X by Friday, ~4h, worth ₹40k") and let
   Nova place it in the hierarchy — not fill six form fields first.

### Non-goals (v1)

- **Not a team collaboration tool.** WorkOS is single-operator (the founder). No
  multi-user assignment, permissions, comments, or real-time collaboration. It
  can *model* other people (a client contact, a subcontractor) but does not seat
  them. Multiplayer is a 3-year horizon question ([§9](#9-future-vision)), not a v1 feature.
- **Not a replacement for code hosting or CI.** GitHub/GitLab remain where code
  and pipelines live. WorkOS *links to* and *reads from* them; it does not host
  repos or run builds.
- **Not a general document editor.** Rich docs and wikis are captured and
  referenced via the existing Knowledge Graph, not reimplemented. WorkOS stores
  *pointers and structure*, not a Notion clone's editor.
- **Not an accounting system.** Revenue, invoices, and cash live in **Finance**.
  WorkOS holds the *expectation and attribution* of revenue to work; Finance
  holds the money. It never double-books the ledger.
- **Not autonomous execution (v1).** Nova *proposes* plans, sprints, and
  re-prioritizations; the human commits them. Agentic auto-execution is a
  deliberate later horizon (Architecture v2 `agents` layer), gated behind trust.
- **Not a rigid methodology.** It does not force Scrum, GTD, or OKRs. It supports
  sprints, goals, and habits as *optional* structures over a common core.

---

## 2. Complete Module Breakdown

Modules are grouped by the bounded context that owns them ([§4](#4-bounded-contexts)).
Each is marked as a **stored aggregate/entity** (owns rows) or a **projection**
(computed read model over primitives, owns no storage — the
`services/api/projections/home.py` pattern). Deciding this split *is* the
architecture; getting it wrong is what makes project tools bloat.

### Context A — Delivery (the core work graph)

| Module | Kind | Purpose |
|---|---|---|
| **Portfolio** | Projection | Top-level roll-up across all projects; the founder's "book of work". No storage — computed from projects. |
| **Project** | Aggregate root | The central unit. Has objective, dates, expected revenue, health, ROI, an optional client. Everything hangs off it. |
| **Milestone** | Entity (in Project) | A dated, meaningful checkpoint within a project ("v1 launch", "50% complete"). Drives completion % and deadline tracking. |
| **WorkItem** | Aggregate root | Unified epic / story / task / subtask via a `type` + self-referencing parent (see [§5](#5-domain-model) — one tree, not four rigid tables). Carries estimate, status, priority, dependencies. |
| **Dependency** | Entity | A typed edge between two WorkItems or Projects (`blocks`, `blocked_by`, `relates_to`). The substrate for blocked-project detection. |
| **Sprint / Cycle** | Aggregate root | A time-boxed capacity window with committed WorkItems. Optional — you can run WorkOS with no sprints at all. |
| **Board / View** | Projection | Saved filters/groupings over WorkItems (kanban, list, by-project). No storage beyond the saved-view definition. |
| **Roadmap** | Projection | Time-laid-out view of milestones and projects (the Gantt/Linear-roadmap read model). Computed from Project + Milestone dates. |

### Context B — Planning & Time

| Module | Kind | Purpose |
|---|---|---|
| **AI Planner** | Projection + Brain | Produces the proposed day/week plan. Reads capacity + priority queue, calls Brain, emits a *proposed* plan the user commits. |
| **Day Plan** | Aggregate root | The committed plan for a date: ordered blocks, each linked to a WorkItem or an external calendar event. |
| **Time Block** | Entity (in Day Plan) | A scheduled span for focused work on an item. Bridges to **Calendar** (injected), never imports it. |
| **Time Entry** | Aggregate root | Actual time spent, linked to a WorkItem/Project. The raw material for time-invested, ROI, and estimate calibration. |
| **Focus Session** | Entity | A tracked work session (start/stop, interruptions) that produces Time Entries. |
| **Capacity** | Projection | Available hours per day/week after fixed commitments (calendar, habits, meetings). The denominator for realistic planning. |
| **Priority Queue** | Projection + Brain | The single ranked list across *all* contexts. The spine of the whole product ([§8.2](#82-automatic-prioritization-the-spine)). |

### Context C — Engagements (Clients, Freelance, Revenue attribution)

| Module | Kind | Purpose |
|---|---|---|
| **Client** | Aggregate root | A person/company you do work for. Lightweight personal CRM: contacts, context, history, health. |
| **Engagement / Contract** | Aggregate root | A commitment to a client: scope, rate model (fixed / hourly / retainer), value, dates, linked project(s). The freelance commitment record. |
| **Deliverable** | Entity (in Engagement) | A contracted output with a due date and acceptance state. Bridges to a Milestone or WorkItem. |
| **Revenue Expectation** | Entity | Expected/attributed revenue for a project or engagement. *Expectation only* — realized money lives in **Finance** (read via injection). |
| **Interaction** | Entity (in Client) | A logged touchpoint (meeting, email, call summary) for CRM continuity. May reference a Meeting. |

### Context D — Growth (Goals, Habits, Learning, Career, Life)

| Module | Kind | Purpose |
|---|---|---|
| **Goal / Objective** | Aggregate root | An OKR-style outcome with measurable key results. Projects and habits *contribute* to goals; goals give strategic weight to prioritization. |
| **Key Result** | Entity (in Goal) | A measurable target with current/target values and a trajectory. |
| **Habit** | Aggregate root | **Reuses existing `memory/habits.py`** — WorkOS surfaces and links habits to goals rather than reinventing them. |
| **Learning Item / Path** | Aggregate root | A skill or course on a roadmap, with progress and a link to the goal/career it serves. |
| **Career Roadmap** | Projection | A time-laid-out view of career goals, skills, and milestones. Computed. |
| **Life Goal** | Aggregate root | Long-horizon personal outcomes (health, relationships, finance targets) that compete for time alongside work. |

### Context E — Workspace (Documents, Meetings, Notes)

| Module | Kind | Purpose |
|---|---|---|
| **Document** | Reference | A pointer + metadata to a doc that lives in the **Knowledge Graph** / Memory semantic store. WorkOS stores the link and its relations, not the body. |
| **Meeting** | Aggregate root | A scheduled or logged meeting: attendees (Client contacts), agenda, notes, action items. Produces WorkItems. |
| **Note / Capture** | Entity | Fast unstructured capture that Nova later triages into WorkItems/notes ([§6.1](#61-morning-planning)). |
| **Action Item** | Entity | A commitment extracted from a meeting/note; becomes (or links to) a WorkItem. |

### Context F — Insight (all projections; owns no storage)

| Module | Kind | Purpose |
|---|---|---|
| **Daily Briefing** | Projection + Brain | The morning answer. Assembled from priority queue, deadlines, risks, calendar, revenue. |
| **Founder Dashboard** | Projection + Brain | The "how is everything?" view: portfolio health, revenue vs plan, time allocation, ROI, at-risk projects. |
| **Project Health** | Projection + Brain | Per-project score from schedule variance, velocity, blocked deps, staleness, budget/time burn. |
| **Risk Register** | Projection + Brain | Surfaced risks (slipping deadline, blocked chain, over-allocation, stale project, revenue at risk). Mostly *derived*; user-pinned risks are a small stored entity. |
| **ROI View** | Projection | Expected revenue ÷ time invested per project/engagement. Reads Finance (realized) + Time Entries (invested). |
| **Reports** | Projection + Brain | Weekly review, monthly review, quarter planning summaries. Generated, exportable. |
| **Notifications** | Reuse | Deadline/risk/plan alerts materialize into the **existing `reminders` domain** (Finance precedent) — WorkOS grows no parallel notification channel. |

### Deliberately deferred (designed-for, not built in v1)

- **Automations / rules engine** ("when a story's last task closes, close the
  story") — reserve the hook, defer the engine; agentic execution is the v2
  `agents` layer.
- **Templates** (project/sprint templates) — natural later addition once the
  entity shapes are proven.
- **Budgets/burn limits per project** — mirrors Finance's deferred budgets.
- **Multiplayer / delegation** — non-goal for v1.
- **External write-back** (creating GitHub issues from WorkItems) — read-only
  enrichment first; write-back is a trust-gated later step.

---

## 3. Information Architecture

How the modules nest and connect. The tree is the *conceptual* hierarchy, not the
storage layout (storage is [§5](#5-domain-model), navigation is a UI concern for
the implementation gates).

```
LIFE (the operator — implicit root; the "single priority queue" owner)
│
├── GOALS & GROWTH ............................ why the work matters (strategic weight)
│   ├── Life Goal
│   ├── Goal / Objective ──── Key Result
│   ├── Career Roadmap ────── Learning Path ──── Learning Item
│   └── Habit (existing memory/habits)
│         │
│         └─(gives strategic weight to)─┐
│                                       ▼
├── DELIVERY .................. the work graph (what gets done)
│   └── Portfolio (projection)
│         └── Project ◀───────────────── contributes-to ── Goal
│               ├── Milestone
│               ├── WorkItem (epic)
│               │     └── WorkItem (story)
│               │           └── WorkItem (task)
│               │                 └── WorkItem (subtask / checklist)
│               ├── Dependency ──(edges between WorkItems / Projects)
│               └── (rolls up to) ── Roadmap (projection)
│
├── ENGAGEMENTS ............... who the work is for + what it's worth
│   ├── Client ──── Interaction
│   └── Engagement / Contract ──── Deliverable ──(fulfilled by)── Milestone / WorkItem
│         └── Revenue Expectation ──(realized by)──▶ FINANCE (transactions)
│
├── PLANNING & TIME ........... fitting work into real hours
│   ├── Sprint / Cycle ──(commits)── WorkItem
│   ├── Day Plan ──── Time Block ──(scheduled on)──▶ CALENDAR
│   ├── Time Entry ──(logged against)── WorkItem / Project
│   └── Capacity (projection) ◀── Calendar + Habits + Meetings
│
├── WORKSPACE ................. context and commitments
│   ├── Meeting ──── Action Item ──▶ WorkItem
│   ├── Document (ref) ──────────────▶ KNOWLEDGE GRAPH
│   └── Note / Capture ─────────────▶ (triaged into) WorkItem / Note
│
└── INSIGHT (all projections; Brain-assembled) ... the answers
    ├── Priority Queue  ◀── everything above
    ├── Daily Briefing  ◀── Priority Queue + deadlines + Calendar + risks
    ├── Founder Dashboard ◀── Project Health + ROI + Revenue + Time
    ├── Project Health / Risk Register / ROI View
    └── Reports (weekly / monthly / quarter) ──▶ Notifications (existing reminders)
```

### The three cross-domain seams (the only edges that leave WorkOS)

These are the *only* places WorkOS touches another domain/service. Each obeys
[ADR 0011](adr/0011-domain-isolation.md): the connection is made by the
composition root (injected tool-handler) or Brain, never a direct import.

| Seam | WorkOS side | Other side | Mechanism |
|---|---|---|---|
| **Revenue** | Revenue Expectation, ROI View, Founder Dashboard | **Finance** (transactions/accounts) | Injected read-only query handler at the root; or Brain fuses both. WorkOS never imports `domains.finance`. |
| **Time / scheduling** | Time Block, Day Plan, Capacity | **Calendar** service | Injected tool-handler (the exact pattern Finance uses to reach Calendar per ADR 0017). |
| **Knowledge** | Document (ref), Meeting notes, semantic search over work | **Knowledge Graph / Memory semantic** | Through Memory's public API + `services/knowledge`. |

Everything else is *internal* to WorkOS and may reference freely — which is the
central reason WorkOS is **one** domain, not six ([§4](#4-bounded-contexts)).

---

## 4. Bounded Contexts

### The central decision: WorkOS is ONE domain with internal contexts

**A domain never imports another domain** (ADR 0011). The Delivery, Planning,
Engagements, Growth, and Workspace concepts reference each other *constantly*: a
Sprint commits WorkItems, an Engagement fulfils via a Milestone, a Goal weights a
Project, a Time Entry logs against a WorkItem. If each were a separate *domain
package*, every one of these everyday links would have to be routed through Brain
or the composition root — turning one consistency boundary into a mesh of
indirection. That is precisely the failure ADR 0011 exists to prevent, applied in
reverse: over-splitting is as damaging as under-isolating.

**Decision (requires a new ADR — draft only, see below):** WorkOS is a single
domain package, `domains/work/`, internally organized into the six bounded
contexts as *modules*, not packages. The contexts are a **modeling and ownership**
boundary (which team/agent owns which entities, which invariants hold together),
enforced by convention and directory structure — not by the import-boundary tests
that separate *domains*. The domain-isolation tests still apply at the
`domains/work/` ↔ `domains/finance/` edge, which stays clean.

> **This is a structural decision that touches the package taxonomy and the
> dependency graph — it MUST NOT be implemented until a human accepts an ADR**
> (Handbook §11.4). See ADRs required at the end of this section.

Within `domains/work/`, the Insight context (Context F) is special: it owns **no
storage at all** and depends on all others — it is the domain's internal
"read-model + Brain-fusion" layer, structurally analogous to how Brain sits above
domains globally.

### Context responsibilities, ownership, and communication

For each context: what it is responsible for, what it **owns** (writes), what it
must **not own**, and how it communicates.

#### A — Delivery
- **Responsible for:** the integrity of the work graph — a task always has a
  valid parent chain, progress rolls up correctly, dependencies form no cycles.
- **Owns:** Project, Milestone, WorkItem, Dependency, Sprint, saved View defs.
- **Does NOT own:** money (Finance), calendar slots (Calendar), the *decision* of
  what to work on (Insight/Brain), document bodies (Knowledge).
- **Communicates:** emits `work.project.*`, `work.item.*`, `work.sprint.*`
  MutationEvents. Read by every projection.

#### B — Planning & Time
- **Responsible for:** turning the ranked backlog into a realistic, time-bounded
  plan, and recording what actually happened (time spent).
- **Owns:** Day Plan, Time Block, Time Entry, Focus Session, Sprint capacity.
- **Does NOT own:** the calendar itself (injected Calendar handler), the ranking
  logic (that is Brain via the Priority Queue projection), the WorkItems it
  schedules (Delivery owns those).
- **Communicates:** emits `work.plan.*`, `work.time.*`; consumes the Priority
  Queue and Capacity projections; reaches Calendar only via an injected handler.

#### C — Engagements
- **Responsible for:** the truth of *who you owe work to and what it's worth*, and
  attributing expected revenue to work.
- **Owns:** Client, Engagement/Contract, Deliverable, Interaction, Revenue
  Expectation.
- **Does NOT own:** realized money, invoices, or the ledger — those are
  **Finance**. Owns only the *expectation* and the *attribution link*.
- **Communicates:** emits `work.client.*`, `work.engagement.*`. Reads realized
  revenue from Finance through an injected read query (never an import). Brain
  fuses expectation (WorkOS) + realized (Finance) into ROI.

#### D — Growth
- **Responsible for:** the *why* — strategic outcomes that give work its weight.
- **Owns:** Goal, Key Result, Learning Item/Path, Life Goal. **Reuses** Habit
  from existing `memory/habits.py` (does not re-own it).
- **Does NOT own:** the projects that fulfil goals (Delivery owns those; Goals
  hold contribution links).
- **Communicates:** emits `work.goal.*`, `work.learning.*`; contributes
  strategic-weight signals consumed by the Priority Queue.

#### E — Workspace
- **Responsible for:** capturing context (meetings, notes, docs) and converting it
  into actionable work.
- **Owns:** Meeting, Note/Capture, Action Item; a Document *reference* row.
- **Does NOT own:** document bodies or embeddings (Knowledge Graph / Memory
  semantic own those). Stores pointers + relations only.
- **Communicates:** emits `work.meeting.*`, `work.note.*`; hands note/meeting text
  to `services/knowledge` for embedding; extracts Action Items → Delivery.

#### F — Insight
- **Responsible for:** every *answer* — briefings, health, ROI, risk, reports,
  the priority queue.
- **Owns:** **nothing persistent** except small user artifacts (pinned risks,
  saved report configs). Everything else is computed.
- **Does NOT own:** any primitive — it only reads them.
- **Communicates:** assembles read models; delegates all reasoning to **Brain**
  (ADR 0003). Produces the payloads `services/api` serves and the content
  `services/planner`/voice speak.

### Backend module placement (obeys the frozen taxonomy)

Mirrors exactly how Finance is placed (per `FINANCE_DOMAIN.md` §1 and the real
`domains/finance/` + `memory/finance/` layout):

- **`memory/work/`** — new persistence sub-package beside `memory/finance/`: one
  module per table family (`projects.py`, `items.py`, `sprints.py`,
  `dependencies.py`, `planning.py`, `time_entries.py`, `clients.py`,
  `engagements.py`, `goals.py`, `learning.py`, `meetings.py`, `notes.py`). Memory
  stays the only persistence owner; tables created idempotently from
  `memory/schema.py`.
- **`domains/work/`** — new domain package with the DDD tactical structure Finance
  already uses (`aggregates.py`, `value_objects.py`, `mutations.py`,
  `repository_adapters.py`, plus per-context modules like `delivery.py`,
  `planning.py`, `engagements.py`, `growth.py`, `insight.py`). Contains domain
  logic that is more than a row insert: progress roll-up, dependency-cycle
  checks, capacity math, ROI computation, health scoring inputs. Does **not** call
  Claude and does **not** open the DB — it calls `memory.work.*` and hands
  reasoning to Brain.
- **`services/api/routers/work/`** — thin routers per sub-resource, same shape as
  `routers/finance/`: validate → call domain/memory → build mutation events →
  `finalize_mutations()` → typed response. Insight projections are GET-only
  aggregate endpoints (the `/home`, `/finance/dashboard` pattern).
- **`runtime/mutation_builders.py`** — new pure builders
  (`build_project_created`, `build_item_updated`, `build_time_logged`, …).
  `MutationEvent` shape is **untouched**; the existing dataclass already expresses
  everything WorkOS needs (`entity_type`, `operation`, payload).
- **Brain jobs** — new reasoning entry points (`brain.run_daily_plan`,
  `brain.run_prioritization`, `brain.run_project_health`,
  `brain.run_weekly_review`), following the `knowledge.reflection →
  brain.run_reflection_job` precedent. All Claude access lives here.
- **`memory_producers.py`** — policy additions where a work mutation is genuinely
  memorable (project created/closed, milestone hit, engagement won, goal
  achieved). Routine task edits produce **no** semantic memory (noise), exactly as
  routine transactions don't.
- **Chat/voice path:** planner commands gain work verbs over time; `mutation_chat`
  translates them to the same events, with per-gate parity tests (the Finance
  discipline).

### ADRs this milestone requires (drafts for human acceptance)

Per Handbook §11.4, none of these are self-approvable:

1. **"WorkOS as the second domain"** — mirrors ADR 0017; records why WorkOS is
   one domain with internal contexts (not six domains), and confirms it obeys
   0004/0005/0011.
2. **Cross-domain read access pattern** — how WorkOS reads Finance
   (realized revenue) without importing it: the injected read-query handler at
   the composition root. This may extend `ALLOWED_EDGES` in
   `tests/architecture/test_dependencies.py`; that change is human-gated.
3. **(If needed) `entity_type` vocabulary extension** — the new work entity types
   below are additive to the mutation vocabulary; confirm they need no
   `MutationEvent` shape change (expected: they do not).

---

## 5. Domain Model

Entities, relationships, aggregates, value objects, and lifecycle — **no
implementation, no columns**. (Physical tables are a later gate; this is the
conceptual model, following `FINANCE_DOMAIN.md` §1's "primitive concepts"
approach.) Inherited conventions from Finance: money as integer minor units,
domain date (`occurred_at`) separated from audit date (`created_at`), soft-delete
via `deleted_at`, never destroy data.

### 5.1 Aggregates (consistency boundaries)

An **aggregate** is edited and validated as a unit; nothing outside it may hold a
reference to its internal entities except through the root.

| Aggregate root | Internal entities | Key invariant it protects |
|---|---|---|
| **Project** | Milestone | Milestone dates lie within project dates; completion % is a consistent roll-up; a project has exactly one lifecycle state. |
| **WorkItem** | Subtask/Checklist item | Parent chain is acyclic and type-valid (task ∈ story ∈ epic ∈ project); a done item has all blocking deps satisfied; estimate ≥ logged is not required but variance is tracked. |
| **Sprint** | Committed-item link, capacity | Committed effort is recorded against a fixed capacity; an item is in at most one active sprint. |
| **Engagement** | Deliverable, Revenue Expectation | Sum of deliverable values reconciles to engagement value; revenue expectation attaches to exactly one engagement/project. |
| **Client** | Interaction | Client health and last-contact derive only from its own interactions. |
| **Goal** | Key Result | Goal progress is a defined function of its key results; contribution links point to existing projects. |
| **Day Plan** | Time Block | Blocks do not overlap; total planned ≤ capacity (soft — over-allocation is *flagged*, not forbidden). |
| **Time Entry** | — (leaf aggregate) | Immutable once closed; sums are exact (integer minutes). |
| **Meeting** | Action Item | Action items convert to WorkItems idempotently. |
| **Learning Path** | Learning Item | Path progress rolls up from item progress. |

**Why WorkItem is a unified tree (not four Jira tables):** epic/story/task/subtask
share one lifecycle, one estimate model, one dependency model, one priority
model. Differentiating by a `type` value on a self-referencing parent link — the
same move Finance made unifying bills/subscriptions/EMIs into `recurring_rules`
by `kind` — keeps the graph queryable, the roll-up uniform, and avoids four
near-identical tables that can't be reparented. Hierarchy *rules* (a task's parent
must be a story or a project) are a domain invariant, not a schema rigidity.

### 5.2 Value Objects (no identity; compared by value; immutable)

| Value Object | Captures | Notes |
|---|---|---|
| **Estimate** | expected effort | Integer minutes/points + a confidence band (ADR 0016) — never a bare number. |
| **Priority Score** | computed rank | Derived; carries its component reasons (ADR 0015). Not user-set directly — see lifecycle. |
| **Progress** | 0–100% completion | Always a roll-up function, never a free-typed field on parents. |
| **Status** | lifecycle state | A small enum per aggregate ([§5.4](#54-lifecycles)); the only field that drives workflow. |
| **DateRange** | start/target/actual | Separates *planned* from *actual* end; slippage = actual − target. |
| **Money** | expected/realized value | **Reuses Finance's integer minor-unit VO**; WorkOS never invents its own money type. |
| **ROI** | value ÷ time | Expected-revenue ÷ time-invested-hours; a pure derivation, carries its inputs. |
| **Cadence** | recurrence | For sprints/reviews/habits — reuses the Finance `recurring_rules` cadence vocabulary conceptually. |
| **Rate Model** | how an engagement earns | `fixed` \| `hourly` \| `retainer` + amount; the basis for revenue expectation. |
| **Health Score** | project vitality | Derived band (`on_track` \| `at_risk` \| `off_track`) + reason vector; never stored as ground truth, always recomputed. |
| **Confidence** | model certainty | Attached to every AI estimate/forecast (ADR 0016). |

### 5.3 Key relationships

```
Goal ──contributes──< Project ──has──< Milestone
  │                      │
  │                      ├──contains──< WorkItem (epic→story→task→subtask, self-ref)
  │                      │                  │
  │                      │                  ├──depends-on──> WorkItem/Project (Dependency edge)
  │                      │                  ├──logged-by──< Time Entry
  │                      │                  └──committed-in──> Sprint
  │                      │
Engagement ──delivers-via──> Milestone/WorkItem
  │   │
  │   └──expects──> Revenue Expectation ──realized-by──▶ Finance.Transaction (cross-domain, injected)
  │
Client ──holds──< Engagement ;  Client ──has──< Interaction
Meeting ──produces──< Action Item ──becomes──> WorkItem
Day Plan ──schedules──< Time Block ──for──> WorkItem  ;  Time Block ──on──▶ Calendar (injected)
Learning Path ──contains──< Learning Item ──serves──> Goal/Career
```

Cardinalities worth pinning: a WorkItem has **one** parent and **one** project; a
Project has **zero-or-one** primary Engagement (and may be internal/personal with
none); an Engagement has **one** Client; a Time Entry has **one** WorkItem; a
Revenue Expectation attaches to **one** Engagement *or* Project (exclusive).

### 5.4 Lifecycles

Each aggregate has a single explicit state machine (the "one lifecycle state"
invariant). Transitions are the *only* thing that drives workflow and are the
natural `operation` verbs on MutationEvents.

- **Project:** `idea → planned → active → (paused ⇄ active) → completed | archived`.
  `blocked` is *not* a stored state — it is a **derived** health condition
  (a project with all active items blocked), keeping status honest.
- **WorkItem:** `backlog → todo → in_progress → (blocked ⇄ in_progress) → in_review → done | cancelled`.
  `blocked` here *is* explicit because it's item-local and user-meaningful; but the
  system can also *infer* it from unmet dependencies and prompt the user.
- **Milestone:** `pending → in_progress → reached | missed` (missed when target
  date passes unreached — a derived-then-confirmed transition).
- **Sprint:** `planned → active → completed`; incomplete items roll forward on
  completion (proposed by Nova, confirmed by user).
- **Engagement:** `prospect → proposed → active → (on_hold ⇄ active) → delivered → closed | lost`.
- **Deliverable:** `pending → submitted → accepted | revising`.
- **Goal:** `draft → active → (achieved | missed | abandoned)`; progress derived
  from key results throughout.
- **Time Entry / Focus Session:** `open → closed` (closed = immutable).
- **Day Plan:** `proposed → committed → (in_progress) → done`; a proposed plan
  from the AI Planner has no side effects until committed (the "propose, human
  commits" philosophy).

**Priority is not a lifecycle** — it is a continuously recomputed Value Object,
never a stored status. This is deliberate: a stored priority rots the moment
context changes; a computed one is always current and always explainable.

---

## 6. User Journeys

Concrete flows, each showing (a) the capture surface, (b) which contexts/entities
move, (c) where Brain enters, and (d) what the human commits. Capture is always
available by **voice, chat, or hand** (the Finance capture precedent).

### 6.1 Morning Planning

1. User: *"Good morning — what's my day?"* (voice) or opens the Daily Briefing.
2. **Insight** assembles the read model: Priority Queue (across *all* contexts),
   deadlines within horizon, today's Calendar (injected), open risks, yesterday's
   uncommitted items, capacity for today.
3. **Brain** (`run_daily_plan`) produces a *proposed* Day Plan: an ordered set of
   Time Blocks that fit capacity, each with a one-line **why** (ADR 0015) and a
   **confidence** (ADR 0016) — "2h on Client X export (due Fri, ₹40k, blocks their
   sign-off), 45m on Nova learning (habit streak), 1h buffer."
4. User edits/accepts → Day Plan transitions `proposed → committed`; Time Blocks
   optionally sync to Calendar (injected). `work.plan.committed` emitted.
5. Overflow items stay in the queue; nothing is lost.

### 6.2 Capturing & structuring a freelance project

1. User (chat): *"New client Acme, fixed ₹2L, build their analytics dashboard,
   three milestones, first due July 25."*
2. **Brain** parses intent → proposes a **Client** (Acme), an **Engagement**
   (fixed, ₹2,00,000 → stored as minor units), a **Project** linked to it, and 3
   **Milestones**. Shows the structured proposal.
3. User confirms/adjusts → mutations emitted (`work.client.created`,
   `work.engagement.created`, `work.project.created`, `work.milestone.created`).
   Revenue Expectation ₹2L attached to the engagement.
4. Later: *"For the first milestone I need auth, the chart page, and CSV export,
   ~4h each."* → three **WorkItems** created under milestone 1 with Estimates.
5. Founder Dashboard now shows Acme's ₹2L in *expected* revenue and 0 realized
   (Finance shows realized once an invoice is paid — read via injection, never
   double-counted).

### 6.3 Launching a product (milestone crunch)

1. Project "Nova WorkOS v1" nears its launch Milestone.
2. **Project Health** flags `at_risk`: 3 blocked WorkItems on the critical path,
   velocity below the rate needed to hit the target date.
3. **Risk Register** surfaces the specific chain (`blocked_by` edges) and the
   revenue at risk if it slips.
4. User: *"What do I have to do to still hit Friday?"* → **Brain** replays the
   dependency graph + capacity and returns the minimal critical path and what to
   drop, with confidence.
5. User re-plans; Nova proposes moving lower-priority personal items out of the
   week (the cross-context trade-off — the whole point of one queue).

### 6.4 Managing deadlines across everything

1. A freelance deliverable (Fri), a personal learning deadline (Sun), and a
   company milestone (next Wed) all approach.
2. **Priority Queue** ranks them against each other by the shared function
   ([§8.2](#82-automatic-prioritization-the-spine)) — deadline × revenue ×
   strategic weight × blocking-others × decay — not by silo.
3. Nova proactively (via existing **reminders**): *"Two deadlines collide Friday;
   the client one is ₹40k and blocks their sign-off — start it Wednesday."*

### 6.5 AI Daily Briefing (proactive, scheduled)

1. A scheduled Brain job (analogous to the finance sweep pattern — invoked on
   access or by the existing runtime, **no new daemon**) composes the briefing
   each morning.
2. Delivered by voice on wake, or as the Insight home payload: today's top 3, why,
   one risk, one deadline, revenue note, one habit/goal nudge.
3. Explicitly bounded ([§8](#8-ai-features)) — it *reports and proposes*, it does
   not silently mutate anything.

### 6.6 Quarter planning

1. User: *"Plan Q3."* → **Brain** (`run_period_review` in planning mode) reads
   Goals, current project trajectories, revenue expectation vs Finance realized,
   and capacity.
2. Produces a proposed quarter: which Goals to push, which Projects fit the
   available hours, what to *not* do (explicit — capacity is finite).
3. User commits selected Goals/Milestone target dates; a **Report** is generated
   and exported.

### 6.7 Revenue review

1. User: *"How's my money looking against my work?"*
2. **ROI View** fuses WorkOS Revenue Expectations + Time Entries with **Finance**
   realized transactions (injected read): expected vs realized per engagement,
   ROI-per-hour per project, which client is most profitable per hour.
3. **Brain** narrates: "Acme is ₹40k realized of ₹2L expected, ~18h in →
   ~₹2,200/hr; your personal project has 60h and ₹0 — is that intentional?"
   Finance stays the money system of record; WorkOS only attributes it to work.

### 6.8 Weekly & monthly review

1. Friday/month-end scheduled review: **Brain** (`run_weekly_review`) summarizes
   completed vs planned, slippage, time allocation across projects, habit
   adherence, goal movement, and the top risks for next week.
2. Output is a **Report** (exportable) + a proposed next-week focus that seeds
   Monday's plan. The loop closes.

---

## 7. AI Features

**The most important section.** Every feature here is a **Brain** job (ADR 0003),
returns **reasons** (ADR 0015) and **confidence** (ADR 0016), and *proposes* —
the human commits (the v1 non-goal on autonomy). WorkOS structures the inputs;
Brain reasons; the runtime records the human's decision as a MutationEvent.

Nova's tiered model architecture (ADR 0002) applies: cheap/local models for
routine structuring (parsing a captured note, tagging), the strong model for the
reasoning that matters (prioritization, planning, health, review).

### 7.1 Daily planning
Turns the ranked backlog + capacity + calendar into a realistic, time-blocked day.
Respects fixed commitments and habits; leaves buffer; explains each block. Output
is a *proposed* Day Plan. **Signals in:** priority queue, capacity, calendar,
energy patterns (from historical Time Entries), deadlines. **Guardrail:** never
over-commits silently — over-allocation is surfaced, not hidden.

### 7.2 Automatic prioritization (the spine)
The single most important AI feature: **one ranked queue across all of life.**
The score is an explainable function of:

- **Deadline proximity** (and hardness — contractual vs soft).
- **Revenue** attached (expected, from Engagement) and **revenue-at-risk**.
- **Strategic weight** — how strongly the item's project contributes to an active
  **Goal**.
- **Blocking factor** — how many other items/people this unblocks (from the
  Dependency graph).
- **Decay/staleness** — aging important-but-not-urgent work so it doesn't rot.
- **Effort/ROI** — quick high-value wins surface appropriately.

Every ranked item can answer *"why here?"* with its component contributions
(ADR 0015). Weights are user-tunable; the model proposes, the human sets the
policy. This is what makes WorkOS more than a task list.

### 7.3 Project health scoring
Per project: `on_track | at_risk | off_track` + a reason vector, from schedule
variance (milestone target vs trajectory), velocity vs required rate, count/age of
blocked items, staleness (no activity), and time-burn vs value. Recomputed, never
stored as truth. Feeds the Founder Dashboard and Risk Register.

### 7.4 Revenue prediction & ROI
Fuses WorkOS Revenue Expectations + trajectory with **Finance** realized data
(injected) to forecast: expected-close revenue this month/quarter, per-engagement
realized-vs-expected, ROI-per-hour by project/client. **Confidence bands
mandatory** (ADR 0016) — a forecast without uncertainty is banned.

### 7.5 Deadline & slippage risk
Detects deadlines that will be missed at current velocity, dependency chains that
threaten a milestone, and collisions (two hard deadlines in one week beyond
capacity). Proactive via existing **reminders**. Explains the chain and proposes
the minimal recovery path.

### 7.6 Task estimation & calibration
Proposes Estimates for new WorkItems from similar historical items (semantic
similarity via Memory's vector store), and — crucially — **calibrates**: compares
past estimates to logged Time Entries and tells you your personal estimation bias
("you run ~1.6× on backend tasks"). Estimates always carry confidence.

### 7.7 Automatic sprint planning
Given a sprint length and capacity, proposes a committed set that fits — pulling
from the priority queue, respecting dependencies (won't commit a blocked item
before its blocker), balancing across projects/goals. Proposes carry-forward of
incomplete items on sprint close.

### 7.8 Dependency detection
Suggests likely `blocks`/`blocked_by` edges from item text and history ("'deploy'
usually depends on 'CI setup'"), and flags **cycles** and **critical paths**. The
user confirms edges; Nova never fabricates hard dependencies silently.

### 7.9 Meeting capture → action items
From meeting notes (captured by voice/paste, embedded via Knowledge Graph), Brain
extracts Action Items and proposes WorkItems with owners/dates. Idempotent
conversion (re-processing the same note doesn't duplicate).

### 7.10 Roadmap suggestions
Given goals + capacity, proposes a sequenced Roadmap (which milestones, in what
order, with realistic dates), surfacing where ambition exceeds available hours —
the honest "you cannot do all of this by Q3" conversation.

### 7.11 Learning recommendations
Connects Career/Goals to a Learning Path: proposes next skills/courses that serve
active goals, and finds slack in the schedule where learning realistically fits.

### 7.12 Context-switch assistance
When you move between projects, Brain assembles the *context bundle*: where you
left off, the relevant docs (Knowledge), open items, and the last decisions — to
kill the re-orientation tax that kills founder productivity.

### 7.13 Weekly / monthly / quarter review
Generated retrospectives + forward plans ([§6.8](#68-weekly--monthly-review),
[§6.6](#66-quarter-planning)). Summarize, spot trends (velocity, allocation drift,
goal movement), and seed the next period's plan.

### 7.14 Founder dashboard narration
Turns the raw Founder Dashboard read model into a spoken/written executive summary:
"3 projects active, 1 at risk (Acme — blocked on their API keys), ₹2.4L expected
this quarter vs ₹1.1L realized, you've spent 62% of your hours on the lowest-ROI
project." The chief-of-staff voice.

### AI safety & scope rails (apply to all of the above)

- **Propose, never silently mutate** (v1). Every AI action becomes a human-
  committed MutationEvent or nothing.
- **Explainable** (ADR 0015) and **uncertain** (ADR 0016) by construction — no
  ranking, estimate, or forecast without reasons and confidence.
- **Degrades gracefully** — with Brain unavailable, WorkOS still runs as a
  first-class manual tracker; only the intelligence dims.
- **Local-first inputs** — routine structuring uses local/cheap models (ADR 0002);
  the strong model is reserved for reasoning that earns it (cost + privacy).

---

## 8. Implementation Roadmap

Same rhythm as the Finance gates (FIN-1…6): **backend + events + parity tests
first, desktop second; stop and verify between gates.** Each gate ships a usable
increment and is independently valuable. Ordered so the *spine* (work graph +
prioritization) lands before the breadth.

> Gate 0 is a prerequisite and is **not** code: accept the ADRs from
> [§4](#4-bounded-contexts). Nothing below starts until they're accepted.

| Gate | Theme | Contents | Ships |
|---|---|---|---|
| **WOS-0** | Foundations (human decision) | Accept the 2–3 ADRs (§4). Add `domains/work/` ↔ `memory/work/` scaffolding decision to `ALLOWED_EDGES`. **No feature code.** | The green light. |
| **WOS-1** | Work graph backend | `memory/work/` (projects, items, milestones, dependencies) + `domains/work` aggregates/value-objects + Projects & WorkItems endpoints + mutation builders/events + parity tests. `entity_type`: `project`, `work_item`, `milestone`, `dependency`. | A local project + hierarchical task tracker (API + chat/voice). |
| **WOS-2** | Delivery UI + capture | Work section UI (projects, board/list, item editor with full CRUD), fast capture (voice/chat → structured item). Retire nothing — additive. | A usable, fast task/project manager on the desktop. |
| **WOS-3** | Prioritization spine | Priority Queue projection + `brain.run_prioritization` (explainable, tunable weights). One ranked list across projects. Estimates as value objects. | "What's most important right now?" — the differentiator. |
| **WOS-4** | Planning & time | Day Plan, Time Blocks (Calendar injected), Time Entry/Focus tracking, Capacity projection, `brain.run_daily_plan`. Morning planning journey (§6.1). | The AI Planner + time tracking. |
| **WOS-5** | Sprints & dependencies | Sprint aggregate + auto sprint planning + dependency detection/critical-path + carry-forward. | Team-grade delivery mechanics (single-player). |
| **WOS-6** | Engagements & revenue | Clients (CRM), Engagements/Contracts, Deliverables, Revenue Expectation + the **Finance cross-domain read seam** (injected). ROI View. | Freelance/founder revenue attribution. |
| **WOS-7** | Growth | Goals/OKRs + Key Results, strategic-weight into prioritization, Learning Paths, Career/Life goals, Habit reuse surfaced. | The "why" layer wired into the queue. |
| **WOS-8** | Insight & reviews | Founder Dashboard, Project Health, Risk Register, Reports (weekly/monthly/quarter), Daily Briefing, narration. Notifications via existing reminders. | The chief-of-staff. |
| **WOS-9** | Workspace | Meetings → Action Items, Document references (Knowledge Graph), Note triage. | Context capture closes the loop. |
| **WOS-10** *(future)* | Templates, automations, external enrichment (GitHub read), then trust-gated agentic execution (v2 `agents`). | Scale + autonomy. |

Chat/voice parity per gate (the Finance discipline): each gate that adds mutations
adds the planner verbs + `mutation_chat` translation for the ones that make sense
by voice, with parity tests. Memory-producer policy rides the gate that
introduces the mutation. The spine (WOS-1→4) is the minimum lovable WorkOS; 5–9
are independently shippable breadth; 10 is horizon.

---

## 9. Future Vision

Where WorkOS goes after v1. Each horizon assumes the prior one shipped and stays
inside the frozen architecture (or explicitly earns a new ADR).

### 1 year — The reliable second brain
Every commitment across work and life is in Nova and captured effortlessly by
voice. The morning briefing is trusted enough that the user plans their day *from
it*. Prioritization, health, and ROI are accurate and explainable. WorkOS has
replaced the user's Jira/Notion/Motion/spreadsheet stack for their own work.
**Measure:** the founder opens WorkOS first every morning and Finance/WorkOS
together answer "how am I doing?" without a spreadsheet.

### 3 years — The proactive chief of staff
Nova moves from *proposing* to *trusted, reversible autonomy* (the v2 `agents`
layer, trust-gated): it re-plans the day when a meeting runs long, drafts the
client update from the week's activity, flags a slipping project before the user
notices, and negotiates the calendar. Deep two-way integrations (GitHub, email,
calendars) as *enrichers*, still local-first at the core. Optional lightweight
multiplayer: a subcontractor or collaborator can be *seated* on one engagement
without WorkOS becoming a team SaaS.

### 5 years — The operating system for a portfolio life
WorkOS runs a founder juggling *hundreds* of projects and multiple ventures —
portfolio-level intelligence (which venture deserves the next hour of your life),
predictive capacity planning across quarters, and a genuine model of the operator:
energy, focus patterns, what they procrastinate on, what they're best at. It
allocates a scarce life the way a fund allocates capital — with an explainable,
auditable thesis per decision.

### 10 years — The exocortex
Nova is the durable external memory and executive function of a career: a decade
of decisions, their reasons (every MutationEvent is an audit trail — that
architecture choice pays off here), and their outcomes, queryable. It can answer
"what did I decide about X in 2028 and was I right?" and apply the lesson. Still
local-first, still explainable, still the user's — not a platform's. The frozen
principles (Memory owns truth, Brain reasons, every change is an explainable event)
are exactly what make a 10-year exocortex coherent rather than a decade of
accumulated cruft.

---

## Appendix — Explicit non-goals / deferred decisions (v1)

Kept honest, in the Finance-doc tradition:

- **No multi-user / real-time collaboration.** Single-operator. Others are
  *modeled* (client contacts), not *seated*.
- **No external system as source of truth.** GitHub/calendar/email are optional
  read enrichers; the local SQLite is ground truth (ADR 0001). External *write-
  back* is deferred to WOS-10, trust-gated.
- **No autonomous mutation in v1.** Everything AI proposes; the human commits.
- **No amortization/velocity ML engine** — estimation calibration starts as simple
  ratio-from-history, not a trained model.
- **No rich-doc editor** — documents live in the Knowledge Graph; WorkOS holds
  references and relations.
- **No custom-field/automation builder** — reserve the hooks, defer the engine.
- **No re-invention of money, habits, calendar, or knowledge** — WorkOS reuses
  Finance's money VO, `memory/habits.py`, the Calendar service, and the Knowledge
  Graph through the sanctioned seams; it owns none of them.
- **`MutationEvent` shape, DB schema, package boundaries, tool schemas** — any
  change to these is drafted here for human review and **requires an ADR** before
  implementation (Handbook §11.4). This document proposes; it does not decide.
```