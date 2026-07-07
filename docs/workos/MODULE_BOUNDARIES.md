# WorkOS — Module Boundaries

**Status:** Implementation architecture (canonical).  
**Authority:** Subordinate to ADRs 0021–0023 and `NOVA_WORKOS_ARCHITECTURE_v1.md`.  
**Purpose:** Define every module's responsibility, I/O, dependencies, and forbidden
knowledge so a team can implement without boundary drift over ten years.

WorkOS modules fall into three layers:

```
┌─────────────────────────────────────────────────────────────┐
│  FACADE ADAPTERS (services/api, composition root)           │
│  Finance Adapter · Calendar Adapter · Knowledge Adapter     │
└───────────────────────────┬─────────────────────────────────┘
                            │ reads only
┌───────────────────────────▼─────────────────────────────────┐
│  domains/work/  (single domain — seven internal contexts)   │
│  Capture · Delivery · Planning · Execution · Engagements ·  │
│  Growth · Decision Engine · Insights                          │
└───────────────────────────┬─────────────────────────────────┘
                            │ ports only
┌───────────────────────────▼─────────────────────────────────┐
│  memory/work/  (sole persistence)                           │
└─────────────────────────────────────────────────────────────┘
```

**Founder** is not a domain module — it is a **facade projection** assembling
Insights + Finance + Calendar outputs.

---

## Capture

**Package:** `domains/work/workspace/` + `memory/work/meetings.py`, `notes.py`  
**Context:** F — Workspace

| | |
|---|---|
| **Responsibility** | Frictionless intake of unstructured context; idempotent promotion into the Commitment ledger. |
| **Inputs** | Raw capture text/audio transcript, `CaptureSource`, optional Client/Project hints from Brain structuring, clock. |
| **Outputs** | `Note`/`Capture`, `Meeting`, `ActionItem`, `DocumentRef` aggregates; `work.note.*`, `work.meeting.*`, `work.actionitem.*` events; promotion orchestration → WorkItem creation. |
| **Dependencies** | `memory/work/*`, `runtime` (MutationEvent builders). Brain structuring is invoked **above** the domain. |
| **Must NEVER know** | Priority scores, health bands, Finance balances, Calendar internals, embedding indices, `domains/finance`, Anthropic API. |

---

## Delivery (Products & Work Graph)

**Package:** `domains/work/` (root Work context) + `memory/work/projects.py`, `items.py`, `milestones.py`, `dependencies.py`  
**Context:** A — Work

| | |
|---|---|
| **Responsibility** | Integrity of the delivery graph — Product/Release/Project/Milestone/WorkItem/Dependency lifecycle, acyclic deps, type-valid hierarchy. |
| **Inputs** | Create/update commands, parent ids, facet attributes (deadline, estimate), clock. |
| **Outputs** | Work aggregates; `work.product.*`, `work.release.*`, `work.project.*`, `work.item.*`, `work.milestone.*`, `work.dependency.*` events; ports for other contexts to read. |
| **Dependencies** | `memory/work/*`, `runtime`. |
| **Must NEVER know** | How items are ranked, calendar busy blocks, realized revenue, Brain proposals, other domains. |

**Products** (`Product`, `Release`) live here — optional parents of `Project`.

---

## Planning

**Package:** `domains/work/planning/` + `memory/work/sprints.py`, `roadmaps.py`, priority policy storage  
**Context:** B — Planning

| | |
|---|---|
| **Responsibility** | Turn backlog into ordered intent — Sprint composition, Roadmap sequencing, **PriorityPolicy** storage, deterministic prioritization function. |
| **Inputs** | WorkItem/Dependency rows (via ports), Goal weights (via ports), PriorityPolicy, decay policy, clock. |
| **Outputs** | `Sprint`, `RoadmapPlan`, `PriorityPolicy` mutations; **PriorityQueue** projection (computed); `work.sprint.*`, `work.roadmap.*`, `work.priority.reweighted` events. |
| **Dependencies** | Work ports, Growth ports (goal weights), `memory/work/*`, `runtime`. |
| **Must NEVER know** | Finance, Calendar service imports, Brain API, TimeEntry writes (reads velocity via Execution ports only). |

---

## Execution

**Package:** `domains/work/execution/` + `memory/work/plans.py`, `time_entries.py`, `focus_sessions.py`  
**Context:** C — Execution

