# WorkOS — Phase 1 Schema Gate (Design Artifact)

**Status:** Final design. Approved input for WOS-1 implementation. **No code in this
document is implemented.**  
**Authority:** ADRs 0021–0023, `NOVA_WORKOS_DATA_MODEL_v1.md`, `DATABASE_STRUCTURE.md`,
`IMPLEMENTATION_PLAN.md` Phase 1, `IMPLEMENTATION_GOVERNANCE.md`, Phase 0 (frozen).  
**Supersedes:** nothing yet — this is the first WorkOS schema gate (Finance analogue:
[`FINANCE_DATA_MODEL.md`](../architecture/FINANCE_DATA_MODEL.md)).  
**Hard constraints (unchanged, restated):** Memory is the only persistence owner;
`MutationEvent` shape is frozen; derived values are never stored columns; two ledgers
(Commitment + Time); WorkOS never imports Finance; integer minutes for time facets;
integer minor units for money (Phase 1 has no money columns); soft-delete for
high-churn rows; archive for holdings.

**Phase 1 product scope (frozen — do not expand here):** frictionless capture;
minimal project + task tracking; capture → triage → promote; default `PriorityPolicy`;
deterministic `PriorityQueue` (deadline + decay only); Morning Brief shell
(deterministic numbers, no Brain); chat/voice parity for new mutations.

**Approved decisions baked into this model (not re-litigated here):**
`owner_id` reserved on every table (NOT NULL, DEFAULT `1` in v1) · UTC
`created_at`/`updated_at` · domain dates as local `TEXT 'YYYY-MM-DD'` ·
optimistic concurrency via `updated_at` compare (Finance precedent) ·
`MutationEvent` stream is audit/invalidation, **not** a SQLite table ·
`work_commands` is a planner module, **not** a table · projection cache deferred
to WOS-8+ · Phase 1 `WorkItem.type` is **`task` only** at the service layer
(schema allows the full enum for forward compatibility).

---

## 0. Persistence inventory — what Phase 1 includes and excludes

### 0.1 Tables in scope (five)

| Table | Aggregate root | Context |
|---|---|---|
| `work_notes` | Note / Capture | Workspace (F) |
| `work_action_items` | ActionItem | Workspace (F) |
| `work_projects` | Project | Work (A) — **Holding + commitment container** |
| `work_items` | WorkItem | Work (A) — **Commitment ledger** |
| `work_priority_policies` | PriorityPolicy | Planning (B) — **Commitment ledger (policy, not scores)** |

### 0.2 Explicitly excluded from SQLite (frozen architecture — not omissions)

| Name | What it actually is | Why no table |
|---|---|---|
| **`work_commands`** | `services/planner/work_commands.py` — chat/REST write verbs → domain services | Integration module per `NOVA_WORKOS_ARCHITECTURE_v1.md` §9; same pattern as `finance_commands.py`. |
| **`work_mutation_events`** | `MutationEvent` objects in `runtime/mutation_event.py` → `finalize_mutations()` → WebSocket | Finance has no `finance_mutation_events` table. ADR 0023: ledger rows are authoritative; event stream is audit + invalidation, not v1 replay store. |
| **`work_projection_checkpoint`** | Optional rebuildable cache (`work_projection_cache` in `DATABASE_STRUCTURE.md`) | ADR 0023 Level 0: recompute on read at personal scale. Cache table is **WOS-8+** optional; Phase 1 PriorityQueue and Briefing numbers are pure reads. |

### 0.3 Lookup tables

**None.** Phase 1 closed enums live in `CHECK` constraints. Categories of capture
source, status, and ledger classification do not warrant separate reference tables
at personal scale (Finance `category`/`merchant` TEXT precedent).

---

## 1. Cross-cutting persistence rules

### 1.1 `owner_id` strategy

- Every Phase 1 table includes `owner_id INTEGER NOT NULL DEFAULT 1`.
- v1: constant `1` (single operator). All list/query helpers in `memory/work/*`
  accept `owner_id` and filter on it — shape queries for team mode before it exists.
- Future: remove DEFAULT; filter by authenticated membership. **No schema reshape.**
- Indexes prefix `(owner_id, …)` on every hot list path.

### 1.2 Objective · Type · Facet mapping (Phase 1)

| Frozen concept | Phase 1 aggregate | `type` / discriminator | Facets stored as columns (Phase 1) |
|---|---|---|---|
| **Holding** (stream anchor) | `Project` | implicit `project` | **Outcome** → `name`, optional `objective` · **Time** → `planned_start_on`, `planned_end_on` |
| **Commitment** (intent) | `WorkItem` | `type = 'task'` only (service-enforced) | **Time** → `estimate_minutes`, `estimate_confidence`, `deadline_on`, `deadline_hardness` · **Outcome** → `title` · **Assignment** → `project_id` |
| **Commitment** (pre-promotion) | `ActionItem` | implicit `action_item` | **Outcome** → `title` · **Party/Time** → deferred (no client/deadline in Phase 1) |
| **Artifact** (intake) | `Note` | implicit `note` / capture | **Outcome** → `body` · provenance → `capture_source`, `captured_on` |
| **Policy** (not a score) | `PriorityPolicy` | implicit `priority_policy` | Weight vector → `deadline_weight`, `decay_weight` only in Phase 1 |

Recursion sockets reserved, unused in Phase 1: `work_items.parent_id` (NULL),
`work_projects.release_id` (NULL), `work_projects.engagement_id` (NULL).

### 1.3 Ledger classification

| Table | Ledger | Rationale |
|---|---|---|
| `work_projects` | **Holding** | Position attention flows through; lifecycle root, not a time fact. |
| `work_items` | **Commitment** | Stored work intent with optional estimate/deadline facets. |
| `work_action_items` | **Commitment** | Pre-promotion obligation from capture/meeting extract. |
| `work_notes` | **Artifact** (intake) | Unstructured context until triaged; not ranked or reconciled. |
| `work_priority_policies` | **Commitment** (policy) | Weight vector only — scores are derived (ADR 0022). |

**Time ledger:** no Phase 1 tables (`work_time_entries` is WOS-3).

### 1.4 ID generation

- Surrogate integer PK: `INTEGER PRIMARY KEY AUTOINCREMENT` on every root table.
- Opaque, never reused, stable across soft-delete/archive.
- Natural keys (project name) are `UNIQUE` partial indexes, not PKs.
- External/import identity: provenance columns only (`capture_idempotency_key` on
  notes) — never primary keys.

### 1.5 Timestamps

