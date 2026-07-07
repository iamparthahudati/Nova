# Nova WorkOS — Architecture Specification v1

**Status:** Design only. Nothing in this document is implemented. No packages,
tables, routes, screens, or tests exist for WorkOS yet.
**Type:** Technical architecture — the single source of truth to build against
*after* it is reviewed. It defines the package layout, aggregates, value objects,
services, ports, projections, events, and integration seams. It contains **no
code, no SQL, no route definitions, no schema, no component source**.
**Companion:** the product/scope decisions live in
[`NOVA_WORKOS_PRODUCT_SPEC_v1.md`](NOVA_WORKOS_PRODUCT_SPEC_v1.md). This document
is the *how it is built*; that one is the *what and why*.
**Authority:** Subordinate to `docs/adr/*`, the two frozen specs, and the Handbook
(`CLAUDE.md`). Any part of this that touches a package boundary, the dependency
graph, `MutationEvent`, a Claude tool schema, or the DB schema is a **draft for
human review** requiring an ADR before implementation (Handbook §11.4). The ADRs
required are listed in [§16 Architecture Review](#16-architecture-review).
**Precedent:** WorkOS is Nova's **second domain**, built to copy the Finance
template exactly — `domains/finance/` is the reference implementation for every
structural choice below (aggregates as frozen dataclasses with `from_row`,
`repositories.py` ports + `repository_adapters.py` sqlite adapters that call
`memory.finance.*` only, `services/` domain services, `mutations.py` MutationEvent
builders, `value_objects.py` closed enums, `projections.py` read models, and
per-subcontext subpackages like `cashback/`, `rewards/`, `payments/`).

---

## 0. Alignment with existing architecture (read first)

These are the invariants every later section obeys. They are transcribed from the
real `domains/finance/` layout and `tests/architecture/test_dependencies.py`.

| Invariant | Source | How WorkOS honors it |
|---|---|---|
| A domain may import **only** `memory` and `runtime`. | `ALLOWED_EDGES["domains.finance"] = {"memory","runtime"}` | `domains.work` gets the **same** edge set: `{memory, runtime}`. Nothing else. |
| A domain **never** imports another domain. | [ADR 0011](adr/0011-domain-isolation.md) | `domains.work` never imports `domains.finance`; the reverse is already true. |
| Memory is the only persistence owner. | [ADR 0004](adr/0004-memory-is-the-only-storage-owner.md) | All WorkOS rows live under `memory/work/`; adapters call it, nothing opens sqlite/lancedb. |
| Brain is the only Claude client. | [ADR 0003](adr/0003-brain-is-the-only-claude-client.md) | No WorkOS package imports Anthropic or holds a key. AI runs as Brain jobs reading Memory ([§12](#12-ai-architecture)). |
| Every write is a `MutationEvent` → `finalize_mutations()`. | [ADR 0005](adr/0005-mutationevent-as-atomic-state-change.md) | `domains/work/mutations.py` builds events; the runtime pipeline finalizes them ([§8](#8-mutation-events), [§10](#10-runtime-integration)). |
| Planner is the chat/command integration layer into a domain. | `ALLOWED_EDGES["services.planner"] ⊇ {"domains.finance"}` | Planner gains a `domains.work` edge and `work_commands/queries/serializers` modules ([§9](#9-planner-integration)). |
| `services.api` is the cross-domain facade (top of the graph). | `ALLOWED_EDGES["services.api"]`, `projections/home.py` | Cross-domain read models (ROI = Work × Finance) are assembled in `services.api`, not inside a domain ([§13](#13-cross-domain-interactions)). |
| Money is integer minor units; `occurred_on`≠`created_at`; soft-delete via a nullable timestamp. | `domains/finance/*`, `FINANCE_DATA_MODEL.md` | WorkOS reuses these conventions verbatim; time is integer minutes. |

**The two edges WorkOS needs added to `ALLOWED_EDGES` (human-gated, [§16](#16-architecture-review)):**
`domains.work → {memory, runtime}` (new domain) and
`services.planner → …, domains.work` (chat integration). `services.api`'s existing
facade set gains `domains.work`. No other edge changes; in particular **no
`domains.work → domains.finance` edge is created** — that isolation is the point.

---

## 1. Domain Decomposition (bounded contexts)

WorkOS is a **single domain package** `domains/work/` containing **seven internal
bounded contexts** as subpackages — the same structure Finance uses, where
`cashback/`, `rewards/`, and `payments/` are subcontexts inside the one
`domains/finance/` domain. The contexts are a modeling/ownership boundary enforced
by directory structure and convention; the *import-boundary* tests only police the
`domains.work ↔ domains.finance` edge (which stays empty).

Why one domain and not seven: the contexts reference each other constantly (a
Sprint commits WorkItems, an Engagement delivers via a Milestone, a Goal weights a
Project). If each were a *domain* they could not import each other (ADR 0011) and
every everyday link would route through Brain or the root — turning one
consistency boundary into a mesh. This mirrors Finance exactly: rewards reference
accounts and transactions freely *within* the domain. **This single-domain
decision requires a new ADR** ([§16](#16-architecture-review)).

The seven contexts and their dependency direction (higher reads lower; **Insights
reads all, owns nothing**):

```
                         ┌───────────────────────────────────────┐
                         │            INSIGHTS (context G)         │  ← no storage
                         │  dashboards · reviews · health · risk   │     (read models
                         │  reports · CEO dashboard · briefing     │      + Brain fusion)
                         └───────────────┬─────────────────────────┘
             reads read-models from every context below
   ┌───────────────┬───────────────┬────┴────────┬───────────────┬───────────────┐
   ▼               ▼               ▼             ▼               ▼               ▼
┌────────┐   ┌──────────┐    ┌───────────┐  ┌────────────┐  ┌─────────┐   ┌───────────┐
│PLANNING│──▶│EXECUTION │    │ENGAGEMENTS│  │  GROWTH    │  │WORKSPACE│   │           │
│  (B)   │   │   (C)    │    │    (D)     │  │    (E)     │  │   (F)   │   │           │
│sprint  │   │day plan  │    │client      │  │goal/OKR    │  │meeting  │   │           │
│roadmap │   │time entry│    │engagement  │  │learning    │  │note     │   │           │
│priority│   │focus     │    │revenue exp │  │career/life │  │doc ref  │   │           │
│queue   │   │capacity  │    │deliverable │  │key result  │  │action   │   │           │
└───┬────┘   └────┬─────┘    └─────┬──────┘  └─────┬──────┘  └────┬────┘   │           │
    └─────────────┴────────────────┴───── all read ┴──────────────┘        │           │
                                 ▼                                          │           │
                         ┌───────────────┐                                  │           │
                         │   WORK (A)     │  ◀───────────────────────────────┘           │
                         │ project·epic   │  the delivery graph — the spine              │
                         │ story·task     │                                              │
                         │ milestone·dep  │                                              │
                         └───────────────┘                                              │
```

For each context: **responsibility · owns · does NOT own · communicates with ·
projections it produces · mutation-event namespaces · read models it consumes.**

### A — Work (delivery graph — the spine)
- **Responsibility:** integrity of the work hierarchy — every task has a valid,
  acyclic parent chain; progress rolls up; dependencies form no cycles.
- **Owns:** `Project`, `WorkItem` (epic/story/task/subtask via `type`),
  `Milestone`, `Dependency`, saved `Board`/`View` definitions.
- **Does NOT own:** scheduling (Execution), ranking (Planning), money
  (Engagements/Finance), doc bodies (Workspace/Knowledge), the *decision* of what
  to do (Insights/Brain).
- **Communicates with:** every context reads it. It reads nothing but Memory.
- **Projections produced:** `Portfolio`, `ProjectTree`, `Board`, `Backlog`.
- **Mutation namespaces:** `work.project.*`, `work.item.*`, `work.milestone.*`,
  `work.dependency.*`.
- **Read models consumed:** none (it is the root of the internal graph).

### B — Planning (deciding what & when)
- **Responsibility:** turn the backlog into an ordered, sequenced intent — ranking,
  estimation, sprint composition, roadmap layout.
- **Owns:** `Sprint`, `RoadmapPlan` (saved sequencing), backlog ordering,
  estimation calibration state.
- **Does NOT own:** the items themselves (Work), the actual day/time (Execution),
  the AI model (Brain proposes; Planning records the committed decision).
- **Communicates with:** reads Work (items, deps), Growth (goal weight), Execution
  (velocity/capacity history), Engagements (deadlines/value).
- **Projections produced:** `PriorityQueue`, `Roadmap`, `SprintPlan`, `Backlog`.
- **Mutation namespaces:** `work.sprint.*`, `work.roadmap.*`, `work.estimate.*`,
  `work.priority.*` (weight-policy changes only — computed scores are not stored).
- **Read models consumed:** `Capacity`, `Velocity`, `GoalWeights`.

### C — Execution (doing & tracking)
- **Responsibility:** the truth of *what actually happened* with time and focus,
  and the committed plan for a day.
- **Owns:** `DayPlan`, `TimeBlock`, `TimeEntry`, `FocusSession`.
- **Does NOT own:** the calendar itself (injected Calendar handler), the items it
  schedules (Work), the ranking (Planning).
- **Communicates with:** reads Work (items) and Planning (priority queue); reaches
  **Calendar** via an injected handler ([§13](#13-cross-domain-interactions)).
- **Projections produced:** `TodaysFocus`, `Capacity`, `TimeInvested`, `Velocity`.
- **Mutation namespaces:** `work.plan.*`, `work.timeblock.*`, `work.timeentry.*`,
  `work.focus.*`.
- **Read models consumed:** `PriorityQueue`, external calendar busy-blocks.

### D — Engagements (who it's for & what it's worth)
- **Responsibility:** commitments to clients and the *attribution/expectation* of
  revenue to work.
- **Owns:** `Client`, `Engagement` (a.k.a. FreelanceProject/Contract),
  `Deliverable`, `RevenueExpectation`, `Interaction`.
- **Does NOT own:** realized money, invoices, the ledger — those are **Finance**.
  Owns only *expected* value and the attribution link.
- **Communicates with:** links to Work (Project/Milestone). Realized revenue is
  read from **Finance** at the `services.api` facade, never by a domain import.
- **Projections produced:** `FreelancingSummary`, `RevenueExpectationBook`,
  `ClientHealth`.
- **Mutation namespaces:** `work.client.*`, `work.engagement.*`,
  `work.deliverable.*`, `work.revenue.*`, `work.interaction.*`.
- **Read models consumed:** `ProjectTree`; Finance realized-revenue (via facade).

### E — Growth (the why — strategy)
- **Responsibility:** long-horizon outcomes that give work strategic weight.
- **Owns:** `Goal`/`Objective`, `KeyResult`, `LearningItem`/`LearningPath`,
  `CareerRoadmap` config, `LifeGoal`. **Reuses** `Habit` from existing
  `memory/habits.py` — does not re-own it.
- **Does NOT own:** the projects that fulfil goals (Work); habits' storage.
- **Communicates with:** links contributions to Work projects; supplies goal
  weight to Planning.
- **Projections produced:** `GoalWeights`, `LearningProgress`, `QuarterProgress`,
  `PersonalScorecard`.
- **Mutation namespaces:** `work.goal.*`, `work.keyresult.*`, `work.learning.*`,
  `work.lifegoal.*`.
- **Read models consumed:** `ProjectTree`, habit adherence (from Memory).

### F — Workspace (capture → structure)
- **Responsibility:** capture unstructured context (meetings, notes, docs) and
  convert it into actionable work.
- **Owns:** `Meeting`, `Note`/`Capture`, `ActionItem`, a `Document` **reference**
  (pointer + relations, not the body).
- **Does NOT own:** document bodies or embeddings — the **Knowledge Graph /
  Memory semantic** store owns those.
- **Communicates with:** produces `ActionItem` → Work items; hands note/meeting
  text to `services.knowledge` for embedding (orchestrated above the domain).
- **Projections produced:** `MeetingLog`, `CaptureInbox`, `ActionItemQueue`.
- **Mutation namespaces:** `work.meeting.*`, `work.note.*`, `work.actionitem.*`,
  `work.document.*`.
- **Read models consumed:** semantic search results (from Knowledge, via facade).

### G — Insights (the answers — no storage)
- **Responsibility:** every dashboard, review, health score, risk, and briefing.
- **Owns:** **nothing persistent** except tiny user artifacts (pinned risks, saved
  report/dashboard configs).
- **Does NOT own:** any primitive — it only reads them.
- **Communicates with:** reads read-models from all contexts; delegates all
  reasoning to **Brain**; emits its outputs as *reports* (a stored artifact) or
  serves them live.
- **Projections produced:** `Dashboard`/`CEODashboard`, `WeeklyReview`,
  `MonthlyReview`, `ProjectHealth`, `RiskRegister`, `RevenueForecast`, `BurnRate`,
  `DeadlineRisk`, `Briefing`.
- **Mutation namespaces:** `work.review.*` (generated reports), `work.risk.*`
  (user-pinned risks only). Everything else is read-only and stateless.
- **Read models consumed:** all of the above.

---

## 2. Folder Structure

Every package mirrors a package that already exists in `domains/finance/`. The
*why* column cites the Finance precedent.

```
apps/backend/
├── memory/
│   └── work/                         # persistence — the ONLY writer of work rows
│       ├── __init__.py               #   public API (like memory/finance/__init__.py)
│       ├── projects.py               #   one module per table family, per memory/finance/*
│       ├── items.py                  #   work items (epic/story/task/subtask)
│       ├── milestones.py
│       ├── dependencies.py
│       ├── sprints.py
│       ├── roadmaps.py
│       ├── plans.py                  #   day plans + time blocks
│       ├── time_entries.py
│       ├── focus_sessions.py
│       ├── clients.py
│       ├── engagements.py            #   engagements + deliverables + revenue expectations
│       ├── goals.py                  #   goals + key results
│       ├── learning.py
│       ├── meetings.py               #   meetings + action items
│       ├── notes.py                  #   notes + document refs
│       ├── reports.py                #   generated review artifacts + pinned risks
│       ├── seed.py                   #   default workspace seeding (per memory/finance/seed.py)
│       └── migrations.py             #   idempotent DDL (per memory/finance/migrations.py)
│
├── domains/
│   └── work/                         # the WorkOS domain — imports ONLY memory + runtime
│       ├── __init__.py
│       ├── value_objects.py          # shared closed enums/VOs (per finance/value_objects.py)
│       ├── errors.py                 # domain exceptions (per finance/errors.py)
│       ├── validation.py             # pure invariant checks (per finance/validation.py)
│       ├── aggregates.py             # WORK context roots: Project, WorkItem, Milestone, Dependency
│       ├── repositories.py           # WORK context ports (per finance/repositories.py)
│       ├── repository_adapters.py    # WORK sqlite adapters → memory.work (per finance/repository_adapters.py)
│       ├── mutations.py              # WORK MutationEvent builders (per finance/mutations.py)
│       ├── projections.py            # WORK read models (per finance/*/projections.py)
│       ├── services/                 # WORK domain services (per finance/services/)
│       │   ├── project_service.py
│       │   ├── work_item_service.py
│       │   ├── milestone_service.py
│       │   └── dependency_service.py
│       │
│       ├── planning/                 # context B — subpackage, per finance/rewards/
│       │   ├── aggregates.py         #   Sprint, RoadmapPlan
│       │   ├── value_objects.py      #   Estimate, PriorityWeights, Cadence
│       │   ├── repositories.py  repository_adapters.py  mutations.py  projections.py
│       │   ├── prioritization.py     #   pure ranking function (explainable)
│       │   └── services/             #   PlanningService, SprintService, RoadmapService, EstimationService
│       │
│       ├── execution/                # context C
│       │   ├── aggregates.py         #   DayPlan, TimeBlock, TimeEntry, FocusSession
│       │   ├── value_objects.py      #   TimeBlock(VO), Duration, FocusScore, EnergyScore
│       │   ├── repositories.py  repository_adapters.py  mutations.py  projections.py
│       │   └── services/             #   TimeTrackingService, DayPlanService, CapacityService
│       │
│       ├── engagements/              # context D
│       │   ├── aggregates.py         #   Client, Engagement, Deliverable, RevenueExpectation, Interaction
│       │   ├── value_objects.py      #   RateModel, RevenueForecast, ClientHealth
│       │   ├── money.py              #   re-exports domains.finance-free Money? → see note below
│       │   ├── repositories.py  repository_adapters.py  mutations.py  projections.py
│       │   └── services/             #   ClientService, EngagementService, RevenueProjectionService
│       │
│       ├── growth/                   # context E
│       │   ├── aggregates.py         #   Goal, KeyResult, LearningItem, LearningPath, LifeGoal
│       │   ├── value_objects.py      #   Progress, Confidence, Importance
│       │   ├── repositories.py  repository_adapters.py  mutations.py  projections.py
│       │   └── services/             #   GoalService, LearningService, CareerService
│       │
│       ├── workspace/                # context F
│       │   ├── aggregates.py         #   Meeting, Note, ActionItem, DocumentRef
│       │   ├── value_objects.py      #   Context(tag), CaptureSource
│       │   ├── repositories.py  repository_adapters.py  mutations.py  projections.py
│       │   └── services/             #   MeetingService, NoteService, ActionItemService
│       │
│       └── insights/                 # context G — read models + Brain-input assembly; NO repositories
│           ├── read_models.py        #   dataclasses describing each dashboard/review shape
│           ├── assemblers.py         #   pure functions: read-models → Brain-input bundles
│           ├── mutations.py          #   work.review.*, work.risk.* only
│           └── services/             #   HealthService, RiskService, ReviewService, ReportingService
│
├── runtime/
│   └── mutation_builders.py          # gains generic work builders IF any are cross-context;
│                                     #   per-context builders live in domains/work/**/mutations.py
│                                     #   (exactly as finance keeps builders in domains/finance/mutations.py)
│
└── services/
    ├── planner/
    │   ├── work_commands.py          # chat/REST write verbs → domain services (per finance_commands.py)
    │   ├── work_queries.py           # chat/REST reads (per finance_queries.py)
    │   └── work_serializers.py       # aggregate → envelope dict (per finance_serializers.py)
    └── api/
        ├── routers/work/             # thin routers per sub-resource (per routers/finance/)
        │   ├── _projects.py  _items.py  _milestones.py  _planning.py
        │   ├── _execution.py  _engagements.py  _growth.py  _workspace.py
        │   └── _insights.py
        └── projections/
            └── work_dashboard.py     # cross-domain aggregate (Work × Finance × Calendar), per home.py
```

**Why each package exists** (the non-obvious ones):

- **`memory/work/` split by table family** — mirrors `memory/finance/`'s
  one-module-per-family rule; keeps each file small and under the file-size limit,
  and keeps "the only place a work table is touched" obvious.
- **`repositories.py` (ports) separate from `repository_adapters.py` (sqlite)** —
  this is the Finance pattern verbatim: the port is the abstract contract the
  domain service depends on; the adapter is the sqlite implementation that calls
  `memory.work.*`. It exists so services never know about storage and tests can
  substitute a fake port. (See [§6](#6-repository-interfaces).)
- **Context subpackages (`planning/`, `execution/`, …)** — each repeats the
  aggregates/value_objects/repositories/adapters/mutations/projections/services
  shape, exactly as `finance/rewards/`, `finance/cashback/`, `finance/payments/`
  do. This is how a domain grows subcontexts without a mesh.
- **`insights/` has no repositories** — it owns no storage; it only reads other
  contexts' projections and assembles Brain inputs. Its lone writes (`reports`,
  pinned risks) go through `memory/work/reports.py`.
- **`prioritization.py` / `assemblers.py` as pure modules** — the ranking and
  context-assembly logic is pure and clock-injected (Handbook), so it is
  unit-testable without a DB and reusable by both the REST facade and Brain jobs.
- **`services/planner/work_*` trio** — planner is the sanctioned chat integration
  layer into a domain (it already imports `domains.finance`); WorkOS gets the same
  commands/queries/serializers trio.
- **`services/api/projections/work_dashboard.py`** — cross-domain fusion (Work +
  Finance realized revenue + Calendar) belongs at the facade, never in a domain
  (the `home.py` precedent). This is the *only* place Work and Finance data meet.

> **Note on Money reuse:** WorkOS needs a `Money` value object for revenue
> expectation. It must **not** import `domains.finance.money.MoneyAmount` (domain
> isolation). Options for the ADR to decide: (a) promote `MoneyAmount` to a shared
> root utility (like `identity.py`/`paths.py`) both domains import; or (b) give
> `engagements/` its own minor-unit `Money` VO. Recommended: **(a)** — one money
> type across Nova prevents drift. This is a boundary change → ADR-gated
> ([§16](#16-architecture-review)).

---

## 3. Aggregate Design

Each aggregate is a frozen dataclass with a `from_row` classmethod (the Finance
`aggregates.py` shape). An **aggregate root** is the only entry point for editing
its internals; nothing outside holds a reference to an internal entity except
through the root. Conventions inherited from Finance: integer minor-unit money,
integer-minute durations, `*_on`/`occurred_on` domain dates separate from
`created_at`/`updated_at` audit dates, nullable `deleted_at`/`archived_at`
soft-delete.

### Context A — Work

**`Project`** (root)
- *Responsibilities:* holds objective, date range, lifecycle, health inputs,
  optional engagement link; is the anchor everything hangs off.
- *Invariants:* exactly one lifecycle state; milestone dates ⊆ project date range;
  completion % is a consistent roll-up, never free-typed; a project links to
  0..1 engagement.
- *Lifecycle:* `idea → planned → active → (paused ⇄ active) → completed | archived`.
  `blocked` is **derived** (all active items blocked), never stored.
- *Relationships:* has many `Milestone`, `WorkItem`; contributes to `Goal`; may
  belong to an `Engagement`.

**`WorkItem`** (root — unified epic/story/task/subtask)
- *Responsibilities:* the unit of execution; carries `type`, parent link, estimate,
  status, priority inputs, dependency edges.
- *Invariants:* parent chain is acyclic and type-valid (`subtask ∈ task ∈ story ∈
  epic ∈ project`); a `done` item has all blocking deps satisfied; belongs to
  exactly one project and at most one active sprint; estimate carries confidence.
- *Lifecycle:* `backlog → todo → in_progress → (blocked ⇄ in_progress) → in_review
  → done | cancelled`.
- *Relationships:* self-referencing parent; has `Dependency` edges; logged by
  `TimeEntry`; committed in a `Sprint`.
- *Why unified:* one lifecycle/estimate/priority/dependency model across four
  levels — the same `type`-discriminator move Finance used to unify
  bills/subscriptions/EMIs. Four rigid tables cannot be reparented; one tree can.

**`Milestone`** (entity inside `Project`)
- *Invariants:* dates within project range; drives project completion %.
- *Lifecycle:* `pending → in_progress → reached | missed` (`missed` derived on
  target-date passing, then confirmed).

**`Dependency`** (entity/edge)
- *Responsibilities:* a typed edge between two WorkItems or Projects.
- *Invariants:* endpoints exist; edge set is acyclic (validated on add); type ∈
  `{blocks, blocked_by, relates_to}`.

### Context B — Planning

**`Sprint`** (root)
- *Invariants:* committed effort recorded against a fixed capacity; an item is in
  ≤1 active sprint; sprint dates don't overlap another active sprint.
- *Lifecycle:* `planned → active → completed`; incomplete items propose
  carry-forward on completion.

**`RoadmapPlan`** (root) — saved sequencing of milestones/projects over time.
- *Invariants:* references only existing projects/milestones; each has a planned
  window; over-capacity windows are *flagged*, not forbidden.

### Context C — Execution

**`DayPlan`** (root, contains `TimeBlock`)
- *Invariants:* blocks don't overlap; total planned ≤ capacity is a **soft**
  invariant (over-allocation flagged); a `proposed` plan has no side effects.
- *Lifecycle:* `proposed → committed → in_progress → done`.

**`TimeEntry`** (leaf root) — actual time against a WorkItem/Project.
- *Invariants:* integer minutes; immutable once `closed`; sums are exact.
- *Lifecycle:* `open → closed`.

**`FocusSession`** (root) — a tracked session that produces TimeEntries.
- *Invariants:* one active session at a time; interruptions counted; closing
  produces exactly one TimeEntry.

### Context D — Engagements

**`Client`** (root, contains `Interaction`)
- *Invariants:* health/last-contact derive only from its own interactions.

**`Engagement`** (root, contains `Deliverable`, `RevenueExpectation`)
- *Responsibilities:* the freelance/consulting commitment — scope, rate model,
  value, dates, linked project(s).
- *Invariants:* sum of deliverable values reconciles to engagement value; belongs
  to one client; `RevenueExpectation` attaches to exactly one engagement *or*
  project (exclusive).
- *Lifecycle:* `prospect → proposed → active → (on_hold ⇄ active) → delivered →
  closed | lost`.

**`Deliverable`** (entity) — `pending → submitted → accepted | revising`.

### Context E — Growth

**`Goal`/`Objective`** (root, contains `KeyResult`)
- *Invariants:* progress is a defined function of its key results; contribution
  links point to existing projects.
- *Lifecycle:* `draft → active → (achieved | missed | abandoned)`.

**`KeyResult`** (entity) — measurable target with current/target values + trajectory.

**`LearningPath`** (root, contains `LearningItem`) — path progress rolls up from
items; each item serves a goal/career.

**`LifeGoal`** (root) — long-horizon personal outcome competing for the same hours.

### Context F — Workspace

**`Meeting`** (root, contains `ActionItem`)
- *Invariants:* action-item → WorkItem conversion is idempotent (re-processing a
  note never duplicates).

**`Note`/`Capture`** (root) — fast unstructured capture; triaged later into
items/notes. **`DocumentRef`** (root) — pointer + relations to a Knowledge-Graph
document; never stores the body.

### Context G — Insights
No stored aggregates except **`Report`** (a generated review artifact:
weekly/monthly/quarter) and **`PinnedRisk`** (a user-elevated risk). Everything
else is a projection ([§7](#7-projections)).

---

## 4. Value Objects

Immutable, identity-free, compared by value; closed enums live in each context's
`value_objects.py` (the Finance `AccountType`/`Direction` pattern). Every AI-touched
VO carries **confidence** and can render **reasons** (ADR 0015/0016).

| Value Object | Context | Captures | Rule |
|---|---|---|---|
| `Priority` (Score) | Planning | computed rank + component reasons | Derived only — **never stored** as a field; recomputed on read. |
| `Importance` | Planning | strategic weight from goals | 0..1 contribution from linked active goals. |
| `Estimate` | Planning | expected effort | Integer minutes/points **+ Confidence band**; never a bare number. |
| `PriorityWeights` | Planning | user's ranking policy | The only *stored* priority artifact (a weight vector), tunable. |
| `Deadline` | Work/Engagements | due date + hardness | `hard` (contractual) vs `soft`; drives risk. |
| `Progress` | Work/Growth | 0–100% | Always a roll-up function, never typed on parents. |
| `DateRange` | Work | start/target/actual | Separates planned end from actual; slippage = actual − target. |
| `Duration` | Execution | elapsed/estimated time | Integer minutes; exact sums. |
| `TimeBlock` | Execution | a scheduled span | start+duration+item ref; overlap-checked. |
| `FocusScore` | Execution | quality of a focus session | derived from interruptions/duration. |
| `EnergyScore` | Execution | inferred energy at a time-of-day | from historical throughput; feeds day-plan sequencing. |
| `Money` | Engagements | expected/realized value | Integer minor units; **shared type**, not a Finance import (see §2 note). |
| `RateModel` | Engagements | how an engagement earns | `fixed \| hourly \| retainer` + amount. |
| `RevenueForecast` | Engagements/Insights | predicted revenue | amount **+ Confidence band** (mandatory). |
| `ROI` | Insights | value ÷ time | pure derivation carrying its inputs (expected revenue, invested minutes). |
| `HealthScore` | Insights | project vitality | band `on_track \| at_risk \| off_track` + reason vector; recomputed, never stored. |
| `RiskLevel` | Insights | severity of a risk | `low \| medium \| high \| critical` + reason. |
| `Confidence` | all | model certainty | attached to every estimate/forecast/score (ADR 0016). |
| `Cadence` | Planning/Insights | recurrence | for sprints/reviews; reuses Finance's cadence vocabulary conceptually. |
| `Context` (tag) | Workspace | capture bucket | free tag used to triage captures. |
| `CaptureSource` | Workspace | origin of a capture | `voice \| chat \| manual \| meeting \| import`. |

---

## 5. Services (domain services — responsibilities only)

Domain services hold logic that is more than a row insert; they depend on **ports**
(§6), never on adapters or Memory directly, and return aggregates. They never call
Claude and never open the DB (the Finance service pattern). Instantiated as
module-level singletons by the planner/API layers, exactly as `finance_commands.py`
instantiates `AccountService()` etc.

| Service | Context | Responsibility (only) |
|---|---|---|
| `ProjectService` | Work | Create/update/archive projects; enforce lifecycle transitions; roll up completion from milestones/items. |
| `WorkItemService` | Work | Create/reparent/transition items; enforce acyclic type-valid hierarchy; block/unblock from deps. |
| `MilestoneService` | Work | Manage milestones; detect reached/missed against target dates (clock injected). |
| `DependencyService` | Work | Add/remove edges; reject cycles; expose blocking/critical-path adjacency. |
| `PlanningService` | Planning | Orchestrate backlog ordering; assemble the sprint/roadmap decision the human commits. |
| `PrioritizationService` | Planning | Compute the explainable `Priority` score from the pure `prioritization.py` function + `PriorityWeights`; returns reasons. |
| `EstimationService` | Planning | Propose estimates from historical similars; calibrate estimate-vs-actual bias; attach confidence. |
| `SprintService` | Planning | Compose/activate/close sprints; propose carry-forward; respect dependency order. |
| `RoadmapService` | Planning | Lay milestones/projects over time; flag over-capacity windows. |
| `TimeTrackingService` | Execution | Open/close time entries and focus sessions; guarantee exact minute sums; produce velocity/time-invested. |
| `DayPlanService` | Execution | Turn a proposed plan into committed time blocks; enforce non-overlap; sync blocks to Calendar via injected handler. |
| `CapacityService` | Execution | Compute available hours from calendar busy-blocks, habits, and meetings. |
| `ClientService` | Engagements | Manage clients + interactions; derive client health/last-contact. |
| `EngagementService` | Engagements | Manage engagements/deliverables; reconcile deliverable values to engagement value. |
| `RevenueProjectionService` | Engagements | Turn rate model + trajectory into a `RevenueForecast` with confidence (expectation side only). |
| `GoalService` | Growth | Manage goals/key results; roll up progress; expose goal weights to Planning. |
| `LearningService` | Growth | Manage learning paths/items; roll up progress; connect items to goals/career. |
| `CareerService` | Growth | Sequence career milestones/skills into a roadmap view. |
| `MeetingService` | Workspace | Manage meetings; extract action items idempotently. |
| `NoteService` | Workspace | Capture/triage notes; manage document references. |
| `ActionItemService` | Workspace | Convert action items → work items without duplication. |
| `HealthService` | Insights | Compute per-project `HealthScore` + reasons from schedule/velocity/blocked/staleness. |
| `RiskService` | Insights | Derive the risk register (deadline/dependency/over-allocation/staleness/revenue-at-risk); manage pinned risks. |
| `ReviewService` | Insights | Assemble weekly/monthly/quarter review inputs; record generated reports. |
| `ReportingService` | Insights | Render/export reports; persist report artifacts. |
| `DeadlineService` | Insights | Detect at-risk and colliding deadlines against capacity; feed reminders. |

**AI note:** the `*Service` classes prepare inputs and record human-committed
decisions; the *reasoning* that produces a proposal (rank, plan, forecast) is a
**Brain job** ([§12](#12-ai-architecture)), not a domain service — because a domain
cannot import Brain. `PrioritizationService`'s scoring function is deterministic
and explainable; Brain is used where genuine reasoning (planning narrative,
risk explanation, review synthesis) is needed.

---

## 6. Repository Interfaces (ports)

Abstract contracts only — **no SQL, no implementation**. Each has a matching
sqlite adapter in `repository_adapters.py` that calls `memory.work.*` and returns
aggregates (the exact `SqliteAccountRepository → memory.finance.accounts` shape).
Services depend on the port; tests substitute a fake. Standard responsibilities
across ports: `create`, `get_by_id`, `list_*` (filtered), `update`, `soft_delete`,
plus aggregate-specific query shapes noted below.

| Port | Aggregate-specific responsibilities (beyond CRUD) |
|---|---|
| `ProjectRepository` | list by status/engagement/goal; completion roll-up inputs; count live items. |
| `WorkItemRepository` | list by project/parent/sprint/status; fetch subtree; fetch blocked-by set. |
| `MilestoneRepository` | list by project; find due-before-date; find missed. |
| `DependencyRepository` | list edges for an item/project; fetch adjacency for cycle/critical-path checks. |
| `SprintRepository` | active sprint; committed items; capacity vs committed sums. |
| `RoadmapRepository` | saved roadmap plans; windows by project/milestone. |
| `DayPlanRepository` | plan for a date; committed blocks; overlap checks. |
| `TimeEntryRepository` | entries by item/project/date range; sum minutes exactly; velocity windows. |
| `FocusSessionRepository` | active session; sessions by date; interruption stats. |
| `ClientRepository` | clients with last-interaction; interactions by client. |
| `EngagementRepository` | engagements by client/status; deliverables; revenue expectations by project/engagement. |
| `RevenueExpectationRepository` | expectations by period; expected totals. |
| `GoalRepository` | goals by status; key results by goal; contribution links by project. |
| `LearningRepository` | paths + items; progress roll-up inputs. |
| `MeetingRepository` | meetings by date; action items by meeting. |
| `NoteRepository` | captures (untriaged); notes by tag; document refs. |
| `ReportRepository` | reports by period/type; pinned risks. |

Ports live per context (`domains/work/repositories.py` for Work,
`domains/work/planning/repositories.py` for Planning, …), matching how
`finance/rewards/repositories.py` sits beside `finance/repositories.py`.

---

## 7. Projections (read models)

Projections own no storage; they are computed by pure assemblers over ports (the
`services/api/projections/home.py` / `finance/*/projections.py` pattern). Each is a
described **shape + its inputs** — no fields enumerated (that is a later gate).

| Projection | Context assembled in | Inputs |
|---|---|---|
| `PriorityQueue` | Planning | items + deps + deadlines + goal weights + `PriorityWeights` + decay. **The spine.** |
| `TodaysFocus` | Execution/Insights | committed DayPlan + PriorityQueue + calendar + capacity. |
| `Roadmap` | Planning | projects + milestones + planned windows + capacity flags. |
| `Backlog` | Work/Planning | items not in an active sprint, ordered by priority. |
| `Dashboard` / `CEODashboard` | Insights (facade) | project health + ROI + revenue (Work×Finance) + time allocation + risks. |
| `WeeklyReview` / `MonthlyReview` | Insights | completed-vs-planned + slippage + allocation + habit adherence + goal movement. |
| `QuarterProgress` | Growth/Insights | goals + key-result trajectories + milestone hits. |
| `RevenueForecast` | Engagements/Insights | revenue expectations + trajectory + Finance realized (facade). |
| `BurnRate` | Insights | time invested per project vs value (ROI-per-hour trend). |
| `DeadlineRisk` | Insights | deadlines + velocity + capacity collisions. |
| `FreelancingSummary` | Engagements | engagements + deliverables + expected/realized per client. |
| `LearningProgress` | Growth | learning paths/items progress + goal linkage. |
| `PersonalScorecard` | Growth/Insights | goals + habits + life goals adherence. |
| `ProductHealth` / `ProjectHealth` | Insights | schedule variance + velocity + blocked + staleness. |
| `Portfolio` | Work/Insights | roll-up across all projects. |
| `RiskRegister` | Insights | derived risks + pinned risks. |
| `Briefing` | Insights (Brain) | PriorityQueue + deadlines + calendar + risks + revenue → narrated. |

Cross-domain projections (`Dashboard`, `RevenueForecast`, `BurnRate`) are assembled
in **`services/api/projections/`**, never inside the domain, because only the
facade may read both Work and Finance ([§13](#13-cross-domain-interactions)).

---

## 8. Mutation Events

Built in each context's `mutations.py` as pure `build_*` functions returning a
`MutationEvent(event_type, entity_type, operation, entity, metadata)` — the exact
`domains/finance/mutations.py` shape. **`MutationEvent`'s dataclass is untouched.**

**Naming:** `work.<entity>.<operation>`, matching `finance.<entity>.<operation>`.

**Payload philosophy** (transcribed from Finance):
- `entity` is the **full aggregate row** (`dataclasses.asdict` of the frozen
  aggregate) — self-contained, no lazy references.
- `entity_type` is the singular noun (`project`, `work_item`, `milestone`, …) and
  is additive to the mutation vocabulary — **no new `MutationEvent` shape**.
- `operation` is a verb from a small closed set (`create`, `update`, `delete`,
  `archive`, `complete`, `transition`, `plan`, `commit`, `log`, `generate`).
- `metadata` carries ids for invalidation/routing (`entity_id`, `project_id`,
  `parent_id`), never business data.
- **Must not** contain chat/REST/producer-specific fields (the `MutationEvent`
  docstring rule).
- **Proposals are not mutations.** An AI-proposed plan/sprint/ranking emits **no**
  event until the human commits; only the committed decision is a `MutationEvent`.
- **Orchestrated multi-write** operations emit one composite event with legs (the
  `build_transfer_created`/`build_statement_paid` precedent) — e.g.
  `work.actionitem.promoted` carrying both the closed action item and the new work
  item.

**Representative namespaces** (not exhaustive; each gate adds its own):

```
work.project.created | .updated | .archived | .completed
work.item.created | .updated | .transitioned | .completed | .cancelled | .reparented | .deleted
work.milestone.created | .updated | .reached | .missed
work.dependency.added | .removed
work.sprint.planned | .started | .completed
work.roadmap.updated
work.priority.reweighted            (weight-policy change; scores themselves are never events)
work.plan.proposed*                 (*emitted only on human commit → .committed)
work.plan.committed
work.timeblock.scheduled | .moved | .removed
work.timeentry.logged | .updated | .deleted
work.focus.started | .ended
work.client.created | .updated | .archived
work.engagement.created | .updated | .transitioned | .closed
work.deliverable.submitted | .accepted
work.revenue.expected | .reattributed
work.interaction.logged
work.goal.created | .updated | .achieved | .abandoned
work.keyresult.updated
work.learning.created | .progressed | .completed
work.lifegoal.created | .updated
work.meeting.logged
work.actionitem.created | .promoted
work.note.captured | .triaged
work.document.linked
work.review.generated
work.risk.pinned | .cleared
```

**Memory-producer policy** (per `memory_producers.py`): memorable mutations
(project created/completed, milestone reached, engagement won/closed, goal
achieved) produce a semantic memory; routine churn (item edits, time logs) does
**not** — identical to "log spending doesn't, loan closure does" in Finance.

---

## 9. Planner Integration

`services/planner` is Nova's chat/command integration layer into a domain — it
already imports `domains.finance` and exposes `finance_commands.py`,
`finance_queries.py`, `finance_serializers.py`. WorkOS adds the parallel trio; the
`ALLOWED_EDGES` entry `services.planner → …, domains.work` is added (ADR-gated).

- **`work_commands.py`** — thin write verbs, one per user-meaningful action,
  returning the `(dict, message)` envelope that `finance_commands.py` returns.
  Each instantiates the relevant domain service singleton, calls it, and lets the
  caller (chat pipeline or REST router) build + finalize the MutationEvent. It does
  **not** open the DB or call Brain. Examples of *responsibilities* (not code):
  create project, add/complete/reparent item, plan sprint, log time, mark
  milestone reached, log meeting, promote action item, set goal.
- **`work_queries.py`** — read helpers for chat/voice ("what's on today?", "how's
  project X?") that call the projection assemblers/ports and return serialized read
  models. Read-only; no events.
- **`work_serializers.py`** — pure aggregate/read-model → plain-dict translators
  (the `serialize_account`/`serialize_transaction` role), giving chat, voice, and
  REST one consistent envelope shape.

**Chat/voice parity** is delivered per gate exactly as Finance did: the verbs that
make sense by voice ("add a task to the export project, 2 hours, due Friday", "mark
the auth task done", "plan my week") get `mutation_chat` translation and parity
tests in the same gate that introduces the mutation. The verb lexicon obeys the
Handbook §2 naming/verb rules.

---

## 10. Runtime Integration

WorkOS plugs into the existing pipeline without changing it (the ADR 0005/0006/0007
guarantees):

- **`MutationEvent` + `finalize_mutations()`** — every WorkOS write produces a
  `MutationEvent` (built in `domains/work/**/mutations.py`) that flows through
  `runtime/side_effects.finalize_mutations()`, exactly like Finance. WorkOS adds
  **no** new pipeline stage. `runtime/mutation_builders.py` gains generic helpers
  only if a builder is genuinely cross-context; per-context builders stay in the
  domain (the Finance placement).
- **Brain** — the only Claude client. WorkOS never imports it. AI features are
  Brain jobs (`brain.run_daily_plan`, `brain.run_prioritization_narrative`,
  `brain.run_project_health`, `brain.run_weekly_review`, …) that **read Memory**
  read-models and return structured proposals. Orchestration (assemble inputs →
  call Brain → surface proposal → on human commit, call `work_commands`) happens at
  `services/api` or a scheduled runtime job — **above** the domain, so
  `domains.work → {memory, runtime}` stays clean. Follows the
  `knowledge.reflection → brain.run_reflection_job` precedent.
- **Context Engine** (`services/brain/context_engine`) — assembles the context
  bundle Brain reasons over. WorkOS contributes read-models (priority queue,
  capacity, project health inputs) to that bundle via Memory; it does not call the
  context engine directly.
- **Memory** — the sole system of record. All reads/writes go through
  `memory/work/`. WorkOS opens no connection (ADR 0004/0012/0013).
- **WebSocket / desktop push** — committed `MutationEvent`s are pushed to the
  desktop by `services/api` over the existing channel (per
  `DESKTOP_WRITE_OPERATIONS.md`). The desktop's `invalidation-map` maps each
  `work.*` event to the query keys it invalidates ([§11](#11-desktop-architecture)).
  WorkOS defines the mapping; it does not touch the transport.
- **Scheduling** — proactive jobs (nightly briefing, deadline sweep, review
  generation) run on the existing lazy/access-triggered scheduling model (the
  Finance statement-cycle sweep precedent) — **no new daemon**, no new process
  (ADR 0006/0019).

---

## 11. Desktop Architecture

Structure only — no components, no mockups. Follows the established per-domain
desktop conventions (the `FinanceLayout` + `mappers/finance/*` + `use-finance-*`
pattern described in `FINANCE_DOMAIN.md` §4).

- **Sidebar** — one top-level item **Work** (icon + `/work`), same flat sidebar as
  today; breadth lives in the section's sub-navigation, not the sidebar (the
  Finance decision).
- **Section layout** — a `WorkLayout` with sub-nav: *Today · Board · Projects ·
  Planning · Roadmap · Clients · Goals · Reviews · Dashboard*. First nested route
  group after Finance; structurally identical.
- **Routing** — `/work` is a nested route group with `WorkLayout` as element and
  children: `/work` (Today), `/work/board`, `/work/projects`,
  `/work/projects/:id`, `/work/planning`, `/work/roadmap`, `/work/clients`,
  `/work/clients/:id`, `/work/goals`, `/work/reviews`, `/work/dashboard`.
- **React Query strategy** — a nested `queryKeys.work` namespace mirroring
  `queryKeys.finance`: `.dashboard()`, `.today()`, `.projects(params)`,
  `.project(id)`, `.board(params)`, `.priorityQueue()`, `.roadmap()`,
  `.clients()`, `.goals()`, `.reviews(params)` — all under a `['nova','work']`
  root so one invalidation can sweep the domain. `invalidation-map.ts` maps each
  `work.*` event to its specific keys plus `work.dashboard`, `work.today`, and
  `home`.
- **View models** — per-screen view models in `view-models/work/` that shape
  aggregate/projection payloads for rendering (the Finance view-model layer).
- **Hooks** — `use-work-*.ts` hooks over `dataSource` (never `fetch` directly),
  with mock-mode parity in `dev/mocks`, exactly as `use-finance-*` does.
- **Mappers & contracts** — contract types in `packages/api-contracts`;
  `mappers/work/*.ts` translate wire → view model. Money via the shared `formatINR`
  formatter.
- **Component organization** — per-context folders under the Work section
  (`projects/`, `board/`, `planning/`, `today/`, `clients/`, `goals/`, `reviews/`,
  `dashboard/`), each with its screen + local components, mirroring how Finance
  groups its screens.

---

## 12. AI Architecture

Every AI capability is a **Brain job** (only Claude client) that: (1) reads a
Memory-backed input bundle assembled by an Insights/Planning assembler, (2) returns
a **structured proposal** with **reasons** (ADR 0015) and **confidence** (ADR 0016),
(3) is surfaced to the user, (4) mutates state **only** when the human commits (via
`work_commands` → `MutationEvent`). **No autonomous actions in v1.** Tiered models
(ADR 0002): local/cheap models for routine structuring (parsing a captured note,
tagging, similar-item lookup), the strong model for genuine reasoning.

For each feature — **inputs → outputs → confidence → reasons** (all mandatory):

| Feature | Inputs | Output (a proposal) | Confidence / Reasons |
|---|---|---|---|
| **Daily planning** | PriorityQueue, capacity, calendar, energy pattern, deadlines | proposed ordered DayPlan (time blocks) | per-block confidence + one-line why each block is placed. |
| **Prioritization** | items, deps, deadlines, goal weights, `PriorityWeights`, decay | ranked queue | component breakdown per item (deadline/revenue/strategic/blocking/decay). |
| **Deadline prediction** | milestone targets, velocity, capacity, dep chains | will-hit / will-miss + projected date | confidence band; the critical chain as the reason. |
| **Revenue prediction** | revenue expectations, trajectory, Finance realized (facade) | forecast per period/engagement | mandatory confidence band; assumptions listed. |
| **Sprint planning** | backlog, capacity, deps, goal weights | proposed committed set + carry-forward | why each item fits; what was left out and why. |
| **Weekly / monthly review** | completed-vs-planned, slippage, allocation, habits, goals | narrative review + next-period focus | confidence on trend claims; evidence per point. |
| **Executive briefing** | PriorityQueue, deadlines, calendar, risks, revenue | spoken/written morning brief | flags uncertainty explicitly; cites the driving items. |
| **Freelance advisor** | engagements, ROI-per-hour, client health, expected-vs-realized | which client/work is worth more time | reasons from ROI + health; confidence on projections. |
| **Career advisor** | goals, learning progress, career roadmap, capacity | next skills/steps + where they fit | reasons from goal linkage; confidence on fit. |
| **Risk detection** | deadlines, deps, allocation, staleness, revenue-at-risk | ranked risk register | severity + the specific condition triggering each. |
| **Burnout detection** | time entries, focus scores, allocation balance, habit adherence | early-warning signal | confidence; the pattern (e.g. sustained over-allocation) as reason. |
| **Project health** | schedule variance, velocity, blocked count/age, staleness, burn | `on_track/at_risk/off_track` + reason vector | recomputed each read; never asserted without reasons. |
| **Estimation** | historical similar items (vector), estimate-vs-actual bias | proposed estimate + your bias factor | confidence band; the similar items it drew from. |
| **Dependency detection** | item text, historical co-occurrence | suggested edges + cycle/critical-path flags | confidence per suggested edge; user confirms. |

**Guardrails (apply to all):** propose-never-mutate; explainable + uncertain by
construction; graceful degradation (with Brain unavailable, WorkOS is a
first-class manual tracker); local-first inputs. A Brain proposal is a transient
value object, not a `MutationEvent`, until committed.

---

## 13. Cross-Domain Interactions

The **only** edges leaving WorkOS, each obeying ADR 0011 (a domain never imports
another domain or a service):

| Target | What WorkOS needs | Allowed mechanism | Forbidden |
|---|---|---|---|
| **Finance** | realized revenue for ROI / revenue vs plan | Assemble the fused read model in **`services/api/projections/`** (the facade may read both domains — the `home.py` precedent). Alternatively, **Brain** fuses both from Memory. | `domains.work` importing `domains.finance` — **never**. |
| **Calendar** | busy-blocks (capacity) + write time-blocks | An **injected handler** passed by the composition root (ADR 0007) — the exact pattern Finance uses to reach Calendar (ADR 0017). WorkOS calls an injected port, not an import. | `domains.work` importing `services.calendar`. |
| **Memory** | all persistence + semantic similars | Direct `memory.work.*` (and read-only semantic queries Memory exposes). This is the one always-allowed downward edge. | opening sqlite/lancedb directly. |
| **Knowledge Graph** | embed meeting/note text; semantic search over work | WorkOS stores note/doc **references** in `memory.work`; `services.knowledge` (which owns embeddings) indexes them by reading Memory, **orchestrated at the composition root / api layer** — not a domain import. Search results reach WorkOS via the facade. | `domains.work` importing `services.knowledge`. |
| **Habits** | surface/link habits to goals | Read existing `memory/habits.py` through Memory's public API; do not re-own habit storage. | duplicating a habits table in `memory/work`. |

**Rule of thumb:** if two domains' data must meet, they meet **above** both — at
`services/api` (facade projection) or in **Brain** (fusion) — never by one domain
reaching into the other. The `ALLOWED_EDGES` table is the enforcement; the only
additions WorkOS makes are its own inbound edges, **not** a `work → finance` edge.

---

## 14. Future Expansion (extension points, not built)

Each is a *seam reserved now*, implemented later behind an ADR. Designing the seam
costs nothing; building it is out of scope.

| Extension | Reserved seam | Why it fits without redesign |
|---|---|---|
| **CRM depth** | `engagements/` already models Client/Interaction | Grow the Client aggregate + a `crm/` subcontext; no new domain. |
| **Hiring** | new `engagements/hiring/` or `growth/` subcontext | Candidates/roles are just another aggregate family under the same domain shape. |
| **Teams / multi-user / company mode** | reserve an `owner_id`/`workspace_id` scoping column on every `memory/work` table from day one | Single-operator today = one owner; multiplayer later filters by owner without a schema rewrite. **This scoping decision is ADR-gated now** so it's free later. |
| **GitHub / Jira / Linear import** | an `ImportPort` (external-source adapter) feeding the **same** `work_commands` → `MutationEvent` pipeline, read-only | Imports are just another `CaptureSource`; items enter through the existing write path, no parallel ingestion. |
| **Email / Slack capture** | `workspace/` `CaptureSource = email \| slack` | Captures already triage into work items; a new source is a new enum value + an injected reader. |
| **External write-back** (create a GitHub issue from a WorkItem) | a trust-gated outbound port, invoked by the future `agents` layer (Architecture v2) | Deferred behind autonomy; the domain stays local-first and never depends on the external system. |

Guiding constraint: **every external system is an optional enricher, never a
source of truth** (ADR 0001). The local SQLite remains ground truth; integrations
are injected ports at the composition root.

---

## 15. Implementation Roadmap

Milestone gates in the Finance rhythm (FIN-1…6): **backend + events + parity tests
first, desktop second; verify between gates.** Each ships an independently valuable
increment. `entity_type` vocabulary grows per gate.

| Gate | Theme | Backend | Desktop | Independently shippable as |
|---|---|---|---|---|
| **WOS-0** | Foundation *(human decision — no feature code)* | Accept ADRs ([§16](#16-architecture-review)); add `domains.work` + planner/api edges to `ALLOWED_EDGES`; decide shared `Money` + `owner_id` scoping. | — | The green light. |
| **WOS-1** | Projects | `memory/work` (projects) + `domains/work` Work-context core (Project aggregate, ports, adapters, `ProjectService`, mutations) + `routers/work/_projects` + planner verbs + parity tests. `entity_type`: `project`. | Work section shell + Projects list/detail with CRUD. | A local project tracker. |
| **WOS-2** | Tasks | WorkItem + Milestone + Dependency aggregates/services; hierarchy + cycle invariants; `work.item.*`/`.milestone.*`/`.dependency.*`. | Board + item editor (create/reparent/transition/complete); milestones on project. | A hierarchical task manager. |
| **WOS-3** | Planning | `planning/` subcontext: `PriorityWeights`, `PrioritizationService` (explainable), Backlog/PriorityQueue projections, Estimation. | Priority queue + backlog ordering + estimates UI. | "What's most important now?" |
| **WOS-4** | Milestones & Roadmap | Roadmap plans + capacity flags; `RoadmapService`; deadline detection inputs. | Roadmap (timeline) view; milestone tracking. | A planning/roadmap tool. |
| **WOS-5** | Reviews & Execution | `execution/` (DayPlan, TimeEntry, FocusSession, Capacity) + `insights/` ReviewService/ReportingService; weekly/monthly review + time tracking. | Today view, time tracking, reviews. | Time tracking + retrospectives. |
| **WOS-6** | AI Planning | Brain jobs: `run_daily_plan`, `run_prioritization_narrative`, `run_sprint_plan`, dependency/estimation assist; sprint subcontext. | Proposed day/sprint plans (commit flow). | The AI planner. |
| **WOS-7** | Revenue Intelligence | `engagements/` (Client/Engagement/Deliverable/RevenueExpectation) + **Finance cross-domain read seam** (facade) + `RevenueProjectionService` + ROI/RevenueForecast projections. | Clients, engagements, freelancing summary, ROI. | Freelance/founder revenue intelligence. |
| **WOS-8** | Executive Dashboard | `insights/` full: HealthService, RiskService, CEODashboard/Portfolio/BurnRate/DeadlineRisk projections + Briefing (Brain) + reminders integration. | Founder/CEO dashboard + risk register + morning briefing. | The chief-of-staff dashboard. |
| **WOS-9** | Automation | `workspace/` (Meeting/Note/ActionItem/DocumentRef) + Knowledge seam + capture triage; reserved import/automation seams (read-only). | Meetings → action items, capture inbox, note triage. | Context capture + light automation. |
| **WOS-10** | Personal Operating System | `growth/` (Goals/OKR, Learning, Career, Life goals) wired into prioritization weight; PersonalScorecard/QuarterProgress; habit surfacing. | Goals/OKRs, learning, career, personal scorecard. | The full personal OS. |

Chat/voice parity and memory-producer policy ride the gate that introduces each
mutation (the Finance discipline). WOS-1→3 is the minimum lovable WorkOS; 4–10 are
independently shippable breadth; the `agents`/external-write-back autonomy is a
post-v1 horizon (§14).

---

## 16. Architecture Review

*Assumptions, open questions, and the ADRs a human must decide before any WOS-1
code is written. Per Handbook §11.4, none of these are self-approvable — this
document drafts them for review and stops here.*

### Assumptions this design makes
1. **Single-operator v1.** No multi-user seating; other people are modeled, not
   authenticated. Multiplayer is designed-for via `owner_id` scoping (§14) but not
   built.
2. **WorkOS is one domain with internal contexts**, not seven domains — justified
   by the Finance precedent (rewards/cashback/payments as subcontexts) and by the
   mesh that over-splitting would create.
3. **Local SQLite stays the sole system of record;** all external systems are
   optional enrichers (ADR 0001).
4. **Time is integer minutes; money is integer minor units** — reused from
   Finance; no floats anywhere in WorkOS arithmetic.
5. **Computed-not-stored** for priority, health, ROI, and progress roll-ups —
   stored copies would rot; they are recomputed on read.

### Open questions (need a human answer before/at WOS-0)
1. **Shared `Money` type** — promote `MoneyAmount` to a root utility both domains
   import, or give `engagements/` its own `Money` VO? (Recommend: promote — one
   money type Nova-wide.) *Boundary change → ADR.*
2. **`owner_id`/`workspace_id` scoping now or later?** Adding it to every
   `memory/work` table on day one makes multiplayer free later but adds a column
   nothing uses in v1. (Recommend: add it now, default to the single operator.)
   *Schema shape → ADR.*
3. **Cross-domain ROI: facade projection vs Brain fusion** — should the
   Work×Finance read model live in `services/api/projections/` (deterministic) or
   be assembled by Brain (narrated)? (Recommend: facade for the numbers, Brain for
   the narration on top.)
4. **Where do proactive Brain jobs run?** Access-triggered (Finance sweep model)
   vs a scheduled runtime tick for the nightly briefing. (Recommend: access-
   triggered first; a scheduled tick only if a truly proactive push is wanted.)
5. **`WorkItem` type rigidity** — is the epic→story→task→subtask hierarchy fixed,
   or should arbitrary nesting be allowed? (Recommend: fixed type ladder with
   validated parent rules; revisit only if a real need appears.)

### ADRs required before implementation (drafts for human acceptance)
- **ADR — "WorkOS as the second domain."** Mirrors ADR 0017: records the
  single-domain-with-internal-contexts decision, confirms `domains.work → {memory,
  runtime}` and full compliance with 0004/0005/0011.
- **ADR — "WorkOS dependency edges."** Adds `domains.work`,
  `services.planner → domains.work`, and `services.api → domains.work` to
  `ALLOWED_EDGES`; confirms **no** `work → finance` edge; records the
  facade-fusion pattern for cross-domain reads.
- **ADR — "Shared money value object"** *(if Q1 = promote)*: moves the minor-unit
  money type to a shared root utility both domains depend on.
- **ADR — "Multi-tenant scoping reservation"** *(if Q2 = now)*: reserves
  `owner_id` on all `memory/work` tables ahead of any multiplayer feature.
- **Confirmation (likely no ADR):** the new `entity_type` values (§8) are additive
  to the mutation vocabulary and require **no** change to `MutationEvent`'s shape —
  to be verified against `runtime/mutation_event.py` at WOS-0.

**This document ends here. No implementation follows until the ADRs above are
accepted by a human.**
