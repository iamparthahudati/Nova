# WorkOS — Database Structure

**Status:** Implementation architecture (high-level). Column-level DDL is a per-gate
artifact (Finance precedent: `FINANCE_DATA_MODEL.md` → FIN-1 code).  
**Authority:** ADRs 0021–0023, `NOVA_WORKOS_DATA_MODEL_v1.md`.  
**Rule:** Tables store **ledger rows, holdings, and facets only** — never derived
balances.

---

## Design principles

1. **One writer:** `memory/work/` is the only package that touches these tables.
2. **Aggregate = consistency boundary:** one mutation ≈ one aggregate root write
   (sanctioned orchestrations excepted — Finance transfer-pair precedent).
3. **Soft-delete / archive:** high-churn rows use `deleted_at`; long-lived roots
   use `archived_at`. No hard deletes.
4. **Owner scope:** every table reserves `owner_id` (nullable unused in v1 single
   operator — ADR-gated reservation).
5. **Integer truth:** money in minor units; time in minutes; no REAL columns for
   aggregates that feed ROI.
6. **Id-only cross-links:** aggregates reference each other by integer id — no
   embedded copies of foreign aggregates.

---

## Table inventory by ledger

### Holdings (position anchors — lifecycle aggregates)

| Table | Aggregate root | Owner context | Notes |
|---|---|---|---|
| `work_products` | Product | Work | Optional top of hierarchy |
| `work_releases` | Release | Work | Belongs to Product |
| `work_projects` | Project | Work | Core unit; optional Release parent |
| `work_clients` | Client | Engagements | CRM root |
| `work_goals` | Goal | Growth | OKR root |
| `work_life_goals` | LifeGoal | Growth | Long-horizon personal |

### Commitment ledger tables

| Table | Aggregate root | Owner context | Notes |
|---|---|---|---|
| `work_items` | WorkItem | Work | Unified epic/story/task/subtask tree |
| `work_milestones` | Milestone | Work | Child of Project (entity) |
| `work_dependencies` | Dependency | Work | Typed edges |
| `work_saved_views` | SavedView/Board | Work | Filter definition only |
| `work_sprints` | Sprint | Planning | |
| `work_sprint_commitments` | — | Planning | Sprint ↔ WorkItem link + estimate snapshot |
| `work_roadmap_plans` | RoadmapPlan | Planning | |
| `work_roadmap_entries` | — | Planning | Plan window rows |
| `work_priority_policies` | PriorityPolicy | Planning | Weight vector — not scores |
| `work_day_plans` | DayPlan | Execution | |
| `work_time_blocks` | TimeBlock | Execution | Child of DayPlan; commitment when plan committed |
| `work_engagements` | Engagement | Engagements | |
| `work_deliverables` | Deliverable | Engagements | |
| `work_revenue_expectations` | RevenueExpectation | Engagements | Expectation only |
| `work_interactions` | Interaction | Engagements | Client touchpoints |
| `work_action_items` | ActionItem | Workspace | Pre-promotion commitment |
| `work_meetings` | Meeting | Workspace | |
| `work_notes` | Note/Capture | Workspace | |
| `work_document_refs` | DocumentRef | Workspace | Pointer only — no body |
| `work_key_results` | KeyResult | Growth | Child of Goal |
| `work_learning_paths` | LearningPath | Growth | |
| `work_learning_items` | LearningItem | Growth | |
| `work_goal_contributions` | — | Growth | Goal ↔ Project/Habit link table |

### Time ledger tables

| Table | Aggregate root | Owner context | Notes |
|---|---|---|---|
| `work_time_entries` | TimeEntry | Execution | Immutable when closed |
| `work_focus_sessions` | FocusSession | Execution | Produces one TimeEntry on end |

### Insights artifacts (not ledger — small stored exceptions)

| Table | Aggregate root | Owner context | Notes |
|---|---|---|---|
| `work_reports` | Report | Insights | Immutable generated snapshots |
| `work_pinned_risks` | PinnedRisk | Insights | User-elevated derived risks |

### Optional rebuildable cache (not source of truth)

| Table | Purpose | Owner |
|---|---|---|
| `work_projection_cache` | Keyed derived JSON + invalidation cursor | memory/work (optional, WOS-8+) |

**Must not appear:** `priority_scores`, `health_scores`, `roi_values`, `allocation_pct`,
`completion_pct`, `velocity`, `portfolio_verdict`.

---

## Aggregate boundaries

Each boundary defines what one write transaction may touch.

