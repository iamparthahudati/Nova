# ADR 0023 — WorkOS derived state

- **Status:** Accepted
- **Date recorded:** 2026-07-07
- **Deciders:** Principal Architect
- **WorkOS ADR index:** WOS-ADR-003 (derived state)
- **Relates to:** [0021](0021-workos-core-architecture.md),
  [0022](0022-workos-two-ledger-architecture.md),
  [0015](0015-explainable-decision-making.md),
  [0016](0016-explicit-uncertainty.md),
  [0013](0013-lancedb-as-vector-index.md)
- **Companion:** [`../workos/IMPLEMENTATION_GOVERNANCE.md`](../workos/IMPLEMENTATION_GOVERNANCE.md)

## Context

WorkOS surfaces — Morning Brief, Founder dashboard, health bands, priority queue,
ROI — depend on values that are **not** authoritative rows. Finance already
enforces this for balances, statement status, and reward balances. WorkOS has
more derived surface area because the chief-of-staff wedge computes rankings,
health, and narratives continuously.

Implementation needs a canonical inventory of every derived object, a clear rule
for cache vs source of truth, and a rebuild strategy that survives database
corruption, cache loss, and schema migrations over ten years.

The data model distinguishes:

- **Derived field** — pure function of one aggregate's own stored children/attributes.
- **Computed field** — requires multiple aggregates, contexts, Calendar, Finance,
  or Brain.

Both are never stored as live authoritative columns. This ADR lists every derived
object in v1 scope.

## Decision

### Source of truth hierarchy

```
1. SQLite rows in memory/work/     (Commitment + Time ledgers + holdings + facets)
2. MutationEvent stream           (audit + invalidation + rebuild ordering)
3. Foreign reads at facade        (Finance realized, Calendar busy, Knowledge search)
4. Rebuildable caches             (optional; disposable)
5. Derived / computed objects     (never authoritative; always reproducible from 1–3)
```

If a cached value disagrees with a full recompute from (1–3), **the recompute wins**
and the cache is discarded.

---

## Canonical inventory of derived objects

### A — Single-aggregate derived (in-domain)

| Object | Owner module | Inputs | Output shape |
|---|---|---|---|
| Project completion % | Work | Milestone + WorkItem statuses | 0–100 integer |
| Product completion roll-up | Work | Release/Project completion | 0–100 + counts |
| Release scope completion | Work | Committed Milestones reached | % + slip days |
| Milestone progress | Work | Targeted WorkItem done ratio | % + reached/missed |
| WorkItem subtree progress | Work | Child WorkItem statuses | % |
| WorkItem logged time sum | Work | TimeEntry ids referencing item | integer minutes |
| WorkItem staleness | Work | last activity timestamp + now (injected) | days idle |
| Engagement deliverable reconciliation | Engagements | Σ Deliverable values vs engagement value | match flag + delta |
| Client last-contact | Engagements | Interaction timestamps | date + count |
| Goal progress | Growth | KeyResult current/target | % + trajectory |
| Learning path progress | Growth | LearningItem states | % |
| DayPlan planned minutes | Execution | TimeBlock durations | integer minutes |
| DayPlan adherence | Execution | planned blocks vs TimeEntries same date | % + gap |
| FocusScore | Execution | FocusSession duration + interruptions | score + reasons |
| Sprint committed vs capacity | Planning | commitment links + capacity facet | minutes + over-flag |

### B — Cross-context computed (inside `domains/work/`)

| Object | Owner module | Inputs |
|---|---|---|
| **PriorityQueue** | Planning | WorkItems + Dependencies + deadlines + Goal weights + PriorityPolicy + decay + now |
| **Priority score (per item)** | Planning | Same — component breakdown per item |
| **Backlog ordering** | Planning | PriorityQueue filtered to non-sprint items |
| **Blocked-in-fact** | Work / Planning | Dependency graph active `blocks` edges |
| **Critical path adjacency** | Planning | Dependency DAG traversal |
| **Capacity** | Execution | Calendar busy (injected) + Habits + Meetings |
| **Velocity** | Execution / Planning | Sprint completions + TimeEntries over window |
| **EnergyScore** | Execution | Historical throughput by time-of-day | 
| **Roadmap capacity flags** | Planning | RoadmapPlan windows vs Capacity |
| **Estimate calibration bias** | Planning | Historical estimate vs TimeEntry actuals |
| **ProjectHealth inputs bundle** | Insights | schedule variance, velocity, blocked count/age, staleness |
| **RiskRegister (derived portion)** | Insights | deadline, dependency, allocation, staleness, revenue-at-risk rules |
| **DeadlineRisk** | Insights | deadlines + velocity + capacity collisions |
| **BurnRate trend** | Insights | time invested per holding over periods |
| **FreelancingSummary** | Engagements | engagements + deliverables + expectations |
| **LearningProgress** | Growth | paths + items + goal links |
| **QuarterProgress** | Growth / Insights | goals + KRs + milestone hits |
| **PersonalScorecard** | Growth / Insights | goals + habits + life goals |

### C — Cross-domain facade computed (`services/api/projections/`)

