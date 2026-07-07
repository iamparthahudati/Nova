# ADR 0021 — WorkOS core architecture

- **Status:** Accepted
- **Date recorded:** 2026-07-07
- **Deciders:** Principal Architect
- **WorkOS ADR index:** WOS-ADR-001 (core architecture)
- **Relates to:** [0011](0011-domain-isolation.md),
  [0017](0017-finance-as-the-first-domain.md),
  [0004](0004-memory-is-the-only-storage-owner.md),
  [0005](0005-mutationevent-as-atomic-state-change.md),
  [0015](0015-explainable-decision-making.md),
  [0016](0016-explicit-uncertainty.md)
- **Authority:** Subordinate to ADRs 0000–0020 and the frozen WorkOS design
  corpus (`NOVA_WORKOS_*_v1.md`). This ADR freezes *implementation*
  architecture; it does not reopen product or UX design.

## Context

WorkOS is Nova's second domain. Finance proved the pipeline (Memory → Domain →
`MutationEvent` → `finalize_mutations()` → projections). WorkOS must copy that
discipline on a harder asset — **attention** (time × focus) — while serving a
founder who simultaneously runs products, clients, and personal growth.

The frozen product model defines three non-negotiable pillars:

1. **Objective · Type · Facet** — a recursive entity model where every piece of
   work is an *Objective* classified by *Type* and decorated by orthogonal
   *Facets* (Value, Party, Outcome, Time, Assignment). Objectives nest; facets
   attach without duplicating hierarchy.
2. **Two Ledgers** — Commitment (intent) and Time (reality). All decision
   surfaces derive from reconciling them, exactly as Finance derives balance from
   transactions.
3. **Derived, Never Stored** — health, priority, ROI, momentum, allocation, and
   portfolio verdicts are pure functions of ledger rows and stored facets; they
   are never columns.

WorkOS also inherits Nova's global invariants: Brain is the only Claude client,
Memory is the only persistence owner, domains never import domains, every write
is a `MutationEvent`.

The architecture specification models seven *internal bounded contexts* inside
one domain package (`domains/work/`). Over-splitting into seven domain packages
would violate ADR 0011 — everyday links (Sprint → WorkItem, Engagement →
Project, Goal → prioritization weight) would require routing through Brain or
the composition root on every read.

## Decision

**WorkOS is one domain package with seven internal bounded contexts**, mirroring
Finance's single domain with subcontexts (`cashback/`, `rewards/`, `payments/`).

### Frozen core principles

| Principle | What it means in code | Why it exists |
|---|---|---|
| **Objective · Type · Facet** | Every stored work entity is an aggregate root with a closed `type` enum and facet attributes stored as scalar fields or id-links — never as embedded copies of foreign aggregates. Recursion is modeled via nullable parent id on a unified tree (`WorkItem`) and optional parent chain (`Product → Release → Project`). | One lifecycle/estimate/dependency model across hierarchy levels; AI can attach facets at capture time without the user filing forms; ten-year schema stability via discriminator instead of rigid per-level tables. |
| **Two Ledgers** | **Commitment Ledger:** stored intent — WorkItems, Deliverables, Sprint commitments, committed DayPlans, RevenueExpectations, ActionItems, PriorityPolicy. **Time Ledger:** stored reality — TimeEntry (immutable when closed), FocusSession → TimeEntry. | Finance-grade honesty: the gap between intent and reality is the primary signal (drift, waste, overcommitment). Storing derived reconciliation would rot. |
| **Derived, Never Stored** | Priority scores, health bands, ROI, momentum, completion %, velocity, allocation %, portfolio verdict — computed on read by pure assemblers; optional rebuildable caches only. | Prevents the classic project-tool failure mode: statuses and scores that diverge from ground truth because nobody maintained them. |
| **Finance-quality discipline** | Integer minor units for money; integer minutes for time; domain dates (`*_on`) separate from audit timestamps; soft-delete never hard-delete; closed TimeEntry is immutable (adjust via new row). | Exact arithmetic and auditability survive decades of data; matches Finance precedent already proven in production. |
| **AI Chief of Staff wedge** | Brain proposes; human commits; domain records only committed decisions as `MutationEvent`s. Every AI output carries reasons + confidence (ADR 0015/0016). | Trust is earned; WorkOS remains a first-class manual instrument when Brain is unavailable; autonomous mutation is out of scope for v1. |

### Package and dependency decision

```
domains/work/          → may import ONLY {memory, runtime}
memory/work/           → sole writer of WorkOS SQLite rows
services/planner/      → gains domains.work edge (work_commands/queries/serializers)
services/api/          → gains domains.work edge + cross-domain projections
```

**No `domains.work → domains.finance` edge.** Work × Finance fusion happens only
at `services/api/projections/` or in Brain reading Memory — never by domain import.

### Entity model mapping (Objective · Type · Facet → aggregates)

The frozen recursive model maps to stored aggregates without a separate
"objectives" table:

