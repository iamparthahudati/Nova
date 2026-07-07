# WorkOS — Implementation Risks

**Status:** Staff-engineering pre-mortem (canonical).  
**Authority:** ADRs 0021–0023, `NOVA_WORKOS_DATA_MODEL_v1.md` §10.  
**Scope:** Identify risks and mitigations only — **no redesign.**

Risks ordered by **cost-to-reverse once production data exists.**

---

## 1. Owner scoping not reserved (CRITICAL)

**Risk:** Shipping WOS-1 tables without `owner_id` forces a full-table migration
and query rewrite for team mode — the most expensive retrofit.

**Mitigation:** Phase 0 DDL reservation on every table; default single operator;
all list queries shaped with owner filter from day one (filter constant in v1).

**Detection:** Architecture test or migration linter asserts `owner_id` column on
every new `work_*` table.

---

## 2. Derived state leakage into storage (CRITICAL)

**Risk:** A "small" `health_status` or `priority_score` column for performance
rots within weeks; dashboards disagree with ledger truth.

**Mitigation:** ADR 0022/0023 inventory; code review checklist; Memory write
functions reject unknown fields; no UPDATE sets computed values as side effect.

**Detection:** Schema audit script; grep ban for forbidden column names in
migrations.

---

## 3. SQLite scale ceilings

**Risk:** Full recompute of PriorityQueue + Portfolio on every read degrades
after ~100k TimeEntries / deep WorkItem trees if assemblers are naive O(n²).

**Mitigation:**  
- Personal-scale first — optimize assemblers (indexed queries, incremental graph walks).  
- Optional `work_projection_cache` (ADR 0023 Level 1–2) — rebuildable only.  
- Architecturally important indexes in DATABASE_STRUCTURE.md.

**Trigger for cache ADR:** p95 read > 500ms on founder machine with realistic seed.

---

## 4. Dependency graph recursion pitfalls

**Risk:** Cycle in `blocks` edges breaks topological sort → infinite loop in
planning/critical-path; service bypass could insert cycle (SQLite cannot enforce
acyclicity).

**Mitigation:**  
- Cycle check on every edge add (DFS/BFS with depth cap).  
- Architecture test: single write path through domain services.  
- Unit tests: known cyclic fixtures rejected.

**Detection:** Periodic integrity job (dev command) validating DAG in test suite.

---

## 5. Event ordering and multi-surface conflicts

**Risk:** Desktop + chat + voice touch same WorkItem; last-write-wins clobbers
without conflict signal.

**Mitigation:** Optimistic concurrency via `updated_at` compare on UPDATE (Finance
precedent); conflict returns 409 with fresh aggregate; MutationEvent audit trail.

**Future:** Explicit `revision` counter if conflicts prove frequent (data model open
question — not v1 unless measured).

---

## 6. Cache invalidation gaps

**Risk:** React Query or projection cache serves stale ROI after Finance
transaction without invalidating work dashboard keys.

**Mitigation:**  
- Explicit `invalidation-map.ts` per `work.*` and cross-domain `finance.*` event.  
- Integration test: mutation → WebSocket event → expected query keys invalidated.  
- Recompute wins over cache (ADR 0023).

**Detection:** Manual QA script; automated desktop test with mock event stream.

---

## 7. Cross-domain synchronization semantics

**Risk:** WorkOS RevenueExpectation diverges from Finance reality because engineer
stored "paid" on WorkOS row or matched transactions by fuzzy name.

**Mitigation:**  
- WorkOS never stores realization.  
- Facade joins by explicit Project/Engagement attribution id only.  
- Finance Adapter reads public query API — not finance table internals from Work
code.

**Detection:** Boundary test forbids `domains.work → domains.finance`.

---

## 8. Timezone / date bucket errors

**Risk:** Server derives local date from UTC `created_at` → wrong day bucket for
TimeEntries and DayPlans — irreversible misallocation.