| Field | Semantics |
|---|---|
| `created_at` | UTC ISO-8601 via `memory._connection.now()`. Immutable after insert. |
| `updated_at` | UTC ISO-8601; bumped on every UPDATE including soft-delete and archive. |
| `*_on` domain dates | Local calendar `TEXT 'YYYY-MM-DD'` supplied by producer (desktop/chat). Backend never derives local dates from UTC except documented migration backfill. |
| `archived_at` | UTC ISO-8601 when a **holding** enters archived terminal state. NULL = live. |
| `deleted_at` | UTC ISO-8601 when a **high-churn** row is soft-deleted. NULL = live. |

### 1.6 Optimistic concurrency / versioning

- **Mechanism:** `updated_at` compare on UPDATE (Finance precedent; Data Model §1.9).
- Writer reads row → client holds `updated_at` → UPDATE includes
  `WHERE id = ? AND updated_at = ? AND <live-row predicate>`.
- Zero rows updated → `409 Conflict` with fresh aggregate (IMPLEMENTATION_RISKS §5).
- **No `revision` column in Phase 1.** Add only if conflict rate warrants it (open
  question in Data Model §10).
- **No row-level history table.** Audit trail = `MutationEvent` payload + stream order.

### 1.7 Soft delete vs archive

| Pattern | Tables | Verb | Live-row predicate |
|---|---|---|---|
| **Archive** (holdings) | `work_projects` | `archive` | `archived_at IS NULL` |
| **Soft delete** (high churn) | `work_items`, `work_action_items`, `work_notes` | `delete` / dismiss | `deleted_at IS NULL` |
| **Status terminal** (no delete) | `work_notes` triaged | `triage` sets `status='triaged'` | inbox = `status='captured' AND deleted_at IS NULL` |
| **Policy supersede** | `work_priority_policies` | `update` in place | one active row per owner |

Hard `DELETE` is forbidden on user-facing paths (Handbook + ADR 0012 rollback story).

### 1.8 `MutationEvent` integration

- Every successful write emits exactly one `MutationEvent` via
  `runtime/mutation_builders.py` → `finalize_mutations()`.
- `entity` payload = full aggregate row as dict (Finance precedent).
- `metadata` carries invalidation routing ids only (`entity_id`, `project_id`,
  `owner_id`) — never business data, never derived values.
- Proposals (Brain structuring suggestions, triage hints) emit **nothing** until
  human commit.
- Composite promotion: `work.actionitem.promoted` carries both ActionItem and new
  WorkItem in `entity` (Finance transfer-pair precedent).

### 1.9 Derived fields — Phase 1 inventory (all **empty** in storage)

| Would-be derived value | Stored? | Phase 1 source |
|---|---|---|
| Priority score / rank | **No** | Computed from `work_items` + `work_priority_policies` + clock |
| Completion % | **No** | N/A (no milestones in Phase 1) |
| Health / momentum | **No** | WOS-8+ |
| `blocked` status | **No** | No dependencies in Phase 1 |
| Inbox count | **No** | `COUNT(*)` over live notes |
| Briefing narrative | **No** | Brain WOS-9+; Phase 1 = deterministic numbers only |

---

## 2. Entity relationship diagram (Phase 1)

```
┌─────────────────┐         ┌──────────────────────┐
│ work_priority_  │         │     work_projects     │  HOLDING
│    policies     │         │  (release_id NULL)      │
│ 1 active/owner  │         │  (engagement_id NULL)   │
└────────┬────────┘         └───────────┬────────────┘
         │ (read by projection)        │ 1
         │                             │
         │                             │ N
         │                   ┌─────────▼────────────┐
         │                   │     work_items        │  COMMITMENT
         │                   │  type='task' (P1)     │
         │                   │  parent_id NULL (P1)  │
         │                   └─────────▲────────────┘
         │                             │ 0..1
┌────────▼────────┐         ┌─────────┴────────────┐
│   work_notes    │──1:N──▶│  work_action_items   │  COMMITMENT
│   (capture)     │         │  (pre-promotion)     │
└─────────────────┘         └──────────────────────┘
         │
         └── triage outcome ──▶ work_items.id (via outcome_id when outcome_kind='work_item')
```

---

## 3. Table specifications

Conventions stated once: all tables require `PRAGMA foreign_keys = ON` (already enabled
in `memory/_connection.py` from Finance FIN-0). All FKs use default `ON DELETE RESTRICT`.
Partial indexes use `WHERE deleted_at IS NULL` or `WHERE archived_at IS NULL` as noted.

---

### 3.1 `work_notes`

#### Purpose
Frictionless unstructured capture (voice/chat/manual). Drives the decision: *what
loose thoughts need to become commitments today?* Visible in capture inbox until
triaged (Execution Model §13 input; Data Model N1/N2).

#### Ownership
| | |
|---|---|
| **Writer** | `memory/work/notes.py` |
| **Domain** | `domains/work/workspace/` (Capture context) |
| **Aggregate** | `Note` / `Capture |
| **Ledger** | Artifact (intake — not reconciled) |

#### Authoritative fields
| Column | Justification |
|---|---|
| `body` | The captured thought — sole user-provided truth. |
| `capture_source` | Provenance for trust analysis (`manual`/`chat`/`voice`). |
| `captured_on` | Local date bucket for inbox sorting and Briefing "today". |
| `status` | Inbox lifecycle (`captured` → `triaged` \| `archived`). |
| `outcome_kind` + `outcome_id` | Idempotent triage outcome pointer (N2 — link, not delete). |
| `capture_idempotency_key` | REST/voice retry dedup (IMPLEMENTATION_RISKS §10). |

#### Derived fields
**None stored.**

#### Column definitions

| Column | SQL type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | NO | — | |
| `owner_id` | INTEGER | NO | `1` | Owner scope (§1.1) |
| `body` | TEXT | NO | — | Trimmed non-empty (validation) |
| `capture_source` | TEXT | NO | — | CHECK IN `('manual','chat','voice')` — `import`/`email` added WOS-10 |
| `captured_on` | TEXT | NO | — | Local date `YYYY-MM-DD` |
| `status` | TEXT | NO | `'captured'` | CHECK IN `('captured','triaged','archived')` |
| `outcome_kind` | TEXT | YES | NULL | CHECK IN `('work_item','note','dismissed')` OR NULL; set on triage |
| `outcome_id` | INTEGER | YES | NULL | FK target depends on `outcome_kind`; NULL until triaged |
| `capture_idempotency_key` | TEXT | YES | NULL | Client-supplied; unique per owner when set |
| `source` | TEXT | NO | `'manual'` | CHECK IN `('manual','chat','voice','import','ai_committed')` — row entry provenance |
| `created_at` | TEXT | NO | — | UTC |
| `updated_at` | TEXT | NO | — | UTC; concurrency token |
| `deleted_at` | TEXT | YES | NULL | Soft delete (mis-capture correction) |

#### Foreign keys
- None enforced at DB layer for `outcome_id` (polymorphic — validated in service:
  `work_item` → `work_items.id`, `note` → self/filed note id).

#### Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_work_notes_inbox
    ON work_notes(owner_id, captured_on DESC, id DESC)
    WHERE status = 'captured' AND deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_work_notes_idempotency
    ON work_notes(owner_id, capture_idempotency_key)
    WHERE capture_idempotency_key IS NOT NULL AND deleted_at IS NULL;
```