| Frozen concept | Implementation aggregate | Type enum (examples) | Facets (stored attributes / id-links) |
|---|---|---|---|
| Holding (stream altitude) | `Product`, `Client`, `Goal`, `LifeGoal` | `product`, `client`, `goal`, `life_goal` | Value (RevenueExpectation, rate model), Party (Client link), Outcome (Goal contribution links), Time (deadlines, cadence) |
| Commitment | `WorkItem`, `Deliverable`, `ActionItem`, Sprint commitment link, committed `DayPlan`/`TimeBlock` | `epic/story/task/subtask`, `deliverable`, `action_item` | Value, Time (estimate + deadline + hardness), Outcome (Milestone target), Party (Engagement/Client id) |
| Time fact | `TimeEntry`, `FocusSession` | `time_entry`, `focus_session` | Time (duration, target WorkItem/Project id) |
| Policy (not a score) | `PriorityPolicy` | `priority_policy` | Weight vector only — scores are derived |

Recursion: `WorkItem` self-parent tree; optional `Product → Release → Project`
chain via nullable foreign ids.

### Context ownership (internal to `domains/work/`)

| Context | Owns (writes) | Never owns |
|---|---|---|
| **A — Work** | Product, Release, Project, WorkItem, Milestone, Dependency, SavedView | Scheduling, ranking, money realization |
| **B — Planning** | Sprint, RoadmapPlan, PriorityPolicy | WorkItem rows (references only) |
| **C — Execution** | DayPlan, TimeBlock, TimeEntry, FocusSession | Calendar (injected port) |
| **D — Engagements** | Client, Engagement, Deliverable, RevenueExpectation, Interaction | Finance transactions |
| **E — Growth** | Goal, KeyResult, LearningPath/Item, LifeGoal | Habit storage (reads `memory/habits.py`) |
| **F — Workspace** | Meeting, Note/Capture, ActionItem, DocumentRef | Document bodies, embeddings |
| **G — Insights** | Report, PinnedRisk only | Any primitive; all dashboards are projections |

Insights reads all contexts; it writes nothing except generated artifacts and
user-pinned risks.

## Explicit non-goals

WorkOS implementation architecture explicitly refuses:

- **Redesigning the entity model** — no fourth ledger, no alternate hierarchy, no
  stored health/priority columns.
- **Seven separate domain packages** — contexts are directory/convention
  boundaries, not import boundaries.
- **Domain-to-domain imports** — especially Work → Finance.
- **Brain inside the domain** — AI orchestration lives above `domains/work/`.
- **External systems as source of truth** — GitHub, Calendar, email are enrichers
  via injected ports; SQLite remains authoritative (ADR 0001).
- **Team/multiplayer in v1** — `owner_id` is reserved on every aggregate for
  future filtering; no auth model in v1.
- **Autonomous execution** — proposals never mutate; trust-gated agents are a v2
  horizon.
- **Board/kanban as hero surface** — SavedView/Board is a persisted filter;
  board *contents* are projections.
- **Duplicate money ledger** — WorkOS stores revenue *expectation* only; Finance
  owns cash.

## Alternatives considered

1. **Seven domain packages (one per context).** Rejected: violates the spirit of
   ADR 0011 applied to internal links; creates a mesh of Brain/facade hops for
   everyday operations.
2. **Stored priority and health columns "for performance."** Rejected: rots;
   contradicts Finance precedent and the 30-second test (stale scores lie).
3. **WorkOS imports Finance for ROI.** Rejected: cross-domain read at facade
   only; prevents coupling and double-booking.
4. **Unified `objectives` table with JSON facets.** Rejected: loses Finance-grade
   invariants, typed lifecycles, and query predictability; harder to enforce in
   SQLite over ten years.

## Consequences

- Finance is the template: every WorkOS context repeats
  aggregates/ports/adapters/mutations/projections/services.
- `tests/architecture/test_dependencies.py` gains `domains.work → {memory,
  runtime}` and planner/api inbound edges — human-gated before WOS-1 code.
- Cross-domain projections (`Dashboard`, `ROI`, `RevenueForecast`, `Briefing`
  numbers) live in `services/api/projections/`, not in the domain.
- Product/Release aggregates are modeled from day one (nullable links) even if
  UI ships later — avoids portfolio reshape.
- Shared `Money` value object must be promoted to a root utility (see ADR 0021
  companion decision in implementation plan WOS-0) so Engagements never imports
  `domains.finance`.

## Why alternatives were rejected

Alternatives 1–4 all trade short-term convenience for the ten-year failure modes
WorkOS exists to prevent: stale derived state, cross-domain coupling, and schema
rigidity that blocks product/freelance/personal work in one system.

## Future evolution

- **Teams / company mode:** filter existing rows by `owner_id`; add membership
  aggregates — no ledger reshape.
- **Cached projections:** rebuildable cache keyed by `MutationEvent` stream (see
  ADR 0023); never authoritative columns.
- **CRM depth, hiring, imports:** new subcontexts under `domains/work/` using
  the same aggregate pattern — additive only.