| Aggregate root | Tables in boundary | Child entities |
|---|---|---|
| Product | `work_products` | — (Releases are separate roots) |
| Release | `work_releases` | — |
| Project | `work_projects` | Milestones owned via project scope |
| WorkItem | `work_items` | checklist items if modeled |
| Milestone | `work_milestones` | — |
| Dependency | `work_dependencies` | — |
| SavedView | `work_saved_views` | — |
| Sprint | `work_sprints`, `work_sprint_commitments` | commitment links |
| RoadmapPlan | `work_roadmap_plans`, `work_roadmap_entries` | entries |
| PriorityPolicy | `work_priority_policies` | — |
| DayPlan | `work_day_plans`, `work_time_blocks` | TimeBlocks |
| TimeEntry | `work_time_entries` | — |
| FocusSession | `work_focus_sessions` | — |
| Client | `work_clients`, `work_interactions` | Interactions |
| Engagement | `work_engagements`, `work_deliverables`, `work_revenue_expectations` | Deliverables, expectations |
| Goal | `work_goals`, `work_key_results`, `work_goal_contributions` | KRs, contribution links |
| LearningPath | `work_learning_paths`, `work_learning_items` | items |
| LifeGoal | `work_life_goals` | — |
| Meeting | `work_meetings`, `work_action_items` | ActionItems |
| Note | `work_notes` | — |
| DocumentRef | `work_document_refs` | — |
| Report | `work_reports` | — |
| PinnedRisk | `work_pinned_risks` | — |

### Sanctioned multi-aggregate orchestrations (one transaction, one composite event)

| Operation | Aggregates touched |
|---|---|
| ActionItem promotion | ActionItem + new WorkItem |
| FocusSession end | FocusSession + new TimeEntry |
| Transfer-style (future) | — none in v1 beyond above |

---

## Ownership matrix

| Table group | Written by | Read by |
|---|---|---|
| Work graph | `memory/work/projects.py`, `items.py`, … | All contexts via ports |
| Planning | `memory/work/sprints.py`, `roadmaps.py` | Planning, Insights |
| Execution | `memory/work/plans.py`, `time_entries.py`, `focus_sessions.py` | Execution, Insights, facade |
| Engagements | `memory/work/clients.py`, `engagements.py` | Engagements, facade |
| Growth | `memory/work/goals.py`, `learning.py` | Growth, Planning, Insights |
| Workspace | `memory/work/meetings.py`, `notes.py` | Workspace, Capture flow |
| Insights artifacts | `memory/work/reports.py` | Insights, API |
| Habits (external) | `memory/habits.py` | Growth, Insights — **not** duplicated under work |

---

## Architecturally important indexes

Indexes exist for query paths that projections hit on every read — not for derived
columns.

| Index | Table(s) | Purpose |
|---|---|---|
| Live row partial index | all soft-deleted tables | `WHERE deleted_at IS NULL` — every list/projection/sum uses live rows only |
| Owner scope | all tables | `(owner_id, …)` — future multi-tenant; v1 single operator |
| Project hierarchy | `work_items` | `(project_id, parent_id, deleted_at)` — tree fetches |
| WorkItem type + status | `work_items` | backlog/board filters |
| Sprint active | `work_sprints` | one active sprint per owner |
| TimeEntry target + date | `work_time_entries` | ROI and velocity folds |
| TimeEntry open timer | `work_time_entries` | partial unique: one open entry per owner |
| Dependency endpoints | `work_dependencies` | cycle check + blocking queries |
| Milestone due | `work_milestones` | deadline risk inputs |
| Deliverable due | `work_deliverables` | client risk |
| Engagement ↔ Project | link table or fk | freelancing summary |
| RevenueExpectation attribution | `work_revenue_expectations` | exclusive Engagement XOR Project |
| Note inbox | `work_notes` | untriaged captures |
| DocumentRef entity link | `work_document_refs` | reverse lookup from work item |
| Natural name uniqueness | `work_projects`, `work_products`, `work_clients` | `UNIQUE(name) WHERE archived_at IS NULL AND deleted_at IS NULL` per owner |

**Intentionally no index on priority or health** — those fields do not exist.

---

## Cross-domain reference storage

WorkOS stores **provenance ids only** for foreign systems:

| Stored on | Provenance field concept | Points to |
|---|---|---|
| `work_time_blocks` | external calendar event id | Calendar (injected) |
| `work_document_refs` | knowledge doc id | Knowledge Graph |
| `work_items` | import source + external id | GitHub/Jira (future) |

No WorkOS table stores Finance transaction ids as owned FKs — facade joins at read
time by attribution keys (Project/Engagement id).

---

## Migration strategy

1. **`memory/work/migrations.py`** — idempotent DDL blocks per gate (Finance pattern).
2. **Gate order matches IMPLEMENTATION_PLAN** — never add derived columns in
   migrations.
3. **`owner_id` on every CREATE from WOS-1** — default single operator.
4. **Schema version** tracked in Memory meta table — desktop/backend negotiate
   minimum version.
5. **Rollback** — forward-only migrations; rollback = restore SQLite backup (ADR 0012).

---

## Relationship to Finance schema

| Finance | WorkOS analogue |
|---|---|
| `accounts` | Holdings (Product, Client, Project-as-position) |
| `transactions` | TimeEntry |
| `recurring_rules` / expectations | Commitment ledger rows (WorkItem, Deliverable, RevenueExpectation) |
| derived balance | PriorityQueue, Health, ROI — **no table** |

WorkOS never writes to `finance_*` tables. Revenue realization is a read through
the Finance Adapter at the facade.