#### Uniqueness
- `(owner_id, capture_idempotency_key)` when key present — duplicate POST returns
  existing row (idempotent capture).

#### Lifecycle
`captured → triaged | archived` (+ soft-delete for corrections).

#### Invariants
- **N1:** Inbox query returns only `status='captured'` live rows.
- **N2:** Triage sets `status='triaged'`, `outcome_kind`, `outcome_id` — never silent
  delete.
- **N3:** `body` non-empty after trim.
- **N4:** `captured_on` valid calendar date; not >1 day future (validation).
- **N5:** `outcome_kind`/`outcome_id` both NULL or both set; consistent pair.
- **N6:** UPDATE requires matching `updated_at` (§1.6).

#### Expected row counts
High churn — tens to hundreds active; unbounded history. Inbox typically <20 live
`captured` rows.

#### Migration notes
First `work_*` table in WOS-1 migration block. No backfill.

#### Future extension
- `import`, `email`, `slack` in `capture_source` CHECK (WOS-10).
- Optional `audio_transcript_ref` TEXT provenance — not body storage (Knowledge owns media).

#### Complete DDL
```sql
CREATE TABLE IF NOT EXISTS work_notes (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id                INTEGER NOT NULL DEFAULT 1,
    body                    TEXT    NOT NULL,
    capture_source          TEXT    NOT NULL
                            CHECK (capture_source IN ('manual','chat','voice')),
    captured_on             TEXT    NOT NULL,
    status                  TEXT    NOT NULL DEFAULT 'captured'
                            CHECK (status IN ('captured','triaged','archived')),
    outcome_kind            TEXT
                            CHECK (outcome_kind IS NULL OR outcome_kind IN ('work_item','note','dismissed')),
    outcome_id              INTEGER,
    capture_idempotency_key TEXT,
    source                  TEXT    NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at              TEXT    NOT NULL,
    updated_at              TEXT    NOT NULL,
    deleted_at              TEXT
);
```

---

### 3.2 `work_action_items`

#### Purpose
Extracted or hand-entered loop closure items awaiting promotion to the commitment
ledger. Drives: *what micro-commitments from capture should become tasks?*

#### Ownership
| | |
|---|---|
| **Writer** | `memory/work/action_items.py` |
| **Domain** | `domains/work/workspace/` |
| **Aggregate** | `ActionItem` |
| **Ledger** | Commitment (pre-promotion) |

#### Authoritative fields
| Column | Justification |
|---|---|
| `title` | The commitment text. |
| `status` | `open` → `promoted` \| `dismissed`. |
| `note_id` | Provenance link to originating capture (nullable for direct create). |
| `promoted_work_item_id` | Idempotent promotion target (MT1). |

#### Derived fields
**None stored.**

#### Column definitions

| Column | SQL type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | NO | — | |
| `owner_id` | INTEGER | NO | `1` | |
| `title` | TEXT | NO | — | Non-empty trimmed |
| `status` | TEXT | NO | `'open'` | CHECK IN `('open','promoted','dismissed')` |
| `note_id` | INTEGER | YES | NULL | FK → `work_notes(id)` |
| `promoted_work_item_id` | INTEGER | YES | NULL | FK → `work_items(id)`; set once on promote |
| `source` | TEXT | NO | `'manual'` | Provenance enum |
| `created_at` | TEXT | NO | — | UTC |
| `updated_at` | TEXT | NO | — | UTC; concurrency token |
| `deleted_at` | TEXT | YES | NULL | Soft delete |

#### Foreign keys
- `note_id` → `work_notes(id)`
- `promoted_work_item_id` → `work_items(id)`

#### Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_work_action_items_open
    ON work_action_items(owner_id, created_at DESC)
    WHERE status = 'open' AND deleted_at IS NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_work_action_items_promoted_target
    ON work_action_items(promoted_work_item_id)
    WHERE promoted_work_item_id IS NOT NULL AND deleted_at IS NULL;
