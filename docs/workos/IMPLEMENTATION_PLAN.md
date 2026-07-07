# WorkOS — Implementation Plan

**Status:** Implementation architecture (canonical build order).  
**Authority:** ADRs 0021–0023, `NOVA_WORKOS_ARCHITECTURE_v1.md` §15, Execution Model.  
**Rhythm:** Backend + events + parity tests first; desktop second; verify between gates
(Finance FIN-1…6 discipline).

Each phase ships an **independently valuable** increment. No phase depends on a later
phase for correctness of its ledger writes.

---

## Phase 0 — Infrastructure & governance

**Theme:** Green light. No feature code until complete.

| Deliverable | Package / artifact |
|---|---|
| Accept ADRs 0021–0023 | `docs/adr/` |
| Register dependency edges | `tests/architecture/test_dependencies.py` |
| Promote shared `Money` VO to root utility | `money.py` or extend root utils — both domains import, neither imports the other |
| Reserve `owner_id` on all WorkOS DDL | `memory/work/migrations.py` skeleton |
| `memory/work/` package scaffold | migrations, seed, `__init__.py` |
| `domains/work/` package scaffold | value_objects, errors, validation |
| Mutation vocabulary confirmation | verify `entity_type` additive against `runtime/mutation_event.py` |
| WorkOS governance doc in CI readme | `docs/workos/IMPLEMENTATION_GOVERNANCE.md` |

**Why now:** Every later gate assumes boundaries, money type, and owner scope are
settled. Retrofitting any of these after WOS-1 data exists is the highest-cost
mistake (see IMPLEMENTATION_RISKS).

**Becomes usable:** Nothing user-facing — the team can implement WOS-1 without
architecture meetings.

**Risks removed:** Package boundary violations, money type drift, multi-tenant
rewrite, MutationEvent shape surprises.

---

## Phase 1 — Capture + Commitment ledger spine + Morning Brief shell

**Theme:** "Dump a thought; see today's decision."

| Backend | Desktop |
|---|---|
| `work_notes`, `work_action_items` tables + Workspace services | Work section shell + Capture (⌘N) |
| Minimal `work_projects`, `work_items` (task type only) | Today lens (static layout) |
| Capture → triage → promote orchestration | Capture inbox |
| `PriorityPolicy` default + deterministic PriorityQueue (deadline + decay only) | Priority list (read-only) |
| Insights: Briefing assembler (deterministic numbers, no Brain yet) | Morning Brief v0 |
| `work_commands` capture/promote verbs + parity tests | queryKeys.work scaffold |

**Why now:** The product's wedge is the 30-second decision. Capture feeds the
Commitment ledger; Brief proves derivation works before time tracking or clients.

**Becomes usable:** Frictionless capture; a derived "what matters today" list; manual
project/task tracking.

**Risks removed:** Capture idempotency bugs; derived priority stored by accident;
planner integration unknowns.

---

## Phase 2 — Delivery graph (Products & Projects)

**Theme:** Portfolio structure for founders.

| Backend | Desktop |
|---|---|
| Product, Release, Project aggregates + full WorkItem tree | Work lens — product/project list |
| Milestone, Dependency + cycle validation | Project detail (narrative brief v0) |
| `work.product.*`, `work.item.*`, `work.dependency.*` events | Board as SavedView projection |
| Completion % derived (never stored) | invalidation-map for work events |

**Why now:** Holdings must exist before ROI/allocation by product. Dependency graph
is input to Phase 4 planning.

**Becomes usable:** Hierarchical work graph; portfolio roll-up; board view.

**Risks removed:** Type-ladder invariant gaps; dependency cycle corruption;
reparenting edge cases.

---

## Phase 3 — Time ledger + Execution

**Theme:** "Where did my hours actually go?"

| Backend | Desktop |
|---|---|
| TimeEntry, FocusSession, DayPlan, TimeBlock | Timer + Today time strip |
| CalendarPort injection + Capacity projection | Committed day plan UI |
| Allocation projection (Time → Project → holding) | Time lens — weekly allocation bars |
| Closed entry immutability + adjustment pattern | |

**Why now:** ROI, drift, and waste detection require Time ledger facts. Commitment
without Time cannot compute follow-through.

**Becomes usable:** Effortless time capture; capacity-aware planning; revealed
allocation.

**Risks removed:** Float time math; open timer races; calendar coupling via import.

---

## Phase 4 — Planning & Decision Engine

**Theme:** "What's most important across everything?"

| Backend | Desktop |
|---|---|
| Sprint, RoadmapPlan | Planning lens |
| Full prioritization function (goals + revenue weight + blocking) | Priority queue with "why" breakdown |
| Estimation service + calibration from TimeEntries | Estimate display + confidence |
| Decision Engine pure module tests | |

**Why now:** Requires Work graph, Time history, and Goal weights (Phase 5 partial
can stub weights — or parallelize Goal links early). Completes the Commitment ledger
orchestration layer.

**Becomes usable:** Explainable cross-portfolio priority; sprint/roadmap intent.

**Risks removed:** Priority score storage temptation; non-deterministic ranking;
Brain replacing deterministic core.

---

## Phase 5 — Engagements (Clients) + Finance Adapter