| Object | Inputs |
|---|---|
| **TodaysFocus** | committed DayPlan + PriorityQueue + Calendar + Capacity |
| **Dashboard** | health + ROI + revenue + allocation + risks |
| **FounderDashboard / CEODashboard** | portfolio health + expected-vs-realized + hour allocation |
| **ROI (per holding)** | TimeEntry sums + RevenueExpectation + Finance realized |
| **Return on Attention** | portfolio ROI roll-up |
| **RevenueForecast** | expectations + trajectory + Finance realized |
| **Portfolio verdict** | health roll-up + momentum |
| **Realized-vs-expected revenue** | RevenueExpectation + Finance query API |

### D — Brain-computed (transient until committed)

| Object | Persisted? | Notes |
|---|---|---|
| Proposed DayPlan | No | Becomes Commitment ledger on commit |
| Proposed Sprint composition | No | |
| Prioritization narrative | No | Scores are deterministic; narrative is Brain |
| Weekly/Monthly review narrative | Stored as `Report` on generate | Snapshot artifact |
| Briefing narration | No (live) / optional Report snapshot | Numbers from facade first |
| Suggested dependencies | No | User confirms → Dependency rows |
| Proposed estimates | No | Committed estimate facet on WorkItem |
| Triage suggestions for Capture | No | |

All Brain outputs must include **reasons** and **confidence** (ADR 0015/0016).

---

## Cache vs source of truth

| Layer | Role | Invalidation trigger |
|---|---|---|
| SQLite rows | **Source of truth** | N/A |
| MutationEvent stream | Audit + ordering + cache keys | Append-only |
| In-process memo (request scope) | Performance | End of request |
| Projection cache table (optional) | **Rebuildable** | Any `MutationEvent` matching entity/event map |
| React Query (desktop) | **Client cache** | WebSocket event → `invalidation-map.ts` |
| LanceDB vectors | **Rebuildable index** | Knowledge indexing jobs — not WorkOS truth |

### Cache rules (mandatory)

1. **No cache is authoritative.** Deleting all caches must not lose data.
2. **Cache keys include owner scope** (`owner_id`) even when unused in v1.
3. **Invalidation map is explicit** — each `work.*` event type maps to query keys;
   no "invalidate everything" except schema migration rebuild.
4. **Cross-domain caches** (ROI, Dashboard) invalidate on both `work.*` and
   relevant `finance.*` events.
5. **Brain outputs are never cached as state** — only as ephemeral response or
   persisted `Report` artifact.

---

## Rebuild strategy

### Level 0 — Normal operation (no rebuild)

On each read: projection assembler loads live rows via ports → pure function →
DTO. Acceptable default at personal scale (≤100k TimeEntries, ≤10k WorkItems).

### Level 1 — Event-driven cache refresh

After `finalize_mutations()`:

1. Emit `MutationEvent` to desktop WebSocket.
2. If projection cache enabled: delete cache rows matching event's invalidation
   set (entity_type, entity_id, project_id, parent_id from metadata).
3. Next read recomputes and optionally repopulates cache.

### Level 2 — Full derived rebuild (maintenance)

Triggered by: schema migration, cache corruption detection, manual dev command,
or new derived formula deployment.

Procedure:

```
1. TRUNCATE rebuildable cache tables (never touch ledger tables)
2. For each projection type P:
     load required inputs from memory/work/* + facade foreign reads
     compute P from scratch
     optionally write cache row tagged with rebuild_version + max(event_id)
3. Verify spot-check invariants (e.g., sum(TimeEntry) matches ROI numerator)
4. Log rebuild completion with timestamp + event cursor
```

**Ledger rows are never modified during rebuild.**

### Level 3 — Disaster recovery

Source of truth recovery order:

1. Restore SQLite from backup (ADR 0012).
2. Replay is **not** required for v1 — rows are authoritative; MutationEvent stream
   is audit-only unless event-sourcing replay is added later.
3. Drop all caches; run Level 2 rebuild.
4. Re-index Knowledge/LanceDB separately (ADR 0013).

### Rebuild ownership

| Projection family | Rebuild owner |
|---|---|
| In-domain projections | `domains/work/*/projections.py` assemblers |
| Facade projections | `services/api/projections/work_*.py` |
| Desktop view models | Re-fetch via API after invalidation |

---

## Alternatives considered

1. **Materialized views in SQLite for Dashboard/ROI.** Rejected as source of truth —
   acceptable only as explicit rebuildable cache with governance tags.
2. **Store health on Project row updated by nightly job.** Rejected — write-back
   derived state; violates ADR 0022.
3. **Event sourcing as primary store.** Rejected for v1 — rows + MutationEvent audit
   matches Finance; lower operational complexity.

## Consequences

- Every new derived object must be registered in this inventory before merge.
- Projection assemblers must be pure (clock-injected, no I/O inside compute).
- Tests: golden-file recomputation from fixture SQLite — never assert stored
  derived columns.
- Performance work targets assembler efficiency and optional cache — not stored
  balances.

## Why alternatives were rejected

Stored derived state is the highest-risk long-term debt in productivity software.
Finance already paid the design cost to forbid it; WorkOS inherits that cost as
the core product promise.

## Future evolution

- **Event-sourced replay:** if per-field temporal history is required, additive
  ADR — ledger rows remain truth for v1.
- **Background rebuild worker:** if Level 2 exceeds request timeout — still
  rebuildable cache, not authoritative columns.