```

#### Uniqueness
- One WorkItem per promotion (`promoted_work_item_id` unique when set).
- Idempotent promote: second call on `status='promoted'` is no-op returning same ids.

#### Lifecycle
`open → promoted | dismissed`.

#### Invariants
- **AI1:** `promoted_work_item_id` non-NULL iff `status='promoted'`.
- **AI2:** Promotion creates exactly one live `work_items` row and links it here (MT1).
- **AI3:** `dismissed` rows cannot promote without reopen (new row).
- **AI4:** `note_id`, when set, must reference a live note owned by same `owner_id`.
- **AI5:** Optimistic concurrency via `updated_at`.

#### Expected row counts
Moderate — single digits to low hundreds open; history retained.

#### Migration notes
Created after `work_notes` and before `work_items` (FK order). `promoted_work_item_id`
FK added in same migration after `work_items` exists — use two-step migration or
deferred FK (SQLite): create `work_action_items` without FK to `work_items`, then
`work_items`, then attach FK via table rebuild if strict FK required. **Recommended:**
create tables in dependency order in one `executescript` block (SQLite validates FKs
at statement end when all tables exist).

#### Future extension
- `meeting_id` INTEGER FK (WOS-10) — nullable; promotion key becomes
  `(meeting_id, action_item_id)`.

#### Complete DDL
```sql
CREATE TABLE IF NOT EXISTS work_action_items (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id                INTEGER NOT NULL DEFAULT 1,
    title                   TEXT    NOT NULL,
    status                  TEXT    NOT NULL DEFAULT 'open'
                            CHECK (status IN ('open','promoted','dismissed')),
    note_id                 INTEGER REFERENCES work_notes(id),
    promoted_work_item_id   INTEGER REFERENCES work_items(id),
    source                  TEXT    NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at              TEXT    NOT NULL,
    updated_at              TEXT    NOT NULL,
    deleted_at              TEXT
);
```

---

### 3.3 `work_projects`

#### Purpose
The core holding — a bounded body of work the founder tracks. Drives: *which
commitments belong together and which portfolio slot does this occupy?*

#### Ownership
| | |
|---|---|
| **Writer** | `memory/work/projects.py` |
| **Domain** | `domains/work/` (Work context) |
| **Aggregate** | `Project` |
| **Ledger** | Holding (position anchor) |

#### Authoritative fields
| Column | Justification |
|---|---|
| `name` | Identity + natural key (unique while live per owner). |
| `objective` | Why this project exists — Outcome facet; feeds Briefing context. |
| `status` | Lifecycle intent (`idea` … `archived`). **`blocked` excluded** — computed only. |
| `planned_start_on` / `planned_end_on` | Time facet for horizon decisions. |
| `release_id` / `engagement_id` | Nullable sockets for Phase 2/5 — avoid reshape. |

#### Derived fields
**None stored** (completion %, health, blocked — all computed later).

#### Column definitions

| Column | SQL type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | NO | — | |
| `owner_id` | INTEGER | NO | `1` | |
| `name` | TEXT | NO | — | Unique while live per owner |
| `objective` | TEXT | YES | NULL | Optional narrative |
| `status` | TEXT | NO | `'idea'` | CHECK IN `('idea','planned','active','paused','completed')` — **`blocked` forbidden** |
| `planned_start_on` | TEXT | YES | NULL | Local date |
| `planned_end_on` | TEXT | YES | NULL | Local date |
| `release_id` | INTEGER | YES | NULL | Socket — FK added Phase 2 |
| `engagement_id` | INTEGER | YES | NULL | Socket — FK added Phase 5 |
| `source` | TEXT | NO | `'manual'` | Provenance |
| `created_at` | TEXT | NO | — | UTC |
| `updated_at` | TEXT | NO | — | UTC; concurrency token |
| `archived_at` | TEXT | YES | NULL | Archive — holdings use archive not soft-delete |

#### Foreign keys
- Phase 1: none enforced (`release_id`, `engagement_id` are inert integers).

#### Indexes
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_projects_live_name
    ON work_projects(owner_id, name COLLATE NOCASE)
    WHERE archived_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_work_projects_active
    ON work_projects(owner_id, status)
    WHERE archived_at IS NULL;
```

#### Uniqueness
- Live project name unique per owner (case-insensitive).

#### Lifecycle
`idea → planned → active → (paused ⇄ active) → completed`; **`archived`** via
`archived_at` (terminal hidden state).

#### Invariants
- **P1:** Never hard-deleted.
- **P2:** `planned_end_on ≥ planned_start_on` when both set.
- **P3:** `completed` requires explicit transition; items may still be open (warn, not block in Phase 1).
- **P4:** Archived projects excluded from pickers and active projections.
- **P5:** `release_id`/`engagement_id` must be NULL in Phase 1 writes (service guard).
- **P6:** Optimistic concurrency via `updated_at`.

#### Expected row counts
Low — typically 3–20 live projects for a solo founder.

#### Migration notes
Seed optional `Inbox` or `Personal` default project is **deferred** — explicit user
create only in Phase 1 (no magic rows unless product demands later).

#### Future extension
- FK to `work_releases`, `work_engagements` when those tables ship.
- `product_id` path via Release chain (Phase 2).

#### Complete DDL
```sql
CREATE TABLE IF NOT EXISTS work_projects (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id            INTEGER NOT NULL DEFAULT 1,
    name                TEXT    NOT NULL,
    objective           TEXT,
    status              TEXT    NOT NULL DEFAULT 'idea'
                        CHECK (status IN ('idea','planned','active','paused','completed')),
    planned_start_on    TEXT,
    planned_end_on      TEXT,
    release_id          INTEGER,
    engagement_id       INTEGER,
    source              TEXT    NOT NULL DEFAULT 'manual'
                        CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL,
    archived_at         TEXT
);
```

---

### 3.4 `work_items`

#### Purpose
The atomic unit of work intent (Phase 1: flat tasks only). Drives: *what did I
commit to do, by when, with what estimated effort?*

#### Ownership
| | |
|---|---|
| **Writer** | `memory/work/items.py` |
| **Domain** | `domains/work/` (Work context) |
| **Aggregate** | `WorkItem` |
| **Ledger** | Commitment |

#### Authoritative fields
| Column | Justification |
|---|---|
| `project_id` | Hard owner (WI1). |
| `type` | Discriminator — Phase 1 service writes `'task'` only. |
| `title` | Commitment description. |
| `status` | Intent lifecycle — manual transitions in Phase 1. |
| `estimate_minutes` | Time facet — commitment load (integer). |
| `estimate_confidence` | WI6 — never a bare estimate without confidence. |
| `deadline_on` + `deadline_hardness` | Drives PriorityQueue deadline term + risk. |
| `parent_id` | Tree socket — NULL in Phase 1. |
| `action_item_id` | Promotion provenance (nullable). |

#### Derived fields
**None stored** (priority score, blocked, logged time, completion %).

#### Column definitions

| Column | SQL type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | NO | — | |
| `owner_id` | INTEGER | NO | `1` | Denormalized for owner-scoped lists |
| `project_id` | INTEGER | NO | — | FK → `work_projects(id)` |
| `parent_id` | INTEGER | YES | NULL | FK → `work_items(id)` — NULL Phase 1 |
| `type` | TEXT | NO | `'task'` | CHECK IN `('epic','story','task','subtask')` — Phase 1: `'task'` only |
| `title` | TEXT | NO | — | |
| `status` | TEXT | NO | `'backlog'` | CHECK IN `('backlog','todo','in_progress','in_review','done','cancelled')` — **`blocked` forbidden** |
| `estimate_minutes` | INTEGER | YES | NULL | CHECK NULL OR `estimate_minutes > 0` |
| `estimate_confidence` | TEXT | YES | NULL | CHECK NULL OR IN `('low','medium','high')`; required when estimate set (validation) |
| `deadline_on` | TEXT | YES | NULL | Local date |
| `deadline_hardness` | TEXT | YES | NULL | CHECK NULL OR IN `('hard','soft')`; required when deadline set |
| `action_item_id` | INTEGER | YES | NULL | FK → `work_action_items(id)` |
| `source` | TEXT | NO | `'manual'` | |
| `created_at` | TEXT | NO | — | UTC |
| `updated_at` | TEXT | NO | — | UTC; concurrency token |
| `deleted_at` | TEXT | YES | NULL | Soft delete |

#### Foreign keys
- `project_id` → `work_projects(id)`
- `parent_id` → `work_items(id)`
- `action_item_id` → `work_action_items(id)`

#### Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_work_items_project_live
    ON work_items(owner_id, project_id, status)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_work_items_deadline
    ON work_items(owner_id, deadline_on)
    WHERE deleted_at IS NULL AND deadline_on IS NOT NULL AND status NOT IN ('done','cancelled');

CREATE UNIQUE INDEX IF NOT EXISTS idx_work_items_action_item_origin
    ON work_items(action_item_id)
    WHERE action_item_id IS NOT NULL AND deleted_at IS NULL;
```

#### Uniqueness
- At most one live WorkItem per originating ActionItem.

#### Lifecycle
`backlog → todo → in_progress → in_review → done | cancelled` (+ soft-delete).

#### Invariants
- **WI1:** `project_id` references live (non-archived) project on create.
- **WI2:** Phase 1 — `type='task'` and `parent_id IS NULL` (service-enforced).
- **WI3:** `estimate_confidence` required when `estimate_minutes` set.
- **WI4:** `deadline_hardness` required when `deadline_on` set.
- **WI5:** `done`/`cancelled` are terminal for PriorityQueue open set.
- **WI6:** `owner_id` matches project's `owner_id`.
- **WI7:** Optimistic concurrency via `updated_at`.

#### Expected row counts
Primary churn table — hundreds to low thousands live; scales with daily use.

#### Migration notes
None.

#### Future extension
- Hierarchy (parent chain, type ladder validation) — Phase 2.
- `milestone_id`, `sprint` links — Phase 2/3.
- `import_source` + `external_id` provenance TEXT pair — WOS-10.

#### Complete DDL
```sql
CREATE TABLE IF NOT EXISTS work_items (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id                INTEGER NOT NULL DEFAULT 1,
    project_id              INTEGER NOT NULL REFERENCES work_projects(id),
    parent_id               INTEGER REFERENCES work_items(id),
    type                    TEXT    NOT NULL DEFAULT 'task'
                            CHECK (type IN ('epic','story','task','subtask')),
    title                   TEXT    NOT NULL,
    status                  TEXT    NOT NULL DEFAULT 'backlog'
                            CHECK (status IN ('backlog','todo','in_progress','in_review','done','cancelled')),
    estimate_minutes        INTEGER CHECK (estimate_minutes IS NULL OR estimate_minutes > 0),
    estimate_confidence     TEXT    CHECK (estimate_confidence IS NULL OR estimate_confidence IN ('low','medium','high')),
    deadline_on             TEXT,
    deadline_hardness       TEXT    CHECK (deadline_hardness IS NULL OR deadline_hardness IN ('hard','soft')),
    action_item_id          INTEGER REFERENCES work_action_items(id),
    source                  TEXT    NOT NULL DEFAULT 'manual'
                            CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at              TEXT    NOT NULL,
    updated_at              TEXT    NOT NULL,
    deleted_at              TEXT
);
```

---

### 3.5 `work_priority_policies`

#### Purpose
The **only stored priority artifact** — tunable weights for the deterministic
PriorityQueue. Drives: *how should deadline urgency vs staleness decay be weighted
when ranking today's work?*

#### Ownership
| | |
|---|---|
| **Writer** | `memory/work/priority_policies.py` |
| **Domain** | `domains/work/planning/` |
| **Aggregate** | `PriorityPolicy` |
| **Ledger** | Commitment (policy weights — not scores) |

#### Authoritative fields
| Column | Justification |
|---|---|
| `deadline_weight` | Phase 1 priority term — days-to-deadline factor. |
| `decay_weight` | Phase 1 priority term — staleness since last activity. |
| `is_active` | PP2 — one active policy per owner. |

#### Derived fields
**None.** Priority scores and queue order are computed on read.

#### Column definitions

| Column | SQL type | Null | Default | Notes |
|---|---|---|---|---|
| `id` | INTEGER PK AUTOINCREMENT | NO | — | |
| `owner_id` | INTEGER | NO | `1` | |
| `deadline_weight` | INTEGER | NO | `1000` | CHECK `>= 0` — relative weight, not a score |
| `decay_weight` | INTEGER | NO | `100` | CHECK `>= 0` |
| `is_active` | INTEGER | NO | `1` | 0/1 boolean |
| `source` | TEXT | NO | `'manual'` | |
| `created_at` | TEXT | NO | — | UTC |
| `updated_at` | TEXT | NO | — | UTC; concurrency token |

**Deliberately absent in Phase 1:** `strategic_weight`, `revenue_weight`,
`blocking_weight`, `effort_weight` — unused until Phase 4 full prioritization;
add columns then (additive migration), not zero columns "for later."

#### Foreign keys
None.

#### Indexes
```sql
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_priority_policies_active_owner
    ON work_priority_policies(owner_id)
    WHERE is_active = 1;
```

#### Uniqueness
- One `is_active=1` row per `owner_id`.

#### Lifecycle
`active` — updated in place; each weight change emits `work.priority.reweighted`.

#### Invariants
- **PP1:** Weights non-negative (CHECK + validation).
- **PP2:** Exactly one active policy per owner (unique partial index + seed).
- **PP3:** No score/rank columns — ever (governance linter).
- **PP4:** Optimistic concurrency via `updated_at`.

#### Expected row counts
**1 live row per owner** (+ historical inactive rows if policy versioning added later).

#### Migration notes
Seed default policy idempotently in `memory/work/seed.py`:
`deadline_weight=1000`, `decay_weight=100`, `is_active=1` — only if no active policy
exists for owner `1`.

#### Future extension
- Additional weight columns Phase 4 (additive ALTER / migration block).
- Version history table **not** required — MutationEvent audit suffices.

#### Complete DDL
```sql
CREATE TABLE IF NOT EXISTS work_priority_policies (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id            INTEGER NOT NULL DEFAULT 1,
    deadline_weight     INTEGER NOT NULL DEFAULT 1000 CHECK (deadline_weight >= 0),
    decay_weight        INTEGER NOT NULL DEFAULT 100  CHECK (decay_weight >= 0),
    is_active           INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
    source              TEXT    NOT NULL DEFAULT 'manual'
                        CHECK (source IN ('manual','chat','voice','import','ai_committed')),
    created_at          TEXT    NOT NULL,
    updated_at          TEXT    NOT NULL
);
```

---

## 4. Phase 1 index bundle (idempotent)

```sql
-- work_notes
CREATE INDEX IF NOT EXISTS idx_work_notes_inbox
    ON work_notes(owner_id, captured_on DESC, id DESC)
    WHERE status = 'captured' AND deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_notes_idempotency
    ON work_notes(owner_id, capture_idempotency_key)
    WHERE capture_idempotency_key IS NOT NULL AND deleted_at IS NULL;