**Theme:** Freelance cash-now workflow.

| Backend | Desktop |
|---|---|
| Client, Engagement, Deliverable, RevenueExpectation | Clients lens |
| Finance read handler + ROI facade projection | Client brief (owed, payment, ROI/hr) |
| Deliverable risk derivation | Freelancing summary |
| `services/api/projections/work_roi.py` | |

**Why now:** Needs Time ledger (Phase 3) for ROI/hour and Finance read seam for
realized revenue. Unblocks honest client decisions.

**Becomes usable:** Client health; deliverable tracking; expected vs realized revenue.

**Risks removed:** Double-booking revenue; domain importing Finance; stale payment
flags in WorkOS.

---

## Phase 6 — Founder Dashboard

**Theme:** Portfolio capital allocation.

| Backend | Desktop |
|---|---|
| FounderDashboard facade projection | Founder lens |
| Portfolio health roll-up + verdict line | Verdict + holding cards |
| Stated vs revealed allocation | Attention strip |
| Cross-event invalidation (work + finance) | |

**Why now:** Requires holdings, both ledgers, Engagements, and Finance adapter —
the full reconciliation picture.

**Becomes usable:** "Is the company moving forward?" in one glance; rebalance lever.

**Risks removed:** Facade logic leaking into domain; incomplete invalidation.

---

## Phase 7 — Growth (Goals & strategic weight)

**Theme:** Why work matters.

| Backend | Desktop |
|---|---|
| Goal, KeyResult, LifeGoal, LearningPath | Goals lens |
| Habit read integration | Personal scorecard |
| GoalWeights → prioritization input | |
| Quarter progress projection | |

**Why now:** Strategic weight enriches priority and Founder views. Can ship after
core loops work without goals (Phase 4 used neutral weights).

**Becomes usable:** OKRs, learning paths, life goals feeding one queue.

**Risks removed:** Duplicate habits table; goal progress stored as typed field.

---

## Phase 8 — Insights, Health & Reviews

**Theme:** Periodic decisions.

| Backend | Desktop |
|---|---|
| HealthService, RiskService, ReviewService | Review lens |
| Report + PinnedRisk persistence | Weekly / monthly review UI |
| Brain jobs: review narrative, health explanation | "why" chips |
| Optional projection cache table | |

**Why now:** Needs stable ledgers + Founder metrics. Reports are snapshots — must
not precede trustworthy inputs.

**Becomes usable:** Weekly/monthly reallocation decisions; risk register.

**Risks removed:** Report becoming live source of truth; health write-back.

---

## Phase 9 — AI Chief of Staff

**Theme:** Propose, explain, commit.

| Backend | Desktop |
|---|---|
| Brain jobs: daily plan, briefing narrative, sprint proposal | Proposed plan commit flow |
| All proposals transient until `work_commands` commit | Trust dial settings (read) |
| Tiered models for capture structuring | |

**Why now:** AI on top of deterministic Decision Engine — graceful degradation
already proven in Phases 1–8.

**Becomes usable:** Narrated brief; proposed day/sprint with reasons + confidence.

**Risks removed:** Autonomous mutation; Brain in domain; proposal persisted as state.

---

## Phase 10 — Workspace depth + Knowledge Adapter

**Theme:** Meetings → commitments.

| Backend | Desktop |
|---|---|
| Meeting, DocumentRef full flow | Meeting log |
| Knowledge orchestration at API layer | Document links |
| Import provenance sockets (read-only) | |

**Why now:** Capture Phase 1 handles notes; meetings need stable Work graph for
ActionItem promotion.

**Becomes usable:** Meeting → action items → WorkItems; semantic doc links.

**Risks removed:** Embeddings in work tables; knowledge import in domain.

---

## Dependency graph (phases)

```
Phase 0
  └─► Phase 1 (Capture + Brief shell)
        └─► Phase 2 (Delivery graph)
              ├─► Phase 3 (Time ledger)
              │     └─► Phase 5 (Clients + Finance)
              │           └─► Phase 6 (Founder)
              └─► Phase 4 (Planning) — parallel after Phase 2; benefits from Phase 3
Phase 7 (Growth) — after Phase 4 recommended
Phase 8 (Insights/Reviews) — after Phase 6
Phase 9 (AI) — after Phase 8 recommended
Phase 10 (Workspace depth) — after Phase 2; full value after Phase 9
```

---

## Gate exit criteria (every phase)

From `IMPLEMENTATION_GOVERNANCE.md`:

1. Architecture tests pass (`test_dependencies.py`).
2. No derived columns in new migrations.
3. Every new mutation has chat/voice parity test or explicit deferral note.
4. Real SQLite tests — no mocked DB.
5. Desktop invalidation-map updated for new `work.*` events.
6. Black/isort/flake8/mypy/check_limits/pytest green in `apps/backend/`.

---

## Minimum lovable product

**Phases 0–3 + Phase 6 (partial):** Capture, commitments, time, allocation honesty,
and a thin Founder verdict — the Execution Model's daily loop.

**Phases 4–6 complete:** Full founder operating system for solo operator with
products and clients.

**Phases 7–10:** Strategic depth, reviews, AI narration, meetings — breadth without
reshaping the ledger architecture.
