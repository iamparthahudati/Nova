# WorkOS — Implementation Governance

**Status:** Permanent engineering law for WorkOS (and Nova domains thereafter).  
**Authority:** ADRs 0021–0023, Handbook §1/§5/§11, `CLAUDE.md`.  
**Enforcement:** Code review, architecture tests, CI gates, ADR process.

Violations require an ADR to override — not a PR comment negotiation.

---

## The ten laws

### 1. Derived never stored

No column, cache table row, or silent write-back may hold live priority, health,
ROI, momentum, allocation %, completion %, velocity, portfolio verdict, or
reconciliation balances.

**Allowed:** rebuildable projection cache; immutable `Report` snapshots with input
metadata.

**Test:** migrations linter + no forbidden column names.

---

### 2. Every feature must answer: "What decision does this improve?"

If a surface, API endpoint, or metric cannot name the founder decision it drives
(see Execution Model §19), it does not ship.

Data-without-decision is vanity — banned.

---

### 3. No duplicate source of truth

| Truth | Owner |
|---|---|
| Cash / realized revenue | Finance |
| Time spent | TimeEntry rows |
| Work intent | Commitment ledger rows |
| Document bodies / embeddings | Knowledge |
| Calendar events | Calendar service |
| Habits | `memory/habits.py` |

WorkOS stores expectations, pointers, and provenance ids — never copies of
foreign authoritative data.

---

### 4. No module crossing boundaries

`domains/work` imports only `{memory, runtime}`.

Cross-domain reads happen at `services/api/projections/` or Brain orchestration —
never domain-to-domain.

**Enforced by:** `tests/architecture/test_dependencies.py`.

---

### 5. No circular dependencies

Dependency direction:

```
services.api → domains.work → memory.work
services.planner → domains.work → memory.work
```

Insights assemblers may call Planning pure functions; Planning must not import
Insights. Decision Engine pure modules depend on nothing except DTOs and clock.

---

### 6. Every derived value rebuildable

Given: all ledger rows + facet links + foreign read DTOs + injected clock → every
derived/computed object in ADR 0023 must reproduce identically (modulo Brain
narrative non-determinism — numbers must match).

**Test:** golden-file recomputation from fixture SQLite.

---

### 7. Every cache disposable

Deleting all caches (server + desktop React Query + optional projection_cache)
must leave the system fully correct — only slower.

Caches never participate in write paths.

---

### 8. Every AI recommendation explainable and uncertain

Per ADR 0015/0016: reasons + confidence on every ranking, plan block, forecast,
health claim. "I'm not sure" is valid output.

Deterministic priority breakdown lives in domain; Brain adds narrative only.

---

### 9. Every mutation produces an event

No `memory/work` write from router or service without `MutationEvent` →
`finalize_mutations()`.

Proposals (Brain, uncommitted plans) emit **nothing**.

**Enforced by:** side_effects pipeline; no direct Memory writes in `services/api`
except through finalize path (existing Finance/desktop precedent).

---

### 10. Two ledgers — classify before you schema

Every new persisted row must declare: **Commitment**, **Time**, **Holding**, or
**Artifact** (Report/PinnedRisk). If none fit, it is probably derived — do not
store it.

---

## Code organization laws

| Law | Rule |
|---|---|
| Memory sole writer | Only `memory/work/*` touches `work_*` tables |
| Brain sole Claude client | No Anthropic outside `services/brain` |
| Ports not adapters in services | Domain services depend on `repositories.py` ports |
| Pure assemblers | `projections.py`, `prioritization.py` — no I/O, injected clock |
| Integer truth | minor units, integer minutes — no floats in money/time aggregates |
| Soft delete only | no hard DELETE in user-facing paths |
| Parameterized SQL | always — no f-string queries |
| File/function limits | Handbook §3 — check_limits.py blocking |

---

## Mutation vocabulary law

Event names: `work.<entity>.<operation>`.

`entity` in event = full aggregate snapshot in payload.

New `entity_type` values are additive — `MutationEvent` dataclass shape is frozen.

Memory-producer policy: memorable events only (project completed, goal achieved,
engagement closed) — not routine churn.

---

## Desktop law

- Business logic stays in backend domain/facade — desktop shapes view models only.
- `dataSource` + React Query — no raw fetch in components.
- Every new `work.*` event updates `invalidation-map.ts`.
- queryKeys under `['nova','work', …]`.

---

## AI governance

| Rule | Detail |
|---|---|
| Propose never mutate | Human commit via `work_commands` |
| Numbers from facade/domain first | Brain narrates; does not invent ROI |
| Graceful degradation | Full manual instrument with Brain offline |
| No autonomous v1 actions | Trust-gated agents are v2+ ADR |
| Tiered models | cheap for structure, strong for reasoning (ADR 0002) |

---

## Review checklist (every WorkOS PR)

- [ ] Which ledger does this write to?
- [ ] What decision does this improve?
- [ ] Any new derived value registered in ADR 0023?
- [ ] Any new import edge in ALLOWED_EDGES?
- [ ] Migration: no forbidden columns; `owner_id` present?
- [ ] Tests use real SQLite?
- [ ] Chat/voice parity if new mutation?
- [ ] invalidation-map updated?
- [ ] CI green: black, isort, flake8, mypy, check_limits, pytest, architecture tests?

---

## ADR trigger list (human required)

Stop and draft ADR before implementing:

- Package boundary change
- New `ALLOWED_EDGES` entry
- `MutationEvent` shape change
- New stored aggregate type not in DATABASE_STRUCTURE.md
- Projection cache as source of truth (never allowed — but adding cache table needs note)
- Autonomous mutation
- External system as source of truth
- Any change to ADRs 0021–0023 principles

---

## Governance evolution

These laws apply for the life of WorkOS. Amendments are **new ADRs** that supersede
— never silent drift. The Implementation Risks doc is living; update when new
risks are discovered in production.

The 30-second test from the Execution Model is the ultimate acceptance criterion
for any governance exception request.