-- work_action_items
CREATE INDEX IF NOT EXISTS idx_work_action_items_open
    ON work_action_items(owner_id, created_at DESC)
    WHERE status = 'open' AND deleted_at IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_action_items_promoted_target
    ON work_action_items(promoted_work_item_id)
    WHERE promoted_work_item_id IS NOT NULL AND deleted_at IS NULL;

-- work_projects
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_projects_live_name
    ON work_projects(owner_id, name COLLATE NOCASE)
    WHERE archived_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_work_projects_active
    ON work_projects(owner_id, status)
    WHERE archived_at IS NULL;

-- work_items
CREATE INDEX IF NOT EXISTS idx_work_items_project_live
    ON work_items(owner_id, project_id, status)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_work_items_deadline
    ON work_items(owner_id, deadline_on)
    WHERE deleted_at IS NULL AND deadline_on IS NOT NULL
      AND status NOT IN ('done','cancelled');
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_items_action_item_origin
    ON work_items(action_item_id)
    WHERE action_item_id IS NOT NULL AND deleted_at IS NULL;

-- work_priority_policies
CREATE UNIQUE INDEX IF NOT EXISTS idx_work_priority_policies_active_owner
    ON work_priority_policies(owner_id)
    WHERE is_active = 1;
```

**Deliberately no index** on computed priority, health, or inbox counts.

---

## 5. Repository interfaces (ports — `domains/work/repositories.py`)

Pure protocols; implementations in `domains/work/repository_adapters.py` calling
`memory/work/*`. No SQL in domain.

### 5.1 `NoteRepository`
```python
get_note_by_id(note_id: int, owner_id: int) -> NoteRow | None
list_capture_inbox(owner_id: int, limit: int) -> list[NoteRow]
insert_note(row: NoteInsert) -> NoteRow
triage_note(note_id: int, owner_id: int, expected_updated_at: str, outcome: TriageOutcome) -> NoteRow
soft_delete_note(note_id: int, owner_id: int, expected_updated_at: str) -> NoteRow
find_by_idempotency_key(owner_id: int, key: str) -> NoteRow | None
```

### 5.2 `ActionItemRepository`
```python
get_action_item_by_id(item_id: int, owner_id: int) -> ActionItemRow | None
list_open_action_items(owner_id: int, limit: int) -> list[ActionItemRow]
insert_action_item(row: ActionItemInsert) -> ActionItemRow
mark_promoted(item_id: int, owner_id: int, expected_updated_at: str, work_item_id: int) -> ActionItemRow
mark_dismissed(item_id: int, owner_id: int, expected_updated_at: str) -> ActionItemRow
```

### 5.3 `ProjectRepository`
```python
get_project_by_id(project_id: int, owner_id: int) -> ProjectRow | None
list_live_projects(owner_id: int) -> list[ProjectRow]
insert_project(row: ProjectInsert) -> ProjectRow
update_project(project_id: int, owner_id: int, expected_updated_at: str, patch: ProjectPatch) -> ProjectRow
archive_project(project_id: int, owner_id: int, expected_updated_at: str) -> ProjectRow
complete_project(project_id: int, owner_id: int, expected_updated_at: str) -> ProjectRow
find_live_by_name(owner_id: int, name: str) -> ProjectRow | None
```

### 5.4 `WorkItemRepository`
```python
get_work_item_by_id(item_id: int, owner_id: int) -> WorkItemRow | None
list_live_items_for_project(project_id: int, owner_id: int) -> list[WorkItemRow]
list_open_commitments(owner_id: int) -> list[WorkItemRow]  # PriorityQueue input
insert_work_item(row: WorkItemInsert) -> WorkItemRow
update_work_item(item_id: int, owner_id: int, expected_updated_at: str, patch: WorkItemPatch) -> WorkItemRow
transition_work_item(item_id: int, owner_id: int, expected_updated_at: str, to_status: str) -> WorkItemRow
soft_delete_work_item(item_id: int, owner_id: int, expected_updated_at: str) -> WorkItemRow
find_by_action_item_id(action_item_id: int, owner_id: int) -> WorkItemRow | None
```

### 5.5 `PriorityPolicyRepository`
```python
get_active_policy(owner_id: int) -> PriorityPolicyRow
update_policy_weights(owner_id: int, expected_updated_at: str, deadline_weight: int, decay_weight: int) -> PriorityPolicyRow
ensure_default_policy(owner_id: int) -> PriorityPolicyRow  # seed — idempotent
```

---

## 6. Service interfaces (domain — `domains/work/`)

Services accept clock-injected `now: datetime` and ports; return aggregates + build
`MutationEvent`s via `mutations.py` pure builders.

### 6.1 `CaptureService` (`workspace/`)
| Method | Decision driven |
|---|---|
| `capture_note(body, source, captured_on, idempotency_key?, …)` | Log a thought without filing friction |
| `triage_to_task(note_id, project_id, task_fields, …)` | Turn capture into commitment |
| `triage_to_dismiss(note_id, …)` | Clear inbox without losing audit trail |
| `create_action_item(title, note_id?, …)` | Explicit micro-commitment |

### 6.2 `ProjectService` (`delivery/` or work root)
| Method | Decision driven |
|---|---|
| `create_project(name, objective?, dates?, …)` | Start tracking a body of work |
| `update_project(…)` | Correct intent/plan |
| `archive_project(…)` | Stop investing attention in a holding |
| `complete_project(…)` | Close a chapter |

### 6.3 `WorkItemService`
| Method | Decision driven |
|---|---|
| `create_task(project_id, title, estimate?, deadline?, …)` | Record a commitment |
| `update_task(…)` | Adjust intent before reality diverges |
| `transition_task(to_status, …)` | Mark progress honestly |
| `cancel_task(…)` | Explicitly abandon commitment |

### 6.4 `PromotionService` (`workspace/`)
| Method | Decision driven |
|---|---|
| `promote_action_item(action_item_id, project_id, …)` | MT1 idempotent ActionItem → WorkItem |

### 6.5 `PriorityPolicyService` (`planning/`)
| Method | Decision driven |
|---|---|
| `get_active_policy(owner_id)` | Read weights for queue |
| `reweight(deadline_weight, decay_weight, …)` | Tune what "matters" means |

### 6.6 `PrioritizationAssembler` (`planning/prioritization.py`) — **pure, no I/O**
| Function | Decision driven |
|---|---|
| `build_priority_queue(items, policy, now) -> PriorityQueueDTO` | **What should I work on today?** |

### 6.7 `BriefingAssembler` (`insights/`) — **pure, no I/O, no Brain**
| Function | Decision driven |
|---|---|
| `build_briefing_shell(queue, inbox_count, open_commitment_count, now) -> BriefingDTO` | Morning Brief v0 numbers |

---

## 7. API contracts (`services/api/routers/work/`)

Thin HTTP → planner/domain. All writes return `{ events: MutationEvent[], … }`.
Reads return projection DTOs. All routes scoped to v1 single owner (implicit `owner_id=1`).

| Method | Path | Body / params | Response | Write |
|---|---|---|---|---|
| POST | `/work/captures` | `{ body, capture_source, captured_on, idempotency_key? }` | `NoteDTO` + events | `work.note.captured` |
| POST | `/work/captures/{id}/triage/task` | `{ project_id, title, estimate_minutes?, …, updated_at }` | `WorkItemDTO` + events | `work.note.triaged` + `work.item.created` |
| POST | `/work/captures/{id}/triage/dismiss` | `{ updated_at }` | `NoteDTO` + events | `work.note.triaged` |
| GET | `/work/captures/inbox` | — | `NoteDTO[]` | — |
| POST | `/work/action-items` | `{ title, note_id? }` | `ActionItemDTO` + events | `work.actionitem.created` |
| POST | `/work/action-items/{id}/promote` | `{ project_id, …, updated_at }` | `WorkItemDTO` + events | `work.actionitem.promoted` (composite) |
| POST | `/work/action-items/{id}/dismiss` | `{ updated_at }` | `ActionItemDTO` + events | `work.actionitem.dismissed` |
| GET | `/work/projects` | — | `ProjectDTO[]` | — |
| POST | `/work/projects` | `{ name, objective?, … }` | `ProjectDTO` + events | `work.project.created` |
| PATCH | `/work/projects/{id}` | `{ …, updated_at }` | `ProjectDTO` + events | `work.project.updated` |
| POST | `/work/projects/{id}/archive` | `{ updated_at }` | `ProjectDTO` + events | `work.project.archived` |
| POST | `/work/projects/{id}/complete` | `{ updated_at }` | `ProjectDTO` + events | `work.project.completed` |
| GET | `/work/projects/{id}/items` | — | `WorkItemDTO[]` | — |
| POST | `/work/items` | `{ project_id, title, … }` | `WorkItemDTO` + events | `work.item.created` |
| PATCH | `/work/items/{id}` | `{ …, updated_at }` | `WorkItemDTO` + events | `work.item.updated` |
| POST | `/work/items/{id}/transition` | `{ to_status, updated_at }` | `WorkItemDTO` + events | `work.item.transitioned` |
| DELETE | `/work/items/{id}` | `{ updated_at }` | events | `work.item.deleted` |
| GET | `/work/priority/queue` | `?limit=` | `PriorityQueueDTO` | — |
| GET | `/work/briefing/today` | — | `BriefingDTO` | — |
| GET | `/work/priority/policy` | — | `PriorityPolicyDTO` | — |
| PATCH | `/work/priority/policy` | `{ deadline_weight, decay_weight, updated_at }` | `PriorityPolicyDTO` + events | `work.priority.reweighted` |

**409** on stale `updated_at`. **404** on missing/non-owned rows.

Chat/voice parity: mirror verbs in `services/planner/work_commands.py` +
`work_queries.py` + `work_serializers.py`.

---

## 8. Event contracts (Phase 1)

All events: `MutationEvent(event_type, entity_type, operation, entity, metadata)`.

| `event_type` | entity_type | operation | When | Memory producer |
|---|---|---|---|---|
| `work.note.captured` | `note` | `capture` | Note inserted | No (routine churn) |
| `work.note.triaged` | `note` | `triage` | Inbox resolved | No |
| `work.actionitem.created` | `action_item` | `create` | ActionItem inserted | No |
| `work.actionitem.promoted` | `action_item` | `promote` | Promotion committed | No |
| `work.actionitem.dismissed` | `action_item` | `dismiss` | Dismissed | No |
| `work.project.created` | `project` | `create` | Project inserted | **Yes** — durable fact |
| `work.project.updated` | `project` | `update` | Project patched | No |
| `work.project.archived` | `project` | `archive` | Archived | No |
| `work.project.completed` | `project` | `complete` | Completed | **Yes** — milestone |
| `work.item.created` | `work_item` | `create` | Task inserted | No |
| `work.item.updated` | `work_item` | `update` | Task patched | No |
| `work.item.transitioned` | `work_item` | `transition` | Status change | No |
| `work.item.completed` | `work_item` | `complete` | Transition to `done` | No |
| `work.item.cancelled` | `work_item` | `cancel` | Transition to `cancelled` | No |
| `work.item.deleted` | `work_item` | `delete` | Soft delete | No |
| `work.priority.reweighted` | `priority_policy` | `reweight` | Weights changed | No |

**Composite promotion event** (`work.actionitem.promoted`):
```json
{
  "entity": {
    "action_item": { "...full row..." },
    "work_item": { "...full row..." }
  },
  "metadata": { "entity_id": "<action_item.id>", "project_id": "<project.id>", "owner_id": 1 }
}
```

Desktop: each event maps in `invalidation-map.ts` to
`['nova','work','captures']`, `['nova','work','projects']`, `['nova','work','priority']`,
`['nova','work','briefing','today']`.

---

## 9. Transaction boundaries

| Operation | Tables touched | Events | Atomicity |
|---|---|---|---|
| Capture note | `work_notes` | 1 | Single row |
| Triage → task | `work_notes`, `work_items` | 2 (or orchestrated 1+1 sequential finalize) | **One DB transaction** |
| Promote action item | `work_action_items`, `work_items` | 1 composite | **One DB transaction** |
| Create task | `work_items` | 1 | Single row |
| Reweight policy | `work_priority_policies` | 1 | Single row |
| Archive project | `work_projects` | 1 | Single row — items stay live (warn in UI) |

**Rule:** multi-row orchestrations emit one composite event OR sequential events in
one transaction — never partial state without rollback. Finance transfer-pair precedent.

**Forbidden:** writing PriorityQueue results, briefing scores, or inbox counts back
to SQLite.

---

## 10. Read models & projection ownership

| Projection | Owner module | Storage | Phase 1 formula (deterministic) |
|---|---|---|---|
| **CaptureInbox** | `domains/work/workspace/` | None | Live `work_notes` where `status='captured'` |
| **OpenCommitments** | `domains/work/` | None | Live `work_items` not in `done`/`cancelled` |
| **PriorityQueue** | `domains/work/planning/prioritization.py` | None | Per item: `deadline_term = f(days_to_deadline, hardness) * deadline_weight` + `decay_term = g(idle_days_since updated_at) * decay_weight` — **no strategic/revenue/blocking terms** |
| **BriefingShell** | `domains/work/insights/briefing.py` | None | Top N queue items + inbox count + open commitment count + overdue hard-deadline count — **numbers only, no Brain** |
| **ProjectList** | `domains/work/` | None | Live non-archived projects |

**Facade** (`services/api/projections/work_briefing.py`): optional thin wrapper if
Insights assembler needs API-specific DTO shaping — **no new tables**.

Cross-domain projections (ROI, Calendar, Finance): **not Phase 1**.

---

## 11. Validation rules (business layer)

### Notes
1. `body` non-empty after trim.
2. `capture_source` and `source` from closed enums.
3. `captured_on` valid date; ≤ today+1 day.
4. Idempotency key: if duplicate, return existing row (no second event).
5. Triage only from `status='captured'`.

### Action items
1. `title` non-empty.
2. Promote only from `status='open'`.
3. Idempotent promote if already `promoted` with same work item.

### Projects
1. `name` unique among live projects per owner (case-insensitive).
2. Date range validity (P2).
3. Cannot create items under archived project.

### Work items
1. Phase 1: `type='task'`, `parent_id IS NULL`.
2. Estimate/confidence pairing (WI3).
3. Deadline/hardness pairing (WI4).
4. Status transitions from closed set; no `blocked`.
5. `project_id` live and not archived on create.

### Priority policy
1. Weights ≥ 0 (PP1).
2. Seed ensures exactly one active policy before first queue read.

### Universal (every write)
1. Optimistic concurrency — stale `updated_at` → 409.
2. Soft-delete/archive only — no hard delete.
3. No column from `FORBIDDEN_DERIVED_COLUMNS` accepted in writers.
4. `owner_id` consistency across linked rows.

---

## 12. Migration order

Execute in **`memory/work/migrations.py`** as `migrate_work_phase1(con)` — idempotent,
called from `memory/schema.py` after Phase 0 governance hook.

```
Step 1 — CREATE TABLE work_notes
Step 2 — CREATE TABLE work_projects
Step 3 — CREATE TABLE work_items          (FK work_projects)
Step 4 — CREATE TABLE work_action_items   (FK work_notes, work_items)
Step 5 — CREATE TABLE work_priority_policies
Step 6 — CREATE INDEX bundle (§4)
Step 7 — seed.ensure_default_priority_policy(owner_id=1)
Step 8 — verify_work_table_governance(con)  (Phase 0 linter — owner_id + no forbidden cols)
```

**Schema version:** bump app constant `WORK_SCHEMA_VERSION = 1` in `memory/work/__init__.py`
(or shared meta); desktop/backend negotiate minimum version before write (IMPLEMENTATION_RISKS §12).

**Rollback:** forward-only; restore SQLite backup (ADR 0012). No DROP in migration.

---

## 13. Test plan

### 13.1 Schema / governance tests (architecture)
| Test | Asserts |
|---|---|
| `test_work_phase1_ddl_has_owner_id` | Every CREATE in `migrate_work_phase1` includes `owner_id` |
| `test_work_phase1_no_forbidden_columns` | `assert_migration_source_governance` passes |
| `test_work_phase1_fk_integrity` | `PRAGMA foreign_key_check` clean after migration on temp DB |

### 13.2 Memory integration tests (real SQLite — `tmp_path`)
| Test | Asserts |
|---|---|
| `test_capture_idempotency_key` | Duplicate key returns same row, one event worth of state |
| `test_promote_action_item_idempotent` | Second promote is no-op; one WorkItem |
| `test_project_name_unique_live` | Case-insensitive conflict on second create |
| `test_work_item_estimate_confidence_pairing` | Reject estimate without confidence |
| `test_soft_delete_excludes_from_open_commitments` | Deleted item absent from queue input query |
| `test_priority_policy_singleton_seed` | Double seed → one active row |
| `test_optimistic_concurrency_conflict` | Stale `updated_at` update affects 0 rows |

### 13.3 Domain / pure tests
| Test | Asserts |
|---|---|
| `test_priority_queue_deadline_ordering` | Earlier hard deadline ranks higher |
| `test_priority_queue_decay` | Stale item ranks higher than fresh with same deadline |
| `test_priority_queue_no_stored_scores` | Assembler output not written anywhere |
| `test_briefing_shell_counts` | Deterministic counts from fixture rows |

### 13.4 Mutation / parity tests
| Test | Asserts |
|---|---|
| `test_work_note_captured_event_shape` | `entity_type=note`, frozen MutationEvent fields |
| `test_chat_voice_capture_parity` | Same capture via REST and planner → identical row + event |
| `test_promote_composite_event` | Single event carries both aggregates |

### 13.5 Regression guards
| Test | Asserts |
|---|---|
| `test_domains_work_no_finance_import` | Architecture boundary |
| `test_no_priority_score_column` | PRAGMA table_info on all work_* tables |

---

## 14. Phase 1 exit criteria (schema gate → implementation gate)

Before WOS-1 code merges:

1. This document reviewed and frozen (human sign-off).
2. `migrate_work_phase1` DDL reviewed against §3–§4 — no derived columns.
3. Event table (§8) appended to `DESKTOP_WRITE_OPERATIONS.md` in the WOS-1 PR.
4. `entity_type` values registered in `domains/work/value_objects.py` if new nouns added.
5. Desktop `invalidation-map.ts` entries drafted (can land with WOS-1 desktop slice).
6. All §13 tests green with real SQLite.

---

## 15. Risks pinned at schema time

| Risk | Mitigation in this schema |
|---|---|
| Owner scoping retrofit (Risks §1) | `owner_id NOT NULL DEFAULT 1` on every table + index prefix |
| Derived column leakage (Risks §2) | Explicit forbidden list; no score/health/completion columns |
| Capture idempotency (Risks §10) | `capture_idempotency_key` unique partial index |
| Promotion duplication (MT1) | `promoted_work_item_id` unique; `action_item_id` unique on WorkItem |
| Optimistic clobber (Risks §5) | `updated_at` compare documented §1.6 |
| Policy mistaken for score (ADR 0022) | Only weight columns; queue always computed |

---

## 16. Final recommendation

**Implement exactly five tables.** Do not add `work_mutation_events`, `work_commands`,
or `work_projection_checkpoint` to SQLite — they violate the Finance template and
frozen runtime architecture.

**WOS-1 implementation order:** migration (§12) → memory writers → repository
adapters → domain services + mutation builders → planner parity → API routers →
pure prioritization/briefing assemblers → desktop shell.

With human sign-off on this document, the schema gate is closed and WOS-1 feature
work may begin.
