# ADR 0022 — WorkOS two-ledger architecture

- **Status:** Accepted
- **Date recorded:** 2026-07-07
- **Deciders:** Principal Architect
- **WorkOS ADR index:** WOS-ADR-002 (two ledgers)
- **Relates to:** [0021](0021-workos-core-architecture.md),
  [0017](0017-finance-as-the-first-domain.md),
  [0005](0005-mutationevent-as-atomic-state-change.md),
  [0012](0012-sqlite-as-system-of-record.md)
- **Companion:** [`../workos/DATABASE_STRUCTURE.md`](../workos/DATABASE_STRUCTURE.md),
  [`../NOVA_WORKOS_EXECUTION_MODEL_v1.md`](../NOVA_WORKOS_EXECUTION_MODEL_v1.md)

## Context

Finance proved that a durable personal OS stores **movements**, not **balances**.
WorkOS applies the same discipline to attention:

- Founders misremember where time went (reality).
- Founders overcommit relative to capacity (intent).
- The **gap between intent and reality** is the highest-leverage decision signal
  in the product — follow-through, waste, drift, zombie investments.

The frozen execution model names two ledgers explicitly. Implementation must
define which rows belong to which ledger, how reconciliation works, and what
must never be persisted as a reconciled outcome.

## Decision

WorkOS persists exactly **two append-oriented ledgers** plus **holdings**
(positions attention flows through). Everything else is derived.

### Mental model

```
HOLDINGS (positions — not ledger rows, but attribution anchors)
  Product · Client · Goal · LifeGoal · Project (also a commitment container)

COMMITMENT LEDGER (intent — what you said you'd do / owe)
  └── analogous to Finance expectations + open obligations

TIME LEDGER (reality — where hours actually went)
  └── analogous to Finance transactions
```

Holdings are aggregate roots with lifecycle, not ledger entries. Ledger rows
**reference** holdings and objectives by id.

---

## Commitment Ledger

**Definition:** Any stored fact representing *intent, obligation, or planned
allocation* — future-facing or open-loop.

### Stored entry types

| Entry type | Aggregate | What it records | Mutation namespace (representative) |
|---|---|---|---|
| Work intent | `WorkItem` | A unit of work with estimate, deadline facets, status intent | `work.item.*` |
| Contractual output | `Deliverable` | Owed output with due date and acceptance state | `work.deliverable.*` |
| Extracted loop | `ActionItem` | Pre-promotion commitment from meeting/note | `work.actionitem.*` |
| Sprint promise | Sprint commitment link | Item id + committed estimate snapshot in active Sprint | `work.sprint.*` |
| Day allocation (committed) | `TimeBlock` in `committed` DayPlan | Planned span targeting a WorkItem | `work.timeblock.*`, `work.plan.committed` |
| Revenue promise | `RevenueExpectation` | Expected value attributed to Engagement or Project (exclusive) | `work.revenue.*` |
| Ranking policy | `PriorityPolicy` | Weight vector — **not** computed scores | `work.priority.reweighted` |
| Roadmap intent | `RoadmapPlan` entry | Planned window for Project/Milestone | `work.roadmap.*` |

### Commitment ledger rules

1. **Proposals are not commitments.** Brain-proposed DayPlans, sprint compositions,
   and rankings emit **no** `MutationEvent` until human commit.
2. **`proposed` DayPlan has zero side effects** — no calendar writes, no events.
3. **Priority scores are never commitment rows** — only `PriorityPolicy` weights
   are stored.
4. **Soft-delete removes from active reconciliation** — deleted WorkItems do not
   appear in open commitment sets; history remains for audits via events.
5. **Closed deliverables and done WorkItems** remain ledger history — they inform
   follow-through calculations but not "open obligation" counts.

### Primary queries (Memory ports)

- Open commitments by holding (Project, Client/Engagement, Product)
- Commitments due before date (hard vs soft deadline facet)
- Committed effort in active Sprint vs capacity
- Expected revenue by period (Engagements context)

---

## Time Ledger

**Definition:** Any stored fact representing *actual attention spent* — immutable
ground truth once closed.

### Stored entry types

| Entry type | Aggregate | What it records | Mutation namespace |
|---|---|---|---|
| Time fact | `TimeEntry` | Integer minutes against WorkItem or Project | `work.timeentry.*` |
| Session wrapper | `FocusSession` | Active tracking; **ends** by producing exactly one TimeEntry | `work.focus.*` |

### Time ledger rules

1. **Integer minutes only** — sums must be exact (Finance REAL-money ban applied
   to time).
2. **`closed` TimeEntry is immutable** — corrections are new adjusting entries
   (Finance adjustment discipline).
3. **One open timer per owner** — at most one open TimeEntry or active
   FocusSession.
4. **TimeEntry retains on WorkItem soft-delete** — time spent is truth; entries
   re-attribute to Project id.
5. **No derived totals stored** — velocity, time-invested, ROI numerator are
   folds over TimeEntry rows at read time.

### Primary queries (Memory ports)