| | |
|---|---|
| **Responsibility** | Time ledger writes; committed day planning; capacity computation inputs. |
| **Inputs** | WorkItem ids, timer start/stop, DayPlan commit commands, **CalendarPort** (injected), Habit reads (Memory API), Meeting schedule reads, clock. |
| **Outputs** | `DayPlan`, `TimeBlock`, `TimeEntry`, `FocusSession`; `work.plan.*`, `work.timeentry.*`, `work.focus.*` events; Capacity/Velocity projections. |
| **Dependencies** | `memory/work/*`, `runtime`, injected CalendarPort interface (no `services.calendar` import). |
| **Must NEVER know** | Finance, priority formula internals, Brain, desktop UI, SQL outside Memory. |

---

## Engagements (Clients)

**Package:** `domains/work/engagements/` + `memory/work/clients.py`, `engagements.py`  
**Context:** D — Engagements

| | |
|---|---|
| **Responsibility** | Client/Engagement/Deliverable/RevenueExpectation — the **commitment side of value** (expectation only). |
| **Inputs** | Client/engagement CRUD, rate models (Money VO), deliverable state transitions, Project link ids, clock. |
| **Outputs** | Engagements aggregates; `work.client.*`, `work.engagement.*`, `work.deliverable.*`, `work.revenue.*` events; FreelancingSummary projection (in-domain portion). |
| **Dependencies** | `memory/work/*`, `runtime`, shared root `Money` utility. |
| **Must NEVER know** | Finance transaction tables, realized payment state storage, priority queue, Brain. |

---

## Growth

**Package:** `domains/work/growth/` + `memory/work/goals.py`, `learning.py`  
**Context:** E — Growth

| | |
|---|---|
| **Responsibility** | Strategic weight — Goals, KeyResults, LearningPaths, LifeGoals; contribution links to Projects. |
| **Inputs** | Goal/KR updates, learning progress, Project contribution links, Habit adherence reads (`memory/habits.py`). |
| **Outputs** | Growth aggregates; `work.goal.*`, `work.learning.*`, `work.lifegoal.*` events; GoalWeights projection. |
| **Dependencies** | `memory/work/*`, `memory/habits` (read-only public API), `runtime`. |
| **Must NEVER know** | Finance, Calendar, TimeEntry writes, Brain. |

---

## Decision Engine

**Package:** `domains/work/planning/prioritization.py` + `domains/work/insights/` assemblers (pure modules)  
**Not a storage owner.**

| | |
|---|---|
| **Responsibility** | Deterministic synthesis of founder decisions — priority scoring, health band inputs, risk rules, ROI input bundles. **No Claude calls.** |
| **Inputs** | Commitment ledger + Time ledger reads (via ports), PriorityPolicy, Goal weights, Finance read DTOs (passed in from facade — never imported), clock. |
| **Outputs** | Pure data structures: scored queue, health input bundles, risk candidates, allocation gaps — consumed by Insights and facade. |
| **Dependencies** | Ports from Work, Planning, Execution, Engagements, Growth; **no Memory direct access** (goes through domain services in production; pure functions accept DTOs in tests). |
| **Must NEVER know** | Anthropic API, SQLite, desktop, HTTP. |

Brain sits **above** this layer for narrative and proposal generation only.

---

## Insights

**Package:** `domains/work/insights/` + `memory/work/reports.py`  
**Context:** G — Insights

| | |
|---|---|
| **Responsibility** | Assemble read models — health, risk, reviews; persist only `Report` and `PinnedRisk`. |
| **Inputs** | All context projections, Decision Engine outputs, Brain narratives (when orchestrated above domain). |
| **Outputs** | ProjectHealth, RiskRegister, WeeklyReview inputs, Report artifacts; `work.review.generated`, `work.risk.pinned/cleared` events. |
| **Dependencies** | All WorkOS context ports (read-only), `memory/work/reports.py`, `runtime`. |
| **Must NEVER know** | Finance imports, Calendar imports, direct Brain client — receives Brain output from orchestrator. |

---

## Founder (Facade Projection)

**Package:** `services/api/projections/work_dashboard.py`, `work_founder.py`  
**Not in `domains/work/`.**

