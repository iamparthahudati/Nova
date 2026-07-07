# Nova WorkOS — Canonical Data Model v1 (Design Artifact)

**Status:** Design only. Nothing here is implemented. This document defines the
*conceptual* data model — aggregates, entities, relationships, lifecycles,
ownership, consistency rules, and projections. It contains **no SQL, no columns,
no ORM, no migrations, no code, no routes, no UI.** Physical column design is a
later gate and will be its own artifact per bounded context (the Finance sequence:
`FINANCE_DOMAIN.md` → `FINANCE_DATA_MODEL.md` → FIN-1 code).
**Companions:** scope/product in
[`NOVA_WORKOS_PRODUCT_SPEC_v1.md`](NOVA_WORKOS_PRODUCT_SPEC_v1.md); package/service
architecture in
[`NOVA_WORKOS_ARCHITECTURE_v1.md`](NOVA_WORKOS_ARCHITECTURE_v1.md). Where those and
this disagree on an *entity's shape or lifecycle*, **this document wins**; where
they disagree on *package placement or dependency edges*, the architecture doc
wins.
**Authority:** Subordinate to `docs/adr/*`, the frozen specs, and the Handbook
(`CLAUDE.md`). Anything here touching a package boundary, the dependency graph,
`MutationEvent`, a Claude tool schema, or a future DB schema is a **draft for
human review**; the ADRs required are in [§10](#10-architecture-review).

**Approved conventions baked into this model** (inherited from Finance, not
re-litigated): integer minor units for money · integer minutes for time · domain
dates (`*_on`, due dates) are **local calendar dates**, audit stamps
(`created_at`/`updated_at`) are **UTC** · **soft-delete, never hard-delete** ·
**archive** for long-lived roots · **derived and computed values are never stored**
(recomputed on read) · every write is exactly one `MutationEvent` through
`finalize_mutations()` · Memory is the only persistence owner · **no domain imports
another domain.** New for WorkOS and decided here: **`owner_id` scoping is reserved
on every aggregate from day one** ([§1.12](#112-owner-scoping--multi-tenant-reservation)),
and **`Product`/`Release` sit above `Project` as optional parents**
([§2.1](#21-context-a--work-the-delivery-graph)).

---

## 1. Data Philosophy

### 1.1 Source of truth
The **local SQLite database is the single system of record** for all WorkOS data
([ADR 0001](adr/0001-local-first-architecture.md),
[0012](adr/0012-sqlite-as-system-of-record.md)). Every aggregate's authoritative
state is its own live rows under `memory/work/`. External systems (GitHub, a
calendar, an email inbox) are **enrichers that feed captures**, never the truth —
a WorkItem imported from GitHub is a WorkOS WorkItem the moment it lands, and its
GitHub origin is provenance, not authority. If the network is gone, WorkOS is
whole.

### 1.2 Aggregate ownership
An **aggregate root is the unit of consistency for a single write.** One REST call
or chat command mutates exactly **one** aggregate. Nothing outside an aggregate
holds a reference to its internal child entities except through the root; children
are created, edited, and soft-deleted only via their root. Cross-aggregate effects
never happen inside one write except through the small set of **sanctioned
orchestrations** ([§6](#6-data-consistency-rules)), each performed in one DB
transaction inside `domains/work` and emitting one composite event — exactly the
Finance transfer-pair precedent.

### 1.3 Projection ownership
**Projections own no storage and emit no events.** A projection is a pure read
computed on demand from live aggregate rows (the `services/api/projections/home.py`
pattern). Dashboards, the priority queue, roadmaps, reviews, health, ROI — all are
projections. The two exceptions that *do* persist are **`Report`** (a generated
review is an artifact worth keeping) and **`PinnedRisk`** (a user elevating a
derived risk to a tracked one); both are small aggregates in the Insights context,
not projections.

### 1.4 Mutation ownership
**No state changes without a `MutationEvent`**
([ADR 0005](adr/0005-mutationevent-as-atomic-state-change.md)). The event is built
in the owning context's `mutations.py`, flows through the one
`finalize_mutations()` pipeline, and is consumed identically for every event:
desktop invalidation (WebSocket → `invalidation-map`), memory-producer policy, and
entity extraction. **AI proposals are not mutations** — a proposed plan, ranking,
sprint, or forecast is a transient value object and emits **nothing** until the
human commits it; only the committed decision is a write ([§1 philosophy of the
product spec: propose, never silently mutate]).

### 1.5 Soft-delete & archive strategy
Two distinct verbs, mirroring Finance (`transactions.deleted_at` vs
`accounts.archived_at`):

- **Soft-delete** (`deleted_at`, conceptual) — for user-editable, high-churn rows
  (WorkItem, TimeEntry, Note, ActionItem, KeyResult, Interaction, Dependency). A
  soft-deleted row is invisible to **every** list, projection, SUM/COUNT, and
  invariant check. It is never destroyed (the `memories` never-drop philosophy).
- **Archive** (`archived_at`, conceptual) — for long-lived roots that carry
  history and must remain referenceable (Product, Release, Project, Client,
  Engagement, Goal, Sprint). An archived root is hidden from pickers and active
  dashboards but stays in history, in past-as-of projections, and as a valid
  reference target for its existing children.
- **Hard delete never happens, anywhere.** The only delete verb exposed is soft.

Which roots archive vs delete is fixed per aggregate in [§2](#2-the-aggregates).

### 1.6 Time handling
- **Domain dates and instants are producer-supplied local values**; the backend
  never derives a local date from a UTC stamp in pure logic (the clock is injected
  — Handbook rule; the one Finance exception was a one-shot migration, which WorkOS
  has none of).
- **Durations and effort are integer minutes** (Estimate, TimeEntry, TimeBlock,
  capacity). No floats in time arithmetic — sums of logged time must be exact, the
  same reason Finance forbids REAL money.
- **Deadlines carry hardness** (`hard` = contractual/immovable vs `soft` =
  intended). A missed hard deadline is a risk event; a missed soft one is a
  re-plan signal. This distinction is a stored attribute of the deadline, not a
  computed guess.
- **"Now" is always injected**, so every derived date-relative field (overdue,
  days-to-due, staleness) is deterministic and testable.

### 1.7 Money handling
WorkOS holds money in exactly **one** place: revenue **expectation** on Engagements
and Projects, and rate models. All amounts are **integer minor units** with a
currency, reusing Nova's money value object — WorkOS **must not** invent a second
money type and **must not** import `domains.finance` to borrow one
([§10](#10-architecture-review) Open Question 1 resolves *where* the shared type
lives). **Realized money is never stored in WorkOS** — it lives in Finance and is
read at the facade ([§8](#8-cross-domain-references)). WorkOS therefore never
double-books: it owns the *promise* of revenue; Finance owns the *cash*.

### 1.8 Identity & IDs
- **Internal identity is a surrogate integer PK per aggregate/entity** (the
  Finance `INTEGER PRIMARY KEY AUTOINCREMENT` convention). IDs are opaque, stable,
  and never reused.
- **Cross-context and cross-domain links are by ID only**, never by embedded copy
  — a Sprint references WorkItem ids, an Engagement references a Project id, a
  RevenueExpectation references (exclusively) an Engagement id **or** a Project id.
- **External identity is a provenance value**, not a key: an imported item stores
  its source system + external id/URL as attributes for de-duplication and
  back-links, never as its primary identity.
- **Natural keys stay soft** (a project name is unique-while-live per owner, not a
  PK), so renames and archival-then-reuse are cheap — the Finance
  `UNIQUE(name) WHERE archived_at IS NULL` philosophy.

### 1.9 Versioning & optimistic concurrency
WorkOS is single-operator but multi-surface (desktop, chat, voice, scheduled AI
jobs) — two surfaces can touch the same item. The model therefore reserves an
**optimistic-concurrency token** conceptually (a monotonic `revision` or the
`updated_at` stamp) so a stale write is rejected as a conflict rather than
silently clobbering — the Finance rule "every UPDATE/soft-DELETE targets a live
row; editing a superseded row is a conflict, not a resurrect." **Row history is
not versioned** in v1 (no temporal tables); the audit trail is the `MutationEvent`
stream, which already records every change ([§10](#10-architecture-review) Risk 5).

### 1.10 Audit fields
Every aggregate and entity carries, conceptually: **created-at** and **updated-at**
UTC stamps (updated-at bumped on every write including soft-delete), a **source**
provenance enum (`manual | chat | voice | import | ai_committed`), and the
**owner scope** ([§1.12](#112-owner-scoping--multi-tenant-reservation)). `source`
records how a row entered (an AI-proposed-then-human-committed row is
`ai_committed`, distinguishing it from a hand-typed one for later trust analysis) —
it never drives behavior, exactly like Finance's `source`.

### 1.11 Derived fields vs computed fields (a deliberate distinction)
Both are **never stored**; both are recomputed on read. They differ by *what they
depend on*, and the distinction governs *where* they may be calculated:

- **Derived field** — a pure function of the aggregate's **own** live child rows or
  stored attributes. Calculable **inside the domain** with only that aggregate's
  data. Examples: Project completion % (from its milestones/items), Goal progress
  (from its key results), Engagement value reconciliation (from its deliverables),
  TimeEntry totals (from its own rows), Milestone reached/missed (from its target
  date + now).
- **Computed field** — requires **other aggregates, other contexts, cross-domain
  data (Finance/Calendar), or Brain reasoning.** Calculable only at the **Planning
  assembler, Insights layer, or the `services/api` facade** — never inside the
  owning aggregate. Examples: WorkItem priority score (needs goal weights + deps +
  deadlines + policy), Project health (needs velocity + capacity + blocked graph),
  ROI (needs Finance realized revenue), deadline risk (needs capacity + calendar),
  burnout signal (needs allocation + focus history).

This is why Insights owns no aggregates: everything it produces is a *computed*
field, and computed fields belong above the domain, not in it.

### 1.12 Owner scoping (multi-tenant reservation)
Every WorkOS aggregate reserves an **`owner_id`** (or `workspace_id`) scope from
the first design, defaulting to the single operator in v1. Nothing uses it yet;
reserving it now makes Teams / multi-user / company-mode ([§9](#9-future-extensibility))
an additive filter rather than a full-table rewrite once real data exists — the
single most expensive-to-retrofit decision, so it is paid down up front. **This
reservation is ADR-gated** ([§10](#10-architecture-review)).

---

## 2. The Aggregates

Grouped by the seven bounded contexts of the architecture doc. For each aggregate:
**Purpose · Responsibilities · Lifecycle · Invariants · Relationships · Child
entities · Derived fields · Computed fields · Archived/deleted behavior.** No
columns are defined (that is a later gate). Invariant IDs are stable handles for
the consistency rules in [§6](#6-data-consistency-rules).

### 2.1 Context A — Work (the delivery graph)

The Work context carries an **optional five-level parent chain** so a founder
building products and a freelancer doing one-off projects both fit:

```
Product   (optional top — a thing you build & maintain over years)
  └─ Release   (optional — a versioned shipment of a Product)
       └─ Project   (the core unit — may stand alone: freelance / personal / internal)
            └─ Milestone   (a dated checkpoint grouping items within a Project)
                 └─ WorkItem   (epic → story → task → subtask, one self-referencing tree)
                      └─ Dependency edges (WorkItem↔WorkItem or Project↔Project)
```

A `Project` may have **no** Product/Release (freelance/personal work) or belong to
a Release under a Product (product work). This optionality is the whole reason the
chain is modeled as nullable parent links, not a rigid containment.

---

#### `Product` (aggregate root) — *optional top of the Work hierarchy*
- **Purpose:** a durable thing the operator builds and shepherds over its whole
  life (an app, a SaaS, a brand). The unit a founder reasons about at the portfolio
  altitude.
- **Responsibilities:** hold the product's identity, vision, long-horizon
  lifecycle stage, and the roll-up of its releases/projects; anchor product-level
  health and revenue attribution.
- **Lifecycle:** `idea → planning → development → testing → released → growth →
  maintenance → archived` (the operator's own example, adopted as canonical —
  [§4](#4-state-machines)).
- **Invariants:** PR1 — a Product is never hard-deleted, only archived. PR2 — stage
  transitions are monotonic *except* the sanctioned back-edges (`growth ⇄
  maintenance`, and re-opening from `maintenance → development` for a major
  version). PR3 — archiving a Product requires all its Releases to be
  archived/closed ([§6](#6-data-consistency-rules)).
- **Relationships:** contains many `Release`; indirectly parents `Project` (through
  Release, or directly for product-level projects); may link to `Goal`s it serves;
  may carry `RevenueExpectation` at the product level.
- **Child entities:** none owned directly (Releases are their own roots referenced
  by id — a Product is a *thin* root over a large graph, so Releases are separate
  aggregates, not children, to keep the write unit small).
- **Derived fields:** completion roll-up across releases; active/latest release;
  count of open vs shipped releases.
- **Computed fields:** product health (needs velocity/risk across releases);
  product ROI (needs Finance realized revenue); expected vs realized revenue.
- **Archived behavior:** hidden from active portfolio; retained for history and
  past-revenue attribution; its releases/projects remain readable.

#### `Release` (aggregate root)
- **Purpose:** a versioned shipment of a Product ("v1.0", "Q3 launch") — the
  unit that has a scope, a target date, and either ships or slips.
- **Responsibilities:** group the projects/milestones that constitute a version;
  own the release's target/actual ship dates and scope commitment.
- **Lifecycle:** `planned → in_development → in_testing → shipped | cancelled`
  (a lighter echo of the Product lifecycle, scoped to one version).
- **Invariants:** RL1 — belongs to exactly one live Product. RL2 — target ship
  date ≥ release start. RL3 — a Release ships only when its committed Milestones
  are reached (or explicitly de-scoped) — enforced as a warn-and-confirm, not a
  hard block (the operator may ship with known gaps).
- **Relationships:** belongs to one `Product`; contains/《references》 many
  `Project`; groups `Milestone`s across those projects for the version.
- **Child entities:** none owned directly (Projects are separate roots).
- **Derived fields:** scope completion (% of committed milestones reached); slip =
  actual − target ship date.
- **Computed fields:** release health; release-level deadline risk (needs capacity).
- **Archived behavior:** archived when the Product archives or after ship + a
  retention window; stays as historical record of what shipped when.

#### `Project` (aggregate root) — *the core unit*
- **Purpose:** the central object of WorkOS — a bounded body of work with an
  objective, dates, health, and (optionally) an engagement and revenue. Everything
  hangs off it; it is what appears in the portfolio.
- **Responsibilities:** own its milestones and work items; enforce that its
  hierarchy is consistent; carry its objective, planned/actual date range,
  lifecycle, and links (to Release, Engagement, Goals).
- **Lifecycle:** `idea → planned → active → (paused ⇄ active) → completed |
  archived`. **`blocked` is not a stored state** — it is a *computed* condition
  (all active items blocked), keeping status honest (the Finance
  derived-status discipline).
- **Invariants:** P1 — never hard-deleted; archives. P2 — belongs to **0..1**
  Release (nullable). P3 — its Milestones' date windows lie within the project date
  range. P4 — completion % is a derived roll-up, never a typed field. P5 — a
  Project links to **0..1** Engagement (freelance/personal projects have none).
  P6 — a Project may be completed only when its Milestones are reached or explicitly
  dropped ([§6](#6-data-consistency-rules)).
- **Relationships:** belongs to 0..1 `Release`; contains `Milestone`s and
  `WorkItem`s; links to 0..1 `Engagement`; contributes to many `Goal`s; targeted by
  `TimeEntry`s and `RevenueExpectation`.
- **Child entities:** `Milestone` (a grouping/target within the project — see
  below); WorkItems are owned by the Project but are their own aggregate roots for
  write-granularity (a project with thousands of tasks cannot be one write unit).
- **Derived fields:** completion % (from milestones/items); item counts by status;
  next milestone; open-vs-done ratio; time invested (from linked TimeEntries within
  the project — this is *derived* because TimeEntry is in Execution but references
  the Project by id and the sum is a pure fold).
- **Computed fields:** health score; ROI (needs Finance); on-track/at-risk;
  velocity; deadline risk; priority contribution to its items.
- **Archived behavior:** hidden from active views/pickers; retained in history and
  past-ROI; its items/milestones become read-only history.

#### `Milestone` (child entity of `Project`)
- **Purpose:** a dated, meaningful checkpoint that groups work within a project
  ("auth complete", "beta") and anchors completion % and deadline tracking.
- **Responsibilities:** carry a target date and the set of items that fulfil it;
  signal reached/missed.
- **Lifecycle:** `pending → in_progress → reached | missed` (`missed` derived when
  the target date passes unreached, then user-confirmed).
- **Invariants:** M1 — belongs to exactly one live Project. M2 — target date within
  the project's date range (P3). M3 — a Milestone is `reached` only when its
  targeted WorkItems are `done` or explicitly de-scoped.
- **Relationships:** belongs to one `Project`; targeted by many `WorkItem`s
  (a WorkItem *optionally* points at a Milestone — the Milestone groups, the
  Project owns); may be committed to a `Release`.
- **Child entities:** none (it is a child itself).
- **Derived fields:** progress (from targeted items); reached/missed against date +
  now; slip.
- **Computed fields:** milestone deadline risk (needs velocity/capacity).
- **Archived behavior:** archives/soft-history with its Project; never independently
  archived while its Project is live.

#### `WorkItem` (aggregate root — unified epic/story/task/subtask)
- **Purpose:** the unit of execution. One tree of `type ∈ {epic, story, task,
  subtask}` via a self-referencing parent link — the Finance "unify by
  discriminator" move (bills/subscriptions/EMIs → `recurring_rules.kind`) applied to
  the issue hierarchy. Four levels, one lifecycle, one estimate/priority/dependency
  model.
- **Responsibilities:** carry its type, parent link, project, optional milestone,
  estimate (+confidence), status, and dependency edges; enforce a valid, acyclic
  parent chain; block/unblock from its dependencies.
- **Lifecycle:** `backlog → todo → in_progress → (blocked ⇄ in_progress) →
  in_review → done | cancelled`.
- **Invariants:** WI1 — belongs to exactly one live Project. WI2 — parent chain is
  **acyclic** and **type-valid** (`subtask ∈ task ∈ story ∈ epic ∈ project`); a
  type may not parent an equal-or-higher type. WI3 — `done` requires all
  `blocked_by` dependencies satisfied (or explicitly overridden with a recorded
  reason). WI4 — in **≤1 active Sprint**. WI5 — an optional Milestone must belong to
  the same Project. WI6 — estimate carries a Confidence (never a bare number).
- **Relationships:** self-referencing parent/children; belongs to `Project`;
  optionally targets a `Milestone`; has `Dependency` edges; logged by `TimeEntry`s;
  committed in a `Sprint`; may originate from an `ActionItem`.
- **Child entities:** a lightweight **checklist item** (a sub-sub bullet not worth
  a full WorkItem) may be modeled as a child of a task; anything larger is a
  `subtask` WorkItem.
- **Derived fields:** roll-up progress from children; total logged time (fold over
  its TimeEntries); is-leaf; age/staleness against now.
- **Computed fields:** **priority score** (the spine — needs goal weights, deps,
  deadlines, policy, decay); blocked-in-fact (from the dependency graph); estimate
  calibration (needs history).
- **Archived behavior:** soft-deleted (not archived) — items are high-churn;
  cancelled items stay for history; deleting a parent cascades a soft-delete to its
  subtree ([§6](#6-data-consistency-rules)).

#### `Dependency` (entity/edge)
- **Purpose:** a typed directed edge between two WorkItems or two Projects.
- **Responsibilities:** express `blocks` / `blocked_by` / `relates_to`; be the
  substrate for blocked-detection and critical-path.
- **Lifecycle:** `active → removed` (soft). No intermediate states.
- **Invariants:** D1 — both endpoints exist and are live. D2 — the `blocks`/
  `blocked_by` graph is **acyclic**; adding an edge that would create a cycle is
  rejected at write. D3 — endpoints are of the same tier (item↔item or
  project↔project), never mixed. D4 — no duplicate edge of the same type between
  the same ordered pair.
- **Relationships:** connects two `WorkItem`s or two `Project`s.
- **Derived fields:** none (it *is* a relationship).
- **Computed fields:** its contribution to critical path / blocking factor (graph
  traversal at the Planning layer).
- **Archived behavior:** soft-removed; history of past blockers is retained.

#### `SavedView` / `Board` (aggregate root — small)
- **Purpose:** a persisted filter+grouping over WorkItems (a kanban board, a saved
  query). The only stored artifact of the "Board" module; the board's *contents*
  are a projection.
- **Lifecycle:** `active → archived`.
- **Invariants:** SV1 — references only filters/fields that exist; a stale field
  degrades gracefully (ignored), never errors.
- **Derived/computed:** its result set is a projection ([§7](#7-projection-model)),
  never stored.

---

### 2.2 Context B — Planning

#### `Sprint` (aggregate root)
- **Purpose:** a time-boxed capacity window with a committed set of WorkItems.
  Optional — WorkOS runs with zero sprints.
- **Responsibilities:** hold its date range, capacity, and committed-item links;
  propose carry-forward on close.
- **Lifecycle:** `planned → active → completed`.
- **Invariants:** SP1 — date ranges of two *active* sprints (same owner) do not
  overlap. SP2 — a WorkItem is committed to ≤1 active sprint (WI4). SP3 — capacity
  is a fixed number set at planning; committed effort is recorded against it
  (over-commit is flagged, not blocked). SP4 — completing a sprint proposes moving
  incomplete items forward but never auto-moves without confirmation.
- **Relationships:** commits many `WorkItem`s (by id); reads `Capacity`
  (projection) and `PriorityQueue`.
- **Child entities:** commitment links (WorkItem id + committed estimate snapshot).
- **Derived fields:** committed vs capacity; completed vs committed (velocity input).
- **Computed fields:** proposed composition (Brain — a *proposal*, not stored until
  committed).
- **Archived behavior:** completed sprints archive; retained for velocity history.

#### `RoadmapPlan` (aggregate root)
- **Purpose:** a saved sequencing of Products/Releases/Projects/Milestones over
  time — the persisted intent behind the Roadmap projection.
- **Responsibilities:** hold planned windows and ordering; flag over-capacity.
- **Lifecycle:** `draft → active → superseded` (a new plan supersedes the prior;
  the old one archives for "what did we plan in Q1" history).
- **Invariants:** RP1 — references only live projects/milestones. RP2 — each entry
  has a planned window; overlaps that exceed capacity are flagged, not forbidden.
- **Derived fields:** total planned load per period.
- **Computed fields:** over-capacity windows (needs Capacity); feasibility (Brain).
- **Archived behavior:** superseded plans archive; never deleted (planning history
  is valuable for reviews).

#### `PriorityPolicy` (aggregate root — singleton-ish per owner)
- **Purpose:** the **only stored priority artifact** — the user's tunable weight
  vector (deadline × revenue × strategic × blocking × decay × effort). Priority
  *scores* are never stored; the *policy* that computes them is.
- **Responsibilities:** hold the weights and any pinned overrides.
- **Lifecycle:** `active` (versioned by update; changing weights is a
  `work.priority.reweighted` event).
- **Invariants:** PP1 — weights are non-negative and normalizable. PP2 — one active
  policy per owner.
- **Derived/computed:** the queue it drives is a projection.

---

### 2.3 Context C — Execution

#### `DayPlan` (aggregate root, contains `TimeBlock`)
- **Purpose:** the committed plan for a single date — an ordered set of time blocks,
  each pointing at a WorkItem or an external calendar event.
- **Responsibilities:** own the day's blocks; enforce non-overlap; sync committed
  blocks to Calendar via the injected handler.
- **Lifecycle:** `proposed → committed → in_progress → done`. A **`proposed`
  DayPlan has no side effects** and emits no event; only `committed` writes.
- **Invariants:** DP1 — blocks do not overlap in time. DP2 — total planned ≤
  capacity is a **soft** invariant (over-allocation surfaced, not blocked). DP3 — a
  block references a live WorkItem or an external calendar event id. DP4 — one
  committed DayPlan per date per owner.
- **Relationships:** schedules `WorkItem`s (by id); its blocks map to Calendar
  events (injected); reads `PriorityQueue` and `Capacity`.
- **Child entities:** `TimeBlock` (start + duration + target ref + optional
  calendar-event link).
- **Derived fields:** planned minutes; free minutes vs capacity; adherence
  (planned vs actual, once TimeEntries exist).
- **Computed fields:** the proposed plan itself (Brain).
- **Archived behavior:** past day plans archive; retained for adherence/energy
  analysis.

#### `TimeEntry` (aggregate root — leaf)
- **Purpose:** the record of time actually spent against a WorkItem/Project — the
  raw material for time-invested, ROI, velocity, and estimate calibration.
- **Responsibilities:** capture start/end (or duration) and the target; be exact
  and immutable once closed.
- **Lifecycle:** `open → closed`. `closed` is immutable (corrections are a new
  adjusting entry, the Finance adjustment-not-edit discipline).
- **Invariants:** TE1 — integer minutes, > 0 when closed. TE2 — references exactly
  one live WorkItem or Project. TE3 — closed entries are immutable; sums are exact.
  TE4 — no overlap with another open entry (one active timer per owner).
- **Relationships:** logs against `WorkItem` or `Project`; produced by a
  `FocusSession`.
- **Derived fields:** duration; day/period bucket.
- **Computed fields:** contribution to ROI (needs Finance) and velocity (needs
  planning).
- **Archived behavior:** soft-deleted only for genuine mis-logs; otherwise
  permanent (time is truth).

#### `FocusSession` (aggregate root)
- **Purpose:** a tracked work session (start/stop, interruptions) that produces a
  TimeEntry and a focus-quality signal.
- **Lifecycle:** `active → ended`. Ending produces exactly one TimeEntry.
- **Invariants:** FS1 — ≤1 active session per owner. FS2 — interruptions counted;
  ending emits one TimeEntry (TE1).
- **Derived fields:** FocusScore (from duration/interruptions — pure over its own
  data).
- **Computed fields:** contribution to burnout signal (needs allocation history).
- **Archived behavior:** archives with its date's history.

---

### 2.4 Context D — Engagements

#### `Client` (aggregate root, contains `Interaction`)
- **Purpose:** a person/company the operator does work for — a lightweight personal
  CRM record.
- **Responsibilities:** hold identity/context; own its interaction history; derive
  health and last-contact.
- **Lifecycle:** `prospect → active → dormant → archived`.
- **Invariants:** C1 — never hard-deleted; archives. C2 — client health/last-contact
  derive only from its own live interactions.
- **Relationships:** holds many `Engagement`s; has many `Interaction`s; contacts
  may attend `Meeting`s.
- **Child entities:** `Interaction` (a logged touchpoint — call/email/meeting
  summary).
- **Derived fields:** last-contact date; interaction count; simple health from
  recency/frequency.
- **Computed fields:** profitability per hour (needs engagements + Finance +
  TimeEntries); relationship risk (Brain).
- **Archived behavior:** archived clients hidden from active CRM; retained for
  revenue history and re-engagement.

#### `Engagement` (aggregate root, contains `Deliverable` and `RevenueExpectation`)
- **Purpose:** a commitment to a client — the freelance/consulting contract: scope,
  rate model, value, dates, linked project(s).
- **Responsibilities:** own its deliverables and revenue expectations; reconcile
  deliverable values to the engagement value; track its own lifecycle.
- **Lifecycle:** `prospect → proposed → active → (on_hold ⇄ active) → delivered →
  closed | lost`.
- **Invariants:** E1 — belongs to exactly one live Client. E2 — Σ deliverable
  values reconciles to the engagement value (warn on mismatch, not hard block —
  scope changes happen). E3 — its RevenueExpectation attaches to this engagement
  (or is re-attributed to a specific Project) — **exclusive**, never both. E4 — a
  rate model (`fixed | hourly | retainer`) is required to project revenue.
- **Relationships:** belongs to one `Client`; links to 0..N `Project`s; owns
  `Deliverable`s and `RevenueExpectation`.
- **Child entities:** `Deliverable` (a contracted output: `pending → submitted →
  accepted | revising`), fulfilled by a Milestone/WorkItem; `RevenueExpectation`
  (expected value for the engagement or a specific project).
- **Derived fields:** deliverable completion; value reconciliation; expected
  revenue.
- **Computed fields:** expected-vs-realized (needs Finance); ROI-per-hour (needs
  TimeEntries + Finance); forecast confidence (Brain).
- **Archived behavior:** closed/lost engagements archive; retained for revenue
  attribution and client history.

#### `RevenueExpectation` (child entity of `Engagement`; may re-attribute to `Project`)
- **Purpose:** the *promise* of revenue attributed to work. The WorkOS side of the
  Finance seam — expectation only, never cash.
- **Invariants:** RE1 — attaches to exactly one Engagement **or** one Project
  (exclusive). RE2 — amount is integer minor units + currency. RE3 — never records
  realized payment (that is a Finance transaction read at the facade).
- **Derived fields:** expected amount by period.
- **Computed fields:** realized-vs-expected and shortfall (needs Finance).
- **Archived behavior:** archives with its engagement.

---

### 2.5 Context E — Growth

#### `Goal` / `Objective` (aggregate root, contains `KeyResult`)
- **Purpose:** an OKR-style outcome that gives work its strategic weight; projects
  and habits contribute to it.
- **Responsibilities:** own its key results; roll up progress; expose a weight to
  prioritization.
- **Lifecycle:** `draft → active → (achieved | missed | abandoned)`.
- **Invariants:** G1 — progress is a defined function of its key results (never
  typed). G2 — contribution links point to live Projects/Habits. G3 — a Goal is
  `achieved` only when its key-result trajectory meets the bar (or the user
  explicitly marks it).
- **Relationships:** contains `KeyResult`s; contributed-to by `Project`s and
  `Habit`s (existing `memory/habits.py`); may belong to a `CareerRoadmap` or
  `LifeGoal`.
- **Child entities:** `KeyResult` (measurable target with current/target values +
  trajectory).
- **Derived fields:** goal progress (from key results); on-track vs behind against
  target date.
- **Computed fields:** strategic weight fed to the priority queue (Planning);
  quarter progress (Insights).
- **Archived behavior:** achieved/abandoned goals archive; retained for reviews and
  scorecards.

#### `LearningPath` (aggregate root, contains `LearningItem`)
- **Purpose:** a skill/course roadmap serving a goal or career step.
- **Lifecycle:** `planned → in_progress → completed | abandoned`.
- **Invariants:** L1 — path progress rolls up from its items. L2 — each item may
  serve a `Goal`/`CareerRoadmap` by id.
- **Child entities:** `LearningItem` (`todo → learning → done`), with progress.
- **Derived fields:** path progress; next item.
- **Computed fields:** recommended next skills + schedule fit (Brain + Capacity).
- **Archived behavior:** completed paths archive.

#### `LifeGoal` (aggregate root)
- **Purpose:** long-horizon personal outcomes (health, relationships, finance
  targets) that compete for the same hours as work — the reason WorkOS is *one*
  priority queue across all of life.
- **Lifecycle:** `active → (achieved | ongoing | abandoned)` (many life goals are
  perpetual — `ongoing` is a valid terminal-ish state).
- **Invariants:** LG1 — may link to Goals/Habits it decomposes into.
- **Derived/computed:** progress from linked goals/habits; scorecard contribution.
- **Archived behavior:** archives when explicitly closed.

---

### 2.6 Context F — Workspace

#### `Meeting` (aggregate root, contains `ActionItem`)
- **Purpose:** a scheduled or logged meeting — attendees, agenda, notes, and the
  action items it produces.
- **Lifecycle:** `scheduled → held → summarized` (or `cancelled`).
- **Invariants:** MT1 — action-item → WorkItem promotion is **idempotent**
  (re-processing the same meeting never duplicates items). MT2 — attendees
  reference `Client` contacts by id where known, else free text.
- **Relationships:** attendees ↔ `Client` contacts; notes ↔ `DocumentRef` /
  Knowledge Graph; produces `ActionItem`s → `WorkItem`s.
- **Child entities:** `ActionItem` (`open → promoted | dismissed`).
- **Derived fields:** open vs promoted action items.
- **Computed fields:** extracted action items + summary (Brain, from notes embedded
  via Knowledge).
- **Archived behavior:** meetings archive after summarization; retained as context.

#### `Note` / `Capture` (aggregate root)
- **Purpose:** fast unstructured capture (voice/chat/manual) that Nova later triages
  into WorkItems or filed notes — the "reduce data-entry" capture surface.
- **Lifecycle:** `captured → triaged | archived`.
- **Invariants:** N1 — an untriaged capture is visible in the capture inbox until
  resolved. N2 — triage produces links (to a WorkItem/Note), never silent deletion.
- **Derived/computed:** suggested triage target (Brain).
- **Archived behavior:** triaged captures archive with a link to their outcome.

#### `DocumentRef` (aggregate root)
- **Purpose:** a **pointer + relations** to a document that lives in the Knowledge
  Graph / Memory semantic store — WorkOS stores the link and its relationships to
  work items, never the body.
- **Invariants:** DR1 — stores no document body/embedding (Knowledge owns those);
  only the reference + relations. DR2 — a dangling reference degrades gracefully.
- **Derived/computed:** semantic relevance to a project/item (Knowledge, at the
  facade).
- **Archived behavior:** soft-removed; the underlying Knowledge doc is untouched.

---

### 2.7 Context G — Insights (only two stored aggregates)

#### `Report` (aggregate root)
- **Purpose:** a **generated** review artifact worth keeping (weekly/monthly/
  quarter review, a generated briefing snapshot).
- **Lifecycle:** `generated → (superseded)` — reports are immutable snapshots; a new
  one supersedes, the old is retained.
- **Invariants:** RPT1 — immutable after generation (it is a point-in-time truth).
  RPT2 — records the inputs/date range it covered (reproducibility).
- **Derived/computed:** its *content* is computed at generation; once stored it is a
  frozen artifact, not recomputed.
- **Archived behavior:** never deleted; the review history is a durable record.

#### `PinnedRisk` (aggregate root — small)
- **Purpose:** a risk the user elevates from the derived Risk Register to a tracked
  item (with a note/owner-intent), so it persists across recomputation.
- **Lifecycle:** `pinned → cleared`.
- **Invariants:** PK1 — references the derived risk's subject (project/item/deadline)
  by id; if the subject resolves, the pin surfaces as resolvable, never auto-cleared.
- **Everything else in Insights is a projection** ([§7](#7-projection-model)) — no
  storage.

---

## 3. Relationships (in prose)

The Work hierarchy, top to bottom, in the operator's own idiom:

> A **Product** contains **Releases**.
> A **Release** contains **Projects**.
> A **Project** contains **Milestones**.
> A **Milestone** groups **Work Items** (epic → story → task → subtask).
> A **Work Item** depends on other Work Items through **Dependency** edges.

— with the crucial refinement that **Product and Release are optional**: a
freelance or personal **Project** has neither, standing directly at the top of its
own little tree. Containment expresses *ownership of the write and archive
lifecycle*; a child archives when its parent archives and cannot outlive it as a
live row.

Across the other contexts, the links are **by id, never by containment**:

- An **Engagement** belongs to a **Client** and links to one or more **Projects**;
  its **RevenueExpectation** attaches to that engagement *or* to a specific project
  (exclusive), and is *realized* — read-only — by **Finance transactions** at the
  facade.
- A **Sprint** commits **Work Items** (by id) for a date window; a **RoadmapPlan**
  sequences **Projects/Milestones** over time; both *read* items, neither *owns*
  them.
- A **DayPlan** schedules **Work Items** into **Time Blocks**, which map to
  **Calendar** events (injected); a **Time Entry** logs actual minutes against a
  **Work Item** or **Project**; a **Focus Session** produces a **Time Entry**.
- A **Goal** is *contributed to* by **Projects** and **Habits** and gives them
  strategic weight; a **Learning Path** serves a **Goal** or **Career Roadmap**; a
  **Life Goal** decomposes into **Goals** and **Habits**.
- A **Meeting** produces **Action Items** that become **Work Items**; a **Note** is
  triaged into a **Work Item** or a filed note; a **Document Ref** points into the
  **Knowledge Graph**.
- **Insights** (dashboards, reviews, health, ROI, risk, briefings) *reference and
  read* everything above and *own* nothing but generated **Reports** and
  **Pinned Risks**.

**Relationship inventory (every cross-aggregate edge, explicit):**

| From | To | Cardinality | Nature | Notes |
|---|---|---|---|---|
| Release | Product | N : 1 | containment | RL1; nullable-up is not allowed — a Release always has a Product. |
| Project | Release | N : 0..1 | containment (optional) | P2; null = standalone project. |
| Milestone | Project | N : 1 | containment | M1. |
| WorkItem | Project | N : 1 | containment | WI1; the hard owner. |
| WorkItem | Milestone | N : 0..1 | grouping/target | WI5; same project (M-scope). |
| WorkItem | WorkItem | tree | self-parent | WI2; acyclic, type-valid. |
| Dependency | WorkItem/Project (×2) | edge | typed relation | D1–D4; acyclic for blocks. |
| Sprint | WorkItem | N : M | commitment (by id) | WI4/SP2; ≤1 active sprint per item. |
| RoadmapPlan | Project/Milestone | N : M | sequencing (by id) | reads, never owns. |
| DayPlan/TimeBlock | WorkItem | N : 0..1 | scheduling | DP3. |
| TimeBlock | Calendar event | N : 0..1 | injected link | cross-domain (§8). |
| TimeEntry | WorkItem/Project | N : 1 | logging | TE2. |
| FocusSession | TimeEntry | 1 : 1 | production | FS2. |
| Engagement | Client | N : 1 | containment-by-ref | E1. |
| Engagement | Project | N : M | attribution (by id) | links work to a contract. |
| RevenueExpectation | Engagement XOR Project | N : 1 | exclusive attribution | RE1. |
| RevenueExpectation | Finance transaction | read-only | realization (facade) | never a stored link (§8). |
| Goal | Project/Habit | N : M | contribution | G2. |
| KeyResult | Goal | N : 1 | containment | child of Goal. |
| LearningItem | LearningPath | N : 1 | containment | L1. |
| LearningPath/Goal | CareerRoadmap/LifeGoal | N : 0..1 | strategic linkage | by id. |
| Meeting/ActionItem | WorkItem | produces | idempotent promotion | MT1. |
| Note | WorkItem/Note | triage | link, not delete | N2. |
| DocumentRef | Knowledge doc | reference | pointer only | DR1 (§8). |
| PinnedRisk | Project/Item/Deadline | reference | subject of a risk | PK1. |

---

## 4. State Machines

Every root has one explicit lifecycle; transitions are the only workflow drivers
and the natural `operation` verbs on MutationEvents.

**Product** (the operator's canonical example):
```
idea → planning → development → testing → released → growth ⇄ maintenance → archived
                                                  ↘ (major version) ↗
                                          maintenance → development  (re-open)
```

**Release:** `planned → in_development → in_testing → shipped | cancelled`

**Project:** `idea → planned → active → (paused ⇄ active) → completed | archived`
(*`blocked` is computed, never a stored node*)

**Milestone:** `pending → in_progress → reached | missed`
(*`missed` derived on target-date passing, then confirmed*)

**WorkItem:** `backlog → todo → in_progress → (blocked ⇄ in_progress) → in_review → done | cancelled`

**Dependency:** `active → removed`

**Sprint:** `planned → active → completed` (*carry-forward proposed on completion*)

**RoadmapPlan:** `draft → active → superseded`

**DayPlan:** `proposed → committed → in_progress → done` (*proposed = no side effects*)

**TimeEntry:** `open → closed` (*closed = immutable*)

**FocusSession:** `active → ended`

**Client:** `prospect → active → dormant → archived`

**Engagement:** `prospect → proposed → active → (on_hold ⇄ active) → delivered → closed | lost`

**Deliverable:** `pending → submitted → accepted | revising`

**Goal:** `draft → active → (achieved | missed | abandoned)`

**LearningPath:** `planned → in_progress → completed | abandoned`;
**LearningItem:** `todo → learning → done`

**LifeGoal:** `active → (achieved | ongoing | abandoned)`

**Meeting:** `scheduled → held → summarized | cancelled`;
**ActionItem:** `open → promoted | dismissed`

**Note:** `captured → triaged | archived`

**Report:** `generated → superseded` (immutable snapshots)

**PinnedRisk:** `pinned → cleared`

**Priority is not a lifecycle** — it is a continuously recomputed *computed field*,
never a stored status; storing it would rot it (the Finance derived-status rule).

---

## 5. Ownership Rules

Who may **own** (write the aggregate + its children), **modify** (transition/edit),
**reference** (link by id, read-only), and **project** (read into a computed view).
The governing rule: **exactly one context owns each aggregate; every other context
may only reference or project it.**

| Aggregate | Owned by | May modify | May only reference | May project |
|---|---|---|---|---|
| Product, Release | Work | Work | Engagements, Growth, Insights | Insights |
| Project | Work | Work | Planning, Execution, Engagements, Growth | Planning, Insights |
| Milestone | Work (via Project) | Work | Planning, Engagements | Insights |
| WorkItem, Dependency | Work | Work | Planning, Execution, Workspace | Planning, Insights |
| SavedView/Board | Work | Work | — | Work (its result set) |
| Sprint, RoadmapPlan, PriorityPolicy | Planning | Planning | Execution, Insights | Insights |
| DayPlan, TimeBlock | Execution | Execution | Insights | Insights |
| TimeEntry, FocusSession | Execution | Execution | Engagements (ROI), Insights | Insights |
| Client, Interaction | Engagements | Engagements | Workspace (meeting attendees) | Insights |
| Engagement, Deliverable | Engagements | Engagements | Work (project link), Insights | Insights |
| RevenueExpectation | Engagements | Engagements | Insights | Insights (+ Finance read) |
| Goal, KeyResult | Growth | Growth | Planning (weight), Work (contribution) | Planning, Insights |
| LearningPath/Item, LifeGoal, CareerRoadmap | Growth | Growth | Insights | Insights |
| Meeting, ActionItem, Note, DocumentRef | Workspace | Workspace | Work (promoted items) | Insights |
| Report, PinnedRisk | Insights | Insights | — | — |

**Cross-cutting ownership laws:**
1. **A context never writes another context's aggregate.** Planning cannot flip a
   WorkItem's status; it computes a priority *over* it. Promotion of an ActionItem
   into a WorkItem is a **sanctioned orchestration** ([§6](#6-data-consistency-rules))
   that Workspace initiates but which creates the WorkItem *through the Work
   context's writer* — one write unit, one event.
2. **Insights owns no primitive** and may only read — every dashboard is a computed
   field, and computed fields live above the domain
   ([§1.11](#111-derived-fields-vs-computed-fields-a-deliberate-distinction)).
3. **Finance, Calendar, Knowledge, Memory, Habits are referenced/projected, never
   owned** by WorkOS ([§8](#8-cross-domain-references)).

---

## 6. Data Consistency Rules

The exact behavior of every destructive, completing, or cross-aggregate action.
All checks read only **live** rows. Multi-aggregate actions are **sanctioned
orchestrations** performed in one DB transaction inside `domains/work`, emitting one
(possibly composite) event — the Finance transfer-pair discipline.

**Deleting / archiving a Product**
- A Product is never hard-deleted. **Archive** requires all its Releases to be
  archived/shipped/cancelled (PR3). Archiving a Product does **not** cascade a
  delete to its projects' data — they become read-only history under an archived
  parent.

**Deleting / archiving a Release**
- Archive requires its committed Milestones to be reached or explicitly de-scoped
  (RL3, warn-and-confirm). Projects under a cancelled Release are **detached to
  standalone** (their `Release` link nulls), never deleted — losing a version plan
  must not lose the work.

**Deleting / archiving a Project**
- Never hard-deleted; archives (P1). Archiving requires no *blocking open
  obligations*: no active Sprint solely committed to its items, no open Deliverable
  depending on it (warn-and-confirm — the operator may archive a dropped project).
  Its Milestones and WorkItems become read-only history; linked TimeEntries and
  RevenueExpectations are retained for ROI/revenue history.

**Deleting a WorkItem (soft)**
- Soft-deleting a parent **cascades a soft-delete to its entire subtree** (subtasks
  under a task, etc.) in one transaction — orphaned children are never left live.
- Its Dependency edges are soft-removed with it. Its TimeEntries are **retained**
  (time spent is truth; they detach to the Project). A WorkItem committed to an
  active Sprint is removed from the commitment on delete.

**Moving / reparenting a Task**
- Reparenting revalidates the type-ladder (WI2) and re-checks the dependency graph
  for cycles (D2); a move that would create a cycle or an invalid type nesting is
  rejected. Moving an item across Projects re-homes its Milestone link (must clear
  or point to a milestone in the new project, WI5) and re-attributes its
  TimeEntries' project.

**Completing a Milestone**
- Allowed only when its targeted WorkItems are `done` or explicitly de-scoped (M3);
  otherwise warn-and-confirm. Completing a Milestone recomputes (never stores) the
  Project's completion %.

**Completing a Project**
- Allowed when Milestones are reached or dropped (P6). Completion is a lifecycle
  transition, not a cascade — child items keep their own terminal states; cancelled
  items remain cancelled in history.

**Dependencies**
- Adding a `blocks`/`blocked_by` edge is rejected if it creates a cycle (D2). An
  item cannot transition to `done` with unsatisfied `blocked_by` edges (WI3) unless
  the user records an explicit override reason (kept in history). Removing the last
  blocker recomputes (never stores) the item's blocked-in-fact status.

**Sprint closure**
- Completing a Sprint computes its incomplete set and **proposes** carry-forward to
  the next sprint/backlog; nothing moves without confirmation (SP4). Completed
  commitments feed velocity (a computed field), which is never written back onto
  the items.

**Revenue expectations**
- A RevenueExpectation attaches to an Engagement **or** a Project, never both (RE1).
  It records only the *promise*; **realization is a read** against Finance
  transactions at the facade (§8) — WorkOS never writes a "paid" flag, so there is
  no reconciliation drift with the ledger. Re-attributing an expectation (engagement
  → specific project) is a single update event; the amount is preserved.

**Goal completion**
- A Goal is `achieved` only when its key-result trajectory meets the bar or the user
  explicitly marks it (G3). Achieving/abandoning a Goal recomputes the strategic
  weight it lends to prioritization — items lose that weight immediately on the next
  queue read (because priority is computed, not stored). Contribution links from
  archived projects are ignored in the roll-up.

**Action-item promotion**
- Promoting an ActionItem creates a WorkItem through the Work writer and marks the
  ActionItem `promoted` with a link — **idempotent** (MT1): re-running the
  extraction on the same meeting never creates a duplicate WorkItem.

**Note triage**
- Triaging a capture produces a link to its outcome and marks it `triaged`; it is
  never silently deleted (N2).

**Universal rules** (every write):
- Every UPDATE/soft-DELETE targets a **live** row; touching a superseded row is a
  **conflict**, not a resurrect ([§1.9](#19-versioning--optimistic-concurrency)).
- Every write bumps `updated_at` and emits exactly one `MutationEvent`.
- Soft-delete/archive is the only removal verb exposed anywhere; nothing is ever
  hard-deleted.
- A derived or computed value is **never** written as the side effect of another
  write — it is recomputed on read (no stored completion %, priority, health, ROI,
  balance-style fields).

---

## 7. Projection Model (read models)

Every projection is a pure read over live aggregates, computed on demand, owning no
storage and emitting no events (the `projections/home.py` pattern). **Cross-domain
projections are assembled at the `services/api` facade** — never inside a domain
(§8). Listed with their inputs; field-level shapes are a later gate.

| Projection | Kind | Inputs (live rows) |
|---|---|---|
| **Portfolio** | in-domain | Products + Releases + Projects roll-up. |
| **Priority Queue** | Planning (the spine) | WorkItems + Dependencies + deadlines + Goal weights + PriorityPolicy + decay. |
| **Today / Today's Focus** | facade | committed DayPlan + Priority Queue + Calendar (injected) + Capacity. |
| **Roadmap** | Planning | Products/Releases/Projects/Milestones + planned windows + capacity flags. |
| **Backlog / Board** | Work/Planning | WorkItems (filtered by SavedView) ordered by priority. |
| **Capacity** | Execution | Calendar busy-blocks (injected) + Habits + Meetings. |
| **Velocity** | Execution/Planning | completed Sprint commitments + TimeEntries over time. |
| **Dashboard** | facade | Project health + ROI + revenue (Work × Finance) + time allocation + risks. |
| **CEO / Founder Dashboard** | facade | Portfolio health + expected-vs-realized revenue + hour allocation + at-risk projects. |
| **Project / Product Health** | Insights | schedule variance + velocity + blocked graph + staleness + burn. |
| **Deadline Risk** | Insights | deadlines (hard/soft) + velocity + capacity collisions. |
| **Risk Register** | Insights | derived risks + PinnedRisks. |
| **ROI View / Burn Rate** | facade | RevenueExpectation + TimeEntries + Finance realized revenue. |
| **Revenue Forecast** | facade | RevenueExpectation + trajectory + Finance realized (+ Confidence). |
| **Freelancing Summary** | Engagements | Engagements + Deliverables + expected/realized per Client. |
| **Learning Progress** | Growth | LearningPaths/Items progress + Goal linkage. |
| **Quarter Progress** | Growth/Insights | Goals + KeyResult trajectories + Milestone hits. |
| **Personal Scorecard** | Growth/Insights | Goals + Habits + LifeGoals adherence. |
| **Weekly / Monthly Review** | Insights (Brain) | completed-vs-planned + slippage + allocation + habits + goal movement → narrated, then stored as a `Report`. |
| **Briefing** | Insights (Brain) | Priority Queue + deadlines + Calendar + risks + revenue → narrated. |

The three projection *kinds*: **in-domain** (Work/Planning/Execution/Engagements/
Growth data only — computable inside `domains/work`), **facade** (needs Finance or
Calendar — assembled in `services/api/projections/`), and **Brain** (needs
reasoning/narration — assembled by an Insights assembler feeding a Brain job).

---

## 8. Cross-Domain References (ADR-0011 compliant)

WorkOS reads four things it does not own. Each obeys **a domain never imports
another domain or a service** — the connection is made **above** the domain (at the
facade, the composition root, or Brain), or **through Memory**. WorkOS stores
**only ids and provenance** of foreign data, never a copy of it.

| WorkOS needs | From | Allowed mechanism | Forbidden |
|---|---|---|---|
| **Realized revenue** (ROI, revenue-vs-plan, forecast) | **Finance** | Assembled in **`services/api/projections/`**, which may read both domains (the `home.py` precedent), or fused by **Brain** from Memory. WorkOS stores only its own RevenueExpectation ids; the *match* to Finance transactions happens at the facade. | `domains.work` importing `domains.finance`; storing a Finance transaction id inside a WorkOS row as an owned FK. |
| **Busy-blocks + write time-blocks** | **Calendar** | An **injected handler** passed by the composition root (ADR 0007) — the exact pattern Finance uses to reach Calendar (ADR 0017). A TimeBlock stores the external calendar-event id as **provenance**, resolved through the injected port. | `domains.work` importing `services.calendar`. |
| **Document bodies + semantic search** | **Knowledge Graph** | WorkOS stores `DocumentRef` (pointer + relations) in `memory/work`; `services.knowledge` (which owns embeddings) indexes note/meeting text by **reading Memory**, orchestrated at the composition root; search results reach WorkOS at the facade. | `domains.work` importing `services.knowledge`; storing embeddings in `memory/work`. |
| **Habit adherence** | existing **`memory/habits.py`** | Read through **Memory's public API**; Goals/Scorecard reference habit ids. WorkOS does **not** re-own habit storage. | duplicating a habits table under `memory/work`. |
| **All own persistence + semantic similars** | **Memory** | Direct `memory.work.*` and read-only semantic queries Memory exposes — the one always-allowed downward edge. | opening sqlite/lancedb directly (ADR 0004/0012/0013). |

**The invariant:** if WorkOS and another domain's data must meet, they meet at
`services/api` or in Brain — **never** by one domain reaching into the other. The
only foreign identifiers a WorkOS row stores are **provenance values** (a calendar
event id, a knowledge doc id, an external GitHub url) — read-through references,
never owned foreign keys with cascade semantics.

---

## 9. Future Extensibility

Each future module is a **reserved socket in this model** — building it is
additive, never a reshape — provided the reservations in
[§1.12](#112-owner-scoping--multi-tenant-reservation) and the provenance/id
discipline of [§8](#8-cross-domain-references) hold.

| Future module | Reserved socket in this model | When built, adds |
|---|---|---|
| **CRM depth** | Client + Interaction already model relationships and health | a `crm/` subcontext: pipelines, deal stages, contact roles — new aggregates under the same domain, no reshape. |
| **Hiring** | the aggregate-per-write-unit pattern + owner scoping | Candidate/Role/Interview aggregates in an `engagements/hiring/` or new Growth subcontext; ActionItem/Meeting already cover interview capture. |
| **Teams / multi-user / company mode** | **`owner_id`/`workspace_id` reserved on every aggregate** (§1.12) | membership + role aggregates; every existing query gains an owner filter it was already shaped for — the single retrofit this model deliberately pre-pays. |
| **GitHub / Jira / Linear import** | **provenance values** (source system + external id/url) on WorkItems (§1.8) + the single write path | an `ImportSource` adapter feeding items through the **existing** `work_commands` → `MutationEvent` pipeline; imports are just another `CaptureSource`, de-duplicated by provenance id. Read-only enrichment first; write-back is trust-gated. |
| **Email / Slack capture** | Note/Capture with `CaptureSource` enum (§2.6) | new enum values (`email`, `slack`) + injected readers; captures triage into WorkItems through the existing path. |
| **External write-back** (create a GitHub issue from a WorkItem) | provenance links + the future `agents` layer | a trust-gated outbound port invoked by `agents` (Architecture v2); the domain stays local-first and never depends on the external system. |
| **Attachments** | integer PKs + the `entity_type` vocabulary of the event canon | a polymorphic attachment reference (entity_type, entity_id, pointer) — the Finance reserved-extension recipe, reused verbatim. |
| **Cached projections** (if scale demands) | everything derived/computed by formula, never stored | a rebuildable cache maintained by the event stream — *derived, rebuildable, never source of truth* (the LanceDB precedent). |

**Guiding constraint:** every external system is an **optional enricher, never a
source of truth** (ADR 0001); the local store stays authoritative; integrations are
injected ports at the composition root.

---

## 10. Architecture Review

*Assumptions, tradeoffs, risks (ordered by cost-to-reverse once real data exists),
future ADRs, and open questions. Per Handbook §11.4 none of these are
self-approvable — this document drafts them and stops.*

### Assumptions
1. **Single operator in v1**, multi-tenant *reserved* (§1.12) — other people are
   modeled (Client contacts, meeting attendees), not authenticated.
2. **WorkOS is one domain with seven internal contexts** (the architecture-doc
   decision) — the Finance rewards/cashback/payments precedent.
3. **Local SQLite is the sole system of record**; Finance/Calendar/Knowledge are
   read-through, never owned (§8).
4. **Derived and computed values are never stored** — priority, health, ROI,
   completion %, velocity, balances-of-any-kind are recomputed on read.
5. **Product/Release are optional** parents; freelance/personal projects stand
   alone.
6. **The `MutationEvent` shape is sufficient** for every WorkOS write — new
   `entity_type`/`operation` values are additive, no dataclass change (to be
   confirmed at WOS-0).

### Tradeoffs
1. **Unified `WorkItem` tree vs rigid epic/story/task tables** — chosen: unified
   (one lifecycle/estimate/priority/dependency model, reparentable). Cost: type-
   ladder validity (WI2) is a service invariant, not a schema guarantee.
2. **Optional Product/Release vs mandatory** — chosen: optional (fits freelancers).
   Cost: the "what owns this project" question has a nullable answer; portfolio
   roll-ups must handle standalone projects.
3. **Computed-not-stored everywhere vs cached fields** — chosen: computed (always
   fresh, always explainable). Cost: every read recomputes; mitigated by
   personal-scale data and a *rebuildable cache* escape hatch (§9), never a
   written-back column.
4. **Expectation-only money vs mirroring Finance** — chosen: WorkOS holds
   expectation, Finance holds cash, joined at the facade. Cost: ROI needs a
   cross-domain read every time; benefit: zero double-booking, zero reconciliation
   drift.
5. **Owner scoping reserved from day one vs added later** — chosen: reserve now.
   Cost: an unused scope column on every table in v1; benefit: multiplayer becomes
   a filter, not a rewrite.

### Risks (ordered by cost-to-reverse after production data exists)
1. **Owner scoping not reserved (highest).** Retrofitting a tenant key onto every
   table after real single-user data exists is a full-table migration touching
   every query. Mitigation: **reserve it at WOS-0** (§1.12) — the one thing that
   *must* be decided before the first row.
2. **`occurred`/date timezone semantics.** Domain dates must be producer-supplied
   local from the first write; any server-side UTC→local derivation in pure logic
   misbuckets days/periods irreversibly (the Finance Risk 2, inherited).
3. **Computed-field leakage into storage.** If any write ever persists a priority/
   health/completion value "for speed", it rots and diverges — the classic
   derived-model bug. Mitigation: structural — `memory/work` exposes only
   live-row queries; no writer accepts a computed field.
4. **Dependency-cycle integrity lives in the service, not the DB.** SQLite cannot
   declare acyclicity; a writer bypassing `domains/work` could create a cycle that
   breaks scheduling. Mitigation: single write path (already an architecture ban) +
   a cheap graph-integrity assertion in the test suite.
5. **No row-level history in v1.** The audit trail is the `MutationEvent` stream
   only; if per-field temporal history is ever required (e.g. "who changed this
   estimate"), it is additive but the pre-history rows won't have it. Accepted for
   v1; flagged so it isn't assumed present.
6. **Idempotent action-item promotion (MT1).** Getting the idempotency key wrong
   duplicates work items on every re-extraction. Mitigation: pin the promotion key
   (meeting id + action-item id) in tests before the Workspace gate.
7. **Cross-domain ROI coupling.** The facade join to Finance must tolerate Finance
   evolving; it reads Finance's public query API only, never its tables — a change
   in Finance internals must not break WorkOS. Lowest risk given the boundary, but
   named.

### Future ADRs required (before WOS-1 code)
1. **"WorkOS as the second domain"** — records the single-domain/seven-context
   decision; confirms `domains.work → {memory, runtime}` and full 0004/0005/0011
   compliance (mirrors ADR 0017).
2. **"WorkOS dependency edges"** — adds `domains.work`,
   `services.planner → domains.work`, `services.api → domains.work` to
   `ALLOWED_EDGES`; confirms **no** `work → finance` edge; records the
   facade-fusion pattern.
3. **"Shared money value object"** — where the reused minor-unit money type lives
   so both domains use it without one importing the other (Open Question 1).
4. **"Multi-tenant scoping reservation"** — reserves `owner_id` on all
   `memory/work` aggregates ahead of any multiplayer feature (§1.12).
5. **Confirmation (likely no ADR):** the new `entity_type`/`operation` values are
   additive to the mutation vocabulary and need **no** `MutationEvent` shape change
   — verified against `runtime/mutation_event.py` at WOS-0.

### Open questions (need a human answer at WOS-0)
1. **Shared `Money` location** — promote to a root utility both domains import, or
   give Engagements its own minor-unit `Money`? *(Recommend: promote — one money
   type Nova-wide.)*
2. **Is Product/Release in the v1 model or deferred?** Modeling them now costs two
   nullable parent links; deferring means projects can't roll up into products
   until later. *(Recommend: model the sockets now, build the Product/Release
   screens in a later gate — the data model should not need reshaping to add
   them.)*
3. **WorkItem type-ladder: fixed 4 levels or arbitrary nesting?** *(Recommend:
   fixed, validated ladder; revisit only on real need.)*
4. **ROI/revenue fusion: facade projection (deterministic numbers) vs Brain
   narration on top?** *(Recommend: facade for numbers, Brain for the narrative
   layer.)*
5. **Optimistic-concurrency token: `updated_at` compare vs an explicit `revision`
   counter?** *(Recommend: start with `updated_at`; add `revision` only if
   conflicts prove common across surfaces.)*

**This document ends here. It is the canonical WorkOS data model. No
implementation follows until the ADRs above are accepted by a human.**