- Sum minutes by WorkItem / Project / date range
- Sum minutes by holding attribution (via Project → Product/Engagement/Goal links)
- Velocity windows (completed effort / period — inputs to derived metrics)

---

## Reconciliation: how derived values are computed

Reconciliation always means: **read Commitment Ledger rows + Time Ledger rows +
facet links + foreign reads (Finance, Calendar) → pure function → derived object.**

Never: write reconciliation result back to SQLite.

### Core reconciliations

| Derived value | Formula (conceptual) | Inputs |
|---|---|---|
| **Follow-through rate** | closed commitment progress vs time allocated to same targets over period | Done WorkItems + Deliverables vs TimeEntries on those ids |
| **Attention allocation** | minutes by holding ÷ total minutes in period | TimeEntries → Project → (Product \| Engagement \| Goal) |
| **Stated vs revealed priority** | PriorityPolicy-weighted intent rank vs allocation % | PriorityPolicy + PriorityQueue vs allocation |
| **Commitment gap (drift)** | planned/committed minutes − logged minutes per day/week | committed DayPlan blocks vs TimeEntries |
| **Open obligation load** | sum(estimate) of open WorkItems + Deliverables due in window | Commitment rows |
| **Deliverable risk** | progress fraction vs time-to-deadline | Deliverable state + linked WorkItem progress + velocity |
| **Momentum** | recent TimeEntries + recent completions vs cadence target | Time ledger + commitment completions |
| **ROI** | value facet ÷ time invested | RevenueExpectation + Finance realized (facade) ÷ TimeEntry sum |
| **Zombie signal** | high cumulative time + flat momentum + no value path | Time ledger + commitment state + Finance read |
| **Portfolio verdict** | roll-up of holding health bands | All holding-level health derivations |

### Where reconciliation runs

| Derived kind | Computation site | May cache? |
|---|---|---|
| Single-aggregate derived (completion %, deliverable roll-up) | Owning context service / projection | Yes — invalidate on owning aggregate events |
| Cross-context computed (PriorityQueue, health) | `domains/work/planning`, `domains/work/insights` | Yes — event-scoped invalidation |
| Cross-domain (ROI, Dashboard, Briefing numbers) | `services/api/projections/` | Yes — invalidate on `work.*` + `finance.*` events |

---

## What is never stored

The following must **not** exist as columns, materialized tables of record, or
silent write-back fields anywhere in `memory/work/`:

| Never stored | Why |
|---|---|
| Priority score / rank order | Rots; policy weights are the only stored artifact |
| Health band (`thriving` … `zombie`) | Must recompute from fresh ledger data |
| ROI, Return on Attention, ROI/hour | Fusion of Time + Finance + expectations |
| Momentum, velocity, burn rate | Folds over ledgers |
| Completion % on Project/Product | Roll-up derived field |
| Portfolio verdict ("moving forward?") | Computed narrative input |
| Follow-through rate | Reconciliation metric |
| Allocation percentages | Derived from Time ledger |
| `blocked` as lifecycle state | Computed from dependency graph |
| Realized revenue / payment flags | Finance owns cash — facade read only |
| Brain proposal payloads | Transient until human commit |
| Reconciliation snapshots (except `Report`) | `Report` is an intentional immutable artifact with input metadata — not a live balance |

### Permitted exceptions (not ledger balances)

- **`Report`** — immutable generated snapshot with recorded input range (Insights).
- **`PinnedRisk`** — user elevation of a derived risk (Insights).
- **Sprint commitment estimate snapshot** — point-in-time intent at commit, not
  a recomputed priority.
- **Rebuildable projection cache** (optional) — see ADR 0023; disposable, keyed
  by event sequence.

---

## Alternatives considered

1. **Single unified ledger with `kind=intent|actual`.** Rejected: collapses
   immutability rules (TimeEntry closed vs WorkItem editable) and obscures the
   Finance analogy that engineers already understand.
2. **Store daily allocation % for dashboard speed.** Rejected: classic derived-
   state rot; invalidation across two ledgers is harder than recompute at personal
   scale.
3. **Mirror Finance transactions into WorkOS for client payments.** Rejected:
   double-booking; ADR 0011 + Finance ownership of cash.

## Consequences

- Every feature team must classify new rows as Commitment, Time, Holding, or
  Derived before adding schema.
- Code review checks for forbidden columns via governance doc and migration review.
- Insights and facade projections own reconciliation logic; domain services own
  single-aggregate derived fields only.
- Tests must assert: mutating a commitment does not write time totals; logging
  time does not mutate commitment status automatically (unless explicit transition
  event).

## Why alternatives were rejected

The two-ledger split is the load-bearing invariant that makes WorkOS Finance for
Execution. Collapsing or duplicating ledgers recreates spreadsheet semantics —
hand-maintained numbers that diverge from truth within weeks.

## Future evolution

- **Team mode:** TimeEntry and commitments gain `actor_id` facet; reconciliation
  formulas unchanged — sum by actor.
- **External calendar as time source:** imported blocks enter Time ledger through
  the same `TimeEntry` write path with provenance facet — never as a parallel
  ledger.