| | |
|---|---|
| **Responsibility** | Portfolio-level decision surface — verdict line, holding list with health/ROI/allocation, cross-domain fusion. |
| **Inputs** | Insights assemblers, Engagements summaries, Finance read handler, Time allocation projection, clock. |
| **Outputs** | FounderDashboard DTO for API/desktop; no domain mutations. |
| **Dependencies** | `domains/work` (read services), Finance query handler, `memory` (read). |
| **Must NEVER know** | Business logic duplicated from Insights (calls assemblers); never opens sqlite directly. |

---

## Finance Adapter

**Package:** `services/api/projections/` + Finance read handler wired at composition root  
**Not a WorkOS module.**

| | |
|---|---|
| **Responsibility** | Read realized revenue, outstanding payments, transaction summaries for ROI and client payment facets. |
| **Inputs** | Finance domain query API / Memory finance read functions, attribution keys from WorkOS (Project/Engagement ids). |
| **Outputs** | Read DTOs consumed by facade projections — never written into WorkOS rows. |
| **Dependencies** | `domains/finance` or `memory/finance` read API (facade may import finance; WorkOS domain may not). |
| **Must NEVER know** | WorkOS mutation builders, WorkItem lifecycle. |

---

## Calendar Adapter

**Package:** Injected `CalendarPort` at composition root; implemented by `services/calendar`  
**Not imported by `domains/work/`.**

| | |
|---|---|
| **Responsibility** | Busy-block reads for Capacity; optional write of committed TimeBlocks as calendar events. |
| **Inputs** | Date range, owner scope; TimeBlock commit payloads on write. |
| **Outputs** | Busy intervals; external event ids stored as **provenance** on TimeBlock — not owned FK. |
| **Dependencies** | `services/calendar` (implementation only at root). |
| **Must NEVER know** | WorkOS priority, Finance, Brain. |

---

## Knowledge Adapter

**Package:** `services/knowledge` + facade search endpoints  
**Orchestrated at API/composition root.**

| | |
|---|---|
| **Responsibility** | Embed meeting/note text; semantic search; resolve `DocumentRef` pointers. |
| **Inputs** | Memory reads of note/meeting bodies or captures; DocumentRef ids from WorkOS. |
| **Outputs** | Search hits, embedding jobs; no WorkOS row mutations except DocumentRef creation in Workspace. |
| **Dependencies** | `memory`, `services/knowledge`, `services/brain` (embedding jobs). |
| **Must NEVER know** | WorkOS domain internals beyond DocumentRef ids. |

---

## Integration modules (sanctioned edges)

| Module | Package | Role |
|---|---|---|
| **Planner integration** | `services/planner/work_commands.py`, `work_queries.py`, `work_serializers.py` | Chat/voice verbs → domain services |
| **API routers** | `services/api/routers/work/` | Thin HTTP → planner/domain |
| **Brain orchestration** | `services/api` or runtime jobs | Assemble inputs → Brain → surface proposal → commit via commands |
| **Desktop** | `apps/desktop/` Work section | React Query + invalidation-map; no business logic |

---

## Cross-module dependency law

```
Allowed:
  domains/work/* → memory, runtime
  services/planner → domains/work
  services/api → domains/work, domains/finance (facade only)
  composition root → injects CalendarPort into Execution services

Forbidden:
  domains/work → domains/finance
  domains/work → services.*
  domains/work → brain / anthropic
  Insights → write any primitive except Report/PinnedRisk
  Any module → sqlite3 / lancedb except memory/work
```

Violations are caught by `tests/architecture/test_dependencies.py` after WOS-0
edge registration.

---

## Module → ledger mapping

| Module | Commitment ledger | Time ledger | Derived only |
|---|---|---|---|
| Capture | ActionItem (pre-promotion) | — | triage suggestions |
| Delivery | WorkItem, Milestone scope | — | completion % |
| Planning | Sprint, Roadmap, PriorityPolicy | — | PriorityQueue |
| Execution | committed DayPlan/TimeBlock | TimeEntry, FocusSession | Capacity, Velocity |
| Engagements | Deliverable, RevenueExpectation | — | client health inputs |
| Growth | Goal/KR targets | — | GoalWeights |
| Decision Engine | — | — | scores, bands, gaps |
| Insights | — | — | health, risk, reviews |
| Founder (facade) | — | — | portfolio verdict, ROI |