**Mitigation:** Producer-supplied local dates for domain fields; inject clock;
Handbook ban on inline `datetime.now()` in pure logic; parity tests across TZ
offsets.

---

## 9. TimeEntry immutability violations

**Risk:** Editing closed entries breaks ROI and velocity history.

**Mitigation:** Finance adjustment pattern — closed rows immutable; corrections via
new adjusting entry with link metadata; service rejects UPDATE on closed rows.

---

## 10. Idempotent capture promotion failure

**Risk:** Re-processing meeting extracts duplicate WorkItems (MT1 invariant).

**Mitigation:** Promotion key = `(meeting_id, action_item_id)` unique constraint;
orchestration test before Phase 10 ships.

---

## 11. Brain proposal → mutation boundary creep

**Risk:** Brain job writes directly to Memory "to save a step" — breaks propose/commit
and auditability.

**Mitigation:** Brain package imports Memory read-only; commits only through
`work_commands` → MutationEvent; architecture test on `services.brain` writes.

---

## 12. Migration strategy risks

**Risk:** Long-running migration locks SQLite on founder laptop; broken migration
bricks local DB.

**Mitigation:**  
- Idempotent DDL per gate; small migrations.  
- Backup prompt before schema bump (desktop).  
- Forward-only migrations; restore from backup on failure.  
- Schema version gate — old app refuses write on new schema.

---

## 13. Testing strategy gaps

**Risk:** Mocked DB tests pass while real SQLite constraint violations fail in prod.

**Mitigation (Handbook + ADR 0022):**  
- Real temp SQLite (`tmp_path`) for all persistence tests.  
- Golden recomputation tests: fixture DB → assembler → expected derived DTO.  
- Architecture tests first in CI.  
- Parity tests: chat verb ↔ same mutation as REST.  
- Graph invariant tests for dependencies.  
- No assertions on stored derived columns — only on recomputation output.

**Gap to watch:** Cross-domain facade tests need Finance seed + Work seed in one
SQLite — build shared fixture factory in Phase 5.

---

## 14. LanceDB / Knowledge coupling

**Risk:** Storing embeddings in `memory/work` duplicates Knowledge ownership.

**Mitigation:** DocumentRef pointer only; Knowledge indexes via Memory read;
boundary test.

---

## 15. Single-process runtime scheduling

**Risk:** Nightly briefing job races with user write or runs duplicate Brain calls.

**Mitigation:** ADR 0006 single-process model; access-triggered jobs with debounce;
job idempotency key per date; no background thread writes bypassing MutationEvent.

---

## 16. WorkItem tree depth / reparenting cost

**Risk:** Deep subtrees make soft-delete cascade and roll-up expensive.

**Mitigation:** Depth sanity cap in service (warn at >8); subtree queries via
indexed `project_id` + recursive CTE with depth limit; archive projects instead
of mega-trees.

---

## 17. Report artifact confusion

**Risk:** Engineers treat stored `Report` as live dashboard source instead of
immutable snapshot.

**Mitigation:** Report DTO labeled `snapshot`; live views always recompute; Report
stores input range metadata for reproducibility.

---

## Risk monitoring (2036 maintenance)

| Signal | Action |
|---|---|
| Rising read latency | Profile assemblers → cache (Level 1) |
| Conflict 409 rate | Consider `revision` column ADR |
| Cache/ledger mismatch | Truncate cache; Level 2 rebuild |
| New derived surface | Register in ADR 0023 inventory before merge |
| Schema change | Forward migration + optional rebuild |

---

## Explicitly accepted risks (v1)

- **No row-level field history** — MutationEvent audit only; temporal tables deferred.
- **Single operator** — auth/multiplayer not built; `owner_id` reserved only.
- **Personal-scale SQLite** — no sharding; single file local-first.
- **Deterministic priority only in domain** — Brain narrates, does not own score.

These are documented tradeoffs, not oversights.
