# Nova — Master Plan · Program Control Center

**The single entry point to the entire repository. Read this first, before any other document.**

This file answers four questions and nothing else:

1. **Where are we?** → [§1 Current Focus](#1-current-focus) · [§13 Current Sprint](#13-current-sprint)
2. **What is already done?** → [§10 Program Timeline](#10-program-timeline) · [§11 Completed Milestones](#11-completed-milestones)
3. **What are we building now?** → [§13 Current Sprint](#13-current-sprint)
4. **What comes next?** → [§14 Upcoming Sprints](#14-upcoming-sprints) · [§9 Release Roadmap](#9-release-roadmap)

It is a **navigation hub, not a specification.** It never restates architecture,
product, or plans — it links to the document that owns them. If this file and an
owned document disagree, **the owned document wins** and this file is stale — fix it.

> **Status:** Living · **Owner:** Program lead · **Last updated:** 2026-07-07
> **Current phase:** WorkOS implementation — Phase 1 (Capture + Commitment ledger + Brief) backend landed
> **How this file is kept honest:** [§27 Maintenance Contract](#27-maintenance-contract)

### How to read this in under 10 minutes

| Part | Sections | Read it to learn |
|---|---|---|
| **I · At a Glance** | [1–4](#1-current-focus) | Today's state, health, and metrics |
| **II · The Program** | [5–9](#5-vision) | What Nova is and how its domains fit together |
| **III · Where We Are** | [10–14](#10-program-timeline) | History, roadmap, and what's in flight |
| **IV · Decisions & Risk** | [15–19](#15-adr-status) | What's decided, pending, deferred, and risky |
| **V · Authority & Navigation** | [20–26](#20-frozen-design-stack) | Which documents are authoritative and where everything lives |

---

# PART I · AT A GLANCE

## 1. Current Focus

> **The first thing to read. What is happening *right now*.**

| | |
|---|---|
| **Current program** | WorkOS (Nova's second full domain) |
| **Current domain** | `domains/work` + `memory/work` |
| **Current phase** | Phase 1 — Capture + Commitment ledger + Morning Brief shell (backend landed) |
| **Current sprint** | WOS-1: five-table Commitment/Capture spine, deterministic PriorityQueue + Brief, REST + planner parity layer (chat/voice-ready) |
| **Current PR / work unit** | WOS-1 backend on `develop` |
| **Current blocker** | None |
| **Next PR / work unit** | WOS-1 desktop slice (Work section, Capture ⌘N, Today lens, invalidation-map) |
| **Next milestone** | **Phase 2** — Delivery graph (Products, Releases, Projects, WorkItem tree) |
| **Current success metric** | Phase 1 gate: architecture tests pass, no derived columns, real-SQLite tests, CI green |

Full detail → [§13 Current Sprint](#13-current-sprint).

---

## 2. Executive Summary

| | |
|---|---|
| **Current phase** | WorkOS implementation — **Phase 1: Capture + Commitment ledger + Brief (backend landed)** |
| **Design status** | ✅ Frozen — architecture, data, execution, product, UI/UX all complete |
| **Finance domain** | ✅ Complete — first fully-built domain (backend + API + desktop + planner) |
| **WorkOS design** | ✅ Frozen — 6 specs + 3 ADRs + 5 implementation companions |
| **Current sprint** | WOS-1 — five-table spine, memory writers, ports/adapters, domain services, deterministic PriorityQueue + Brief, REST + chat parity |
| **Current milestone** | WOS-1 backend: capture → triage → promote; Commitment ledger; Morning Brief v0 |
| **Next milestone** | **Phase 2** — Delivery graph (Products, Releases, Projects, WorkItem tree) |
| **Overall** | Design **100%** · Finance **100%** · WorkOS build **~13%** (Phase 1 backend of 11 landed) |

**One-line status:** The architecture and product are frozen; Finance shipped as the
proving domain; WorkOS Phase 0 is committed and Phase 1's backend (capture, Commitment
ledger, deterministic Brief) has landed — the next unit of work is the WOS-1 desktop
slice, then Phase 2's delivery graph.

---

## 3. Success Dashboard

```
Architecture & ADRs      ██████████ 100%   frozen, 24/24 accepted
Product & UX design      ██████████ 100%   Build Bible + 6 WorkOS specs frozen
Finance domain           ██████████ 100%   backend + API + desktop + planner
WorkOS design            ██████████ 100%   specs + ADRs + companions
WorkOS implementation    ██░░░░░░░░  ~13%   Phase 1 backend of 11 landed
  ├─ Phase 0 infra       ██████████  100%   committed (edges, money VO, governance)
  ├─ Phase 1 backend     ██████████  100%   spine + services + PriorityQueue + Brief + REST/planner parity
  └─ Phases 2–10         ░░░░░░░░░░   0%    not started
Testing (WorkOS)         ████░░░░░░  ~35%   governance + memory + pure + API/parity (29 tests)
Desktop UI (WorkOS)      ░░░░░░░░░░   0%    WOS-1 desktop slice pending
```

*Finance carries full test + desktop coverage; the bars above track the **WorkOS**
program, which is the active work.*

---

## 4. Repository Metrics

> **Repository health dashboard. Refresh the counts each sprint (§27).**
> Counts as of 2026-07-07.

| Metric | Value | Source of truth |
|---|---|---|
| ADRs (all Accepted) | **24** | [docs/adr/](adr/README.md) |
| Frozen design documents | **11** | [§20 Frozen Design Stack](#20-frozen-design-stack) |
| Architecture specs | 8 | [docs/architecture/](architecture/) |
| WorkOS companion docs | 6 | [docs/workos/](workos/) |
| Product/program domains | **2** built-or-active (Finance ✅, WorkOS 🔨) | [§7 Domain Status Board](#7-domain-status-board) |
| Backend services | **7** (api, automation, brain, calendar, knowledge, planner, voice) | [apps/backend/services/](../apps/backend/services/) |
| Backend test files | 19 | [apps/backend/tests/](../apps/backend/tests/) |
| Test functions (approx) | ~174 | `grep def test_` |
| Coverage gate | Not gated — CI enforces black/isort/flake8/mypy/check_limits/pytest | [CLAUDE.md](../CLAUDE.md) |
| Current active phase | WorkOS **Phase 1** (backend landed) | [§13 Current Sprint](#13-current-sprint) |
| Completed phases | Nova Core M0–M4 + Finance domain · WorkOS: Phase 0 done, Phase 1 backend landed | [§11 Completed Milestones](#11-completed-milestones) |

---

# PART II · THE PROGRAM

## 5. Vision

Nova is **a personal operating system that earns the right to tell you what to do
next** — across money, work, and life — by being more honest than your memory and
more disciplined than your spreadsheet.

The user is a founder (often solo) running a portfolio: products, clients, goals, and
a finite number of hours. Nova's job is to **reduce the number of decisions they must
make alone** while **never making a decision for them they did not approve**.

> **Ground truth in ledgers. Meaning in derivation. Trust in explanation.**

Nova is local-first, voice-capable, and explainable by default: every ranking,
estimate, and forecast carries its reasons and its confidence.

**Read the vision in full:**
- [Build Bible](BUILD_BIBLE.md) — the *why* and the product convictions
- [WorkOS Product Spec](NOVA_WORKOS_PRODUCT_SPEC_v1.md) — *what* to build
- [WorkOS Product Experience](NOVA_WORKOS_PRODUCT_EXPERIENCE_v1.md) — the felt experience
- [WorkOS UI/UX Specification](NOVA_WORKOS_UI_UX_SPECIFICATION_v1.md) — the screens

---

## 6. Program Hierarchy

The complete Nova program. Each pillar names its status, its owning document, and
what it depends on. "Built" = shipped; "Active" = current work; "Adapter/leaf" =
service package exists but domain-depth deferred; "Planned/Deferred" = not started.

```
Nova Program
├── Core Platform     ✅ Built      memory · runtime · brain (composition root)
├── Finance           ✅ Built      first full domain
├── WorkOS            🔨 Active     second full domain (Phase 0)
├── Knowledge         🟡 Adapter    service leaf; WorkOS depth deferred → Phase 10
├── Calendar          🟡 Adapter    service leaf; port injected → Phase 3
├── Automation        🟡 Scaffold   service package; depth deferred
├── AI (Chief of Staff) 🟡 Partial  Brain is built; propose/commit agent deferred → Phase 9
├── Desktop           ✅ Built      Electron; Finance UI shipped, WorkOS UI → Phase 1
├── Mobile            ⬜ Planned    not started
├── Cloud / Sync      ⬜ Deferred   local-first today; hosting model an open decision
└── Enterprise / Teams ⬜ Deferred  `owner_id` reserved; multi-user is post-v1
```

| Pillar | Status | Owner document | Impl. status | Depends on |
|---|---|---|---|---|
| Core Platform | ✅ Frozen & built | [Core Runtime Spec](architecture/NOVA_CORE_RUNTIME_SPECIFICATION_v1.md) | Production | — |
| Finance | ✅ Built | [FINANCE_DOMAIN.md](architecture/FINANCE_DOMAIN.md) | Complete | Core |
| WorkOS | 🔨 Active | [WorkOS Product Spec](NOVA_WORKOS_PRODUCT_SPEC_v1.md) | Phase 0 | Core |
| Knowledge | 🟡 Adapter | [AI_CONTRACTS.md](architecture/AI_CONTRACTS.md) | Service leaf | Core, WorkOS |
| Calendar | 🟡 Adapter | [ADR 0018](adr/0018-voice-first-interaction.md) | Service leaf | Core |
| Automation | 🟡 Scaffold | [Engineering Spec](architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md) | Package only | Core |
| AI / Chief of Staff | 🟡 Partial | [ADR 0002](adr/0002-tiered-three-model-ai-architecture.md) | Brain built | WorkOS Ph. 4–8 |
| Desktop | ✅ Built | [ADR 0019](adr/0019-electron-desktop-separate-process.md) | Finance shipped | API facade |
| Mobile | ⬜ Planned | — | Not started | Desktop, API |
| Cloud / Sync | ⬜ Deferred | — (open decision) | Not started | Core |
| Enterprise / Teams | ⬜ Deferred | [ADR 0021](adr/0021-workos-core-architecture.md) (`owner_id`) | Reserved | WorkOS v1 |

---

## 7. Domain Status Board

The canonical domain tracker. A "domain" here is a program-level capability, not a
Python package. Completion % tracks the *domain's own scope*.

| Domain | Purpose | Status | Current phase | Completion | Owner document | Dependencies |
|---|---|---|---|:---:|---|---|
| **Finance** | Money, cards, statements, rewards, cashback | ✅ Complete | Shipped | 100% | [FINANCE_DOMAIN.md](architecture/FINANCE_DOMAIN.md) | Core |
| **WorkOS** | Commitment + Time ledgers; founder decisions | 🔨 Active | Phase 0 | ~5% | [WorkOS Spec](NOVA_WORKOS_PRODUCT_SPEC_v1.md) | Core, (Finance read seam @ Ph.5) |
| **Knowledge** | Docs, embeddings, meeting → commitment | 🟡 Adapter | Deferred → Ph.10 | ~10% | [AI_CONTRACTS.md](architecture/AI_CONTRACTS.md) | Memory (LanceDB) |
| **Calendar** | External calendar events (read/port) | 🟡 Adapter | Injected @ Ph.3 | ~30% | [ADR 0018](adr/0018-voice-first-interaction.md) | Core |
| **Automation** | Background/scheduled side effects | 🟡 Scaffold | Deferred | ~5% | [Engineering Spec](architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md) | Core |
| **AI / Brain** | The only Claude client; reasoning jobs | 🟢 Built (client) | Chief of Staff → Ph.9 | ~40% | [ADR 0003](adr/0003-brain-is-the-only-claude-client.md) | Memory |
| **Desktop** | Electron UI for all domains | 🟢 Built (Finance) | WorkOS UI → Ph.1+ | ~50% | [ADR 0019](adr/0019-electron-desktop-separate-process.md) | API facade |

Legend: ✅ complete · 🟢 built for current scope · 🔨 active · 🟡 partial/adapter · ⬜ not started.

---

## 8. Program Dependency Map

How major domains depend on **each other at the program level** (not package
imports — those live in [`test_dependencies.py`](../apps/backend/tests/architecture/test_dependencies.py)).
This map drives *sequencing*: you cannot build downstream before upstream exists.

```
              ┌───────────────┐
              │ Core Platform │  memory · runtime · brain
              └───────┬───────┘
          ┌───────────┼─────────────────┐
          ▼           ▼                 ▼
     ┌─────────┐  ┌──────────┐    ┌──────────┐
     │ Finance │  │ Calendar │    │Knowledge │
     └────┬────┘  └────┬─────┘    └────┬─────┘
          │(read seam) │(port @ Ph.3)  │(@ Ph.10)
          └──────┬─────┴───────┬───────┘
                 ▼             ▼
            ┌─────────────────────┐
            │       WorkOS        │  Commitment + Time ledgers
            │  (the integrator)   │
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │   AI Chief of Staff │  proposes over deterministic core (Ph.9)
            └──────────┬──────────┘
                       ▼
            ┌─────────────────────┐
            │     Automation      │  acts on approved proposals (post-v1)
            └─────────────────────┘
```

**Reading:** WorkOS is the integrator — it *reads* Finance (revenue), Calendar
(capacity), and Knowledge (docs) through Memory/ports/Brain, never by importing them
([ADR 0011](adr/0011-domain-isolation.md)). AI sits on top of a working
deterministic WorkOS; Automation sits on top of approved AI proposals.

---

## 9. Release Roadmap

High-level releases only — **no implementation detail** (that lives in
[§12 Implementation Roadmap](#12-implementation-roadmap)). This is planning-level
intent, not a frozen commitment.

| Release | Theme | Contents | Maps to |
|---|---|---|---|
| **Nova v1** | Founder operating system | Finance ✅ · WorkOS MLP (Commitment + Time + Founder verdict) · Desktop | WorkOS Phases 0–6 |
| **Nova v1.1** | Strategic depth | Goals & strategic weight · Insights, Health & Reviews | WorkOS Phases 7–8 |
| **Nova v2** | Intelligence & reach | AI Chief of Staff · Workspace depth + Knowledge adapter | WorkOS Phases 9–10 |
| **Beyond v2** | Scale | Cloud sync · Mobile · Teams / Enterprise | Deferred ([§18](#18-deferred-work)) |

---

# PART III · WHERE WE ARE

## 10. Program Timeline

Chronological path to today. `[x]` = complete, `[ ]` = not started, `[>]` = active.

```
[x] Vision & product philosophy          → Build Bible
[x] Nova Core architecture frozen         → ADRs 0000–0020, frozen specs
[x] Finance domain built                  → first full domain (backend+API+desktop)
[x] WorkOS design frozen                  → 6 specs + ADRs 0021–0023
[x] WorkOS implementation plan            → workos/IMPLEMENTATION_PLAN.md
[x] Phase 0  Infrastructure & governance  → committed (ab11bf3)
[>] Phase 1  Capture + Commitment + Brief ← WE ARE HERE (backend landed; desktop slice pending)
[ ] Phase 2  Delivery graph (Products & Projects)
[ ] Phase 3  Time ledger + Execution
[ ] Phase 4  Planning & Decision Engine
[ ] Phase 5  Engagements (Clients) + Finance adapter
[ ] Phase 6  Founder Dashboard
[ ] Phase 7  Growth (Goals & strategic weight)
[ ] Phase 8  Insights, Health & Reviews
[ ] Phase 9  AI Chief of Staff
[ ] Phase 10 Workspace depth + Knowledge adapter
```

---

## 11. Completed Milestones

Project history, most recent last. Every line here is done and verified.

```
✓ Vision & Build Bible authored
✓ Nova Core architecture frozen (ADRs 0000–0020)
✓ Core Runtime + Engineering specifications frozen
✓ Engineering Handbook frozen
✓ CI, architecture tests & assistant boundary config stood up
✓ Runtime: tool handlers injected (no module-level global)
✓ mypy made blocking in CI (DEBT nova-ci-1 closed)
✓ Finance domain — accounts & transactions UI (production-ready)
✓ Finance — credit card product experience
✓ Finance — statements product experience
✓ Finance — dashboard experience
✓ Finance — rewards product experience
✓ Finance — cashback product experience
✓ Finance — product polish & quality pass
✓ Finance integrated across desktop, API, planner, runtime
✓ WorkOS design frozen (Product, Architecture, Data, Execution, Experience, UI/UX)
✓ WorkOS ADRs accepted (0021 core · 0022 two-ledger · 0023 derived state)
✓ WorkOS implementation companions authored (Plan, Governance, Risks, Boundaries, DB)
✓ WorkOS Phase 0 — infrastructure & governance (committed)
◐ WorkOS Phase 1 — Capture + Commitment ledger + Morning Brief shell (backend landed; desktop slice pending)
```

Detailed history is in git; the frozen decisions are in [§15 ADR Status](#15-adr-status).

---

## 12. Implementation Roadmap

WorkOS is the active program. Phases ship **independently valuable** increments; each
gate has exit criteria in [IMPLEMENTATION_GOVERNANCE.md](workos/IMPLEMENTATION_GOVERNANCE.md).
Full detail per phase → [workos/IMPLEMENTATION_PLAN.md](workos/IMPLEMENTATION_PLAN.md).

| Phase | Delivers | Status | Depends on | Detail |
|---|---|:---:|---|---|
| **0** | Boundaries, `Money` VO, `owner_id`, scaffolds, governance tests | ✅ Done | — | [Plan §0](workos/IMPLEMENTATION_PLAN.md) |
| **1** | Capture → triage → promote; Commitment ledger spine; Morning Brief v0 | 🔨 Backend done | 0 | [Plan §1](workos/IMPLEMENTATION_PLAN.md) |
| **2** | Delivery graph: Products, Releases, Projects, WorkItem tree | ⬜ Planned | 1 | [Plan §2](workos/IMPLEMENTATION_PLAN.md) |
| **3** | Time ledger: TimeEntry, FocusSession, capacity & allocation | ⬜ Planned | 2 | [Plan §3](workos/IMPLEMENTATION_PLAN.md) |
| **4** | Planning & Decision Engine: prioritization, estimation | ⬜ Planned | 2 (3) | [Plan §4](workos/IMPLEMENTATION_PLAN.md) |
| **5** | Engagements (Clients) + Finance read adapter, ROI/hr | ⬜ Planned | 3 | [Plan §5](workos/IMPLEMENTATION_PLAN.md) |
| **6** | Founder Dashboard: portfolio verdict, allocation honesty | ⬜ Planned | 5 | [Plan §6](workos/IMPLEMENTATION_PLAN.md) |
| **7** | Growth: Goals, KeyResults, LifeGoals, strategic weight | ⬜ Planned | 4 | [Plan §7](workos/IMPLEMENTATION_PLAN.md) |
| **8** | Insights, Health & Reviews (snapshots) | ⬜ Planned | 6 | [Plan §8](workos/IMPLEMENTATION_PLAN.md) |
| **9** | AI Chief of Staff: propose / explain / commit | ⬜ Planned | 8 | [Plan §9](workos/IMPLEMENTATION_PLAN.md) |
| **10** | Workspace depth + Knowledge adapter (meetings → commitments) | ⬜ Planned | 2 (9) | [Plan §10](workos/IMPLEMENTATION_PLAN.md) |

**Minimum lovable product:** Phases 0–3 + partial Phase 6 — capture, commitments,
time, allocation honesty, and a thin Founder verdict.

**Completed before WorkOS:** Nova Core v1.0 milestones and the Finance domain — see
the Core roadmap in [NOVA_IMPLEMENTATION_ROADMAP_v1.md](NOVA_IMPLEMENTATION_ROADMAP_v1.md).

---

## 13. Current Sprint

> **This section changes most often. Replace it wholesale each sprint.**

### WorkOS Phase 1 — Capture + Commitment ledger + Morning Brief shell (WOS-1)

**Objective:** *"Dump a thought; see today's decision."* Frictionless capture feeds a
derived priority list; Morning Brief v0 proves derivation works before time or clients
exist. Backend spine only — the desktop slice lands next.

**Done (backend):**
- [x] Five-table spine — `work_notes`, `work_projects`, `work_items`, `work_action_items`, `work_priority_policies` ([migrate_work_phase1](../apps/backend/memory/work/migrations.py)); FK-ordered, idempotent, index bundle, seeded default policy
- [x] Memory writers (sole persistence) with optimistic concurrency + atomic composite triage/promote transactions
- [x] Domain layer — aggregates, repository ports + SQLite adapters, `CaptureService`, `PromotionService`, `ProjectService`, `WorkItemService`, `PriorityPolicyService`
- [x] Pure deterministic `build_priority_queue` (deadline + decay only) and `build_briefing_shell` — no stored scores, injected clock
- [x] `MutationEvent` builders ([domains/work/mutations.py](../apps/backend/domains/work/mutations.py)) — `work.<entity>.<operation>`, composite promotion event
- [x] Planner parity layer (`work_commands`, `work_queries`, `work_serializers`) + REST routers (`services/api/routers/work/`)
- [x] 29 real-SQLite tests — governance/DDL, idempotency, concurrency, promotion, prioritization, briefing, mutation shape, chat/REST parity
- [x] Event contract appended to [DESKTOP_WRITE_OPERATIONS.md](architecture/DESKTOP_WRITE_OPERATIONS.md) §10

**Remaining (WOS-1 desktop slice):**
- [ ] Work section shell, Capture (⌘N), Today lens, capture inbox, read-only priority list, Morning Brief v0
- [ ] `EventsWebSocketEvent` `work.*` union in `@nova/api-contracts` + `invalidation-map.ts` + `queryKeys.work`
- [ ] Deferred: memory producers for `work.project.created/completed` (durable facts) — follow-up, not a gate

**Blocked:** none.

**Exit criteria** (from [IMPLEMENTATION_GOVERNANCE.md](workos/IMPLEMENTATION_GOVERNANCE.md)):
architecture tests pass · no derived columns · MutationEvent shape untouched ·
real-SQLite tests · chat/voice parity · CI green — all met for the backend gate.

**Links:** [Plan §1](workos/IMPLEMENTATION_PLAN.md) · [Schema gate](workos/WORKOS_PHASE1_SCHEMA.md) · [Governance](workos/IMPLEMENTATION_GOVERNANCE.md) · [Risks](workos/IMPLEMENTATION_RISKS.md)

---

## 14. Upcoming Sprints

High-level only — do not duplicate the [Implementation Plan](workos/IMPLEMENTATION_PLAN.md).

- **WOS-1 desktop slice (finishes Phase 1).** *"Dump a thought; see today's
  decision."* Backend spine is landed; remaining work is the Work section shell,
  Capture (⌘N), Today lens, capture inbox, read-only priority list, Morning Brief v0,
  and the `work.*` `invalidation-map.ts` / `queryKeys.work` contract.
- **Phase 2 — Delivery graph.** Products, Releases, Projects, full WorkItem tree with
  dependency cycle validation. Portfolio structure before ROI can be attributed.
- **Phase 3 — Time ledger.** Effortless time capture; capacity-aware planning;
  revealed allocation. Required before follow-through and ROI can be computed.
- **Phase 4 — Planning & Decision Engine.** Explainable cross-portfolio priority;
  estimation calibrated from real time entries.
- **Phases 5–10.** Clients + Finance adapter → Founder Dashboard → Goals →
  Insights/Reviews → AI Chief of Staff → Workspace depth. Breadth without reshaping
  the ledger architecture.

---

# PART IV · DECISIONS & RISK

## 15. ADR Status

The [ADR library](adr/README.md) is append-only and immutable once accepted. **All 24
ADRs are Accepted.** None are superseded or deferred.

**Nova Core (0000–0020) — foundation, accepted:**

| ADR | Title |
|---|---|
| [0000](adr/0000-record-architecture-decisions.md) | Record architecture decisions |
| [0001](adr/0001-local-first-architecture.md) | Local-first architecture |
| [0002](adr/0002-tiered-three-model-ai-architecture.md) | Tiered three-model AI architecture |
| [0003](adr/0003-brain-is-the-only-claude-client.md) | Brain is the only Claude client |
| [0004](adr/0004-memory-is-the-only-storage-owner.md) | Memory is the only storage owner |
| [0005](adr/0005-mutationevent-as-atomic-state-change.md) | MutationEvent as atomic state change |
| [0006](adr/0006-event-driven-single-process-runtime.md) | Event-driven single-process runtime |
| [0007](adr/0007-composition-root-owns-all-wiring.md) | Composition root owns all wiring |
| [0008](adr/0008-dependency-injection-over-imports.md) | Dependency injection over imports |
| [0009](adr/0009-layered-package-taxonomy.md) | Layered package taxonomy |
| [0010](adr/0010-service-isolation.md) | Service isolation (services are leaves) |
| [0011](adr/0011-domain-isolation.md) | Domain isolation (no domain calls another) |
| [0012](adr/0012-sqlite-as-system-of-record.md) | SQLite as the system of record |
| [0013](adr/0013-lancedb-as-vector-index.md) | LanceDB as the vector index |
| [0014](adr/0014-property-graph-in-sqlite.md) | Property graph in SQLite |
| [0015](adr/0015-explainable-decision-making.md) | Explainable decision-making |
| [0016](adr/0016-explicit-uncertainty.md) | Explicit uncertainty |
| [0017](adr/0017-finance-as-the-first-domain.md) | Finance as the first domain |
| [0018](adr/0018-voice-first-interaction.md) | Voice-first interaction |
| [0019](adr/0019-electron-desktop-separate-process.md) | Electron desktop as a separate process |
| [0020](adr/0020-fastapi-facade.md) | FastAPI facade as the desktop boundary |

**WorkOS (0021–0023) — accepted, governs the current build:**

| ADR | Title |
|---|---|
| [0021](adr/0021-workos-core-architecture.md) | WorkOS core architecture (WOS-ADR-001) |
| [0022](adr/0022-workos-two-ledger-architecture.md) | WorkOS two-ledger architecture (WOS-ADR-002) |
| [0023](adr/0023-workos-derived-state.md) | WorkOS derived state (WOS-ADR-003) |

**Superseded:** none. **Deferred:** none. Full index & reading rules → [adr/README.md](adr/README.md).

---

## 16. Decision Log

Major program decisions. Details live in the linked ADR/doc — this is the ledger.

| Date | Decision | Reason | Linked | Status |
|---|---|---|---|:---:|
| 2026-07-06 | Founding ADR library recorded (0000–0020) | Permanent record of frozen Core decisions | [adr/](adr/README.md) | ✅ |
| 2026-07-06 | Finance is the first domain | Pure logic, no external deps — proves the domain architecture | [0017](adr/0017-finance-as-the-first-domain.md) | ✅ |
| 2026-07-06 | WorkOS is Nova's second domain | Inherits every pattern Finance established | [Spec](NOVA_WORKOS_PRODUCT_SPEC_v1.md) | ✅ |
| 2026-07-06 | WorkOS core architecture accepted | Single domain package, bounded contexts | [0021](adr/0021-workos-core-architecture.md) | ✅ |
| 2026-07-06 | Two-ledger model (Commitment + Time) | Separate intent from spent hours | [0022](adr/0022-workos-two-ledger-architecture.md) | ✅ |
| 2026-07-06 | Derived state is never stored | Priority/health/ROI rebuildable, not persisted | [0023](adr/0023-workos-derived-state.md) | ✅ |
| 2026-07-07 | Phase 0 governance-first | Settle boundaries & money type before any WOS-1 data | [Plan §0](workos/IMPLEMENTATION_PLAN.md) | ✅ |
| 2026-07-07 | WOS-1 backend landed | Five-table Commitment/Capture spine + deterministic Brief; parity + real-SQLite green | [Schema gate](workos/WORKOS_PHASE1_SCHEMA.md) | ✅ |
| 2026-07-07 | Planner passes events opaquely | Keep `services.planner` off the `runtime` edge; `domains/work` owns builders | [Boundaries](workos/MODULE_BOUNDARIES.md) | ✅ |
| 2026-07-07 | Desktop slice + memory producers deferred | WOS-1 backend is independently valuable; UI/producers land next per schema §14 | [DWO §10](architecture/DESKTOP_WRITE_OPERATIONS.md) | 🔨 |

---

## 17. Next Decisions

**Pending decisions, not roadmap.** These are open questions that will need an owner
and (where they touch a frozen boundary) an ADR before work proceeds.

| Decision area | The open question | Owner / doc | Status |
|---|---|---|---|
| **Architecture** | None pending — architecture is frozen | Architect / [adr/](adr/README.md) | ✅ Settled |
| **Schema** | WOS-1 capture + commitment tables | [WORKOS_PHASE1_SCHEMA.md](workos/WORKOS_PHASE1_SCHEMA.md) | ✅ Implemented (backend) |
| **Desktop** | WOS-1 Work section + `work.*` invalidation contract | [WORKOS_UI_UX](NOVA_WORKOS_UI_UX_SPECIFICATION_v1.md) | 🔨 Next (WOS-1 desktop slice) |
| **Product** | Pricing / monetization model | — (no owning doc yet) | ⬜ Open, unscheduled |
| **Business** | Cloud sync & hosting model (breaks local-first default?) | — (would need an ADR) | ⬜ Open, unscheduled |
| **Research** | AI Chief of Staff — propose/explain/commit design | [Plan §9](workos/IMPLEMENTATION_PLAN.md) | ⬜ Deferred → Phase 9 |
| **Platform** | Mobile client approach | — | ⬜ Open, unscheduled |

Any item touching a package boundary, `MutationEvent`, a Claude tool schema, or the
DB schema **requires an ADR first** — see the ADR trigger list in
[IMPLEMENTATION_GOVERNANCE.md](workos/IMPLEMENTATION_GOVERNANCE.md).

---

## 18. Deferred Work

Intentionally postponed. Not cut — sequenced later because they depend on ledgers
that do not yet exist.

| Deferred | Why postponed | Returns in |
|---|---|---|
| **AI Chief of Staff** (propose/explain/commit) | Needs a trustworthy deterministic Decision Engine underneath first | Phase 9 |
| **Planning AI / prioritization narrative** | Priority must be deterministic & explainable in the domain before Brain narrates it | Phase 4 → 9 |
| **Reviews & Health snapshots** | Reports must not precede trustworthy ledger inputs | Phase 8 |
| **Clients / Engagements** | ROI/hour needs the Time ledger (Phase 3) and a Finance read seam | Phase 5 |
| **Goals & strategic weight** | Core loops must work with neutral weights first | Phase 7 |
| **Meetings / Knowledge adapter** | Needs a stable Work graph for action-item promotion | Phase 10 |
| **Autonomous agent actions** | v1 is propose-only; trust-gated autonomy is a v2+ ADR | Post-v1 |
| **Teams / multi-user** | `owner_id` is *reserved* now, but v1 is single-operator | Post-v1 |
| **Additional Core domains** (Wellness, Social, etc.) | Pattern proven by Finance; added after WorkOS establishes the second-domain template | Core roadmap M5+ |

---

## 19. Current Risks

Top risks by category. Full register → [workos/IMPLEMENTATION_RISKS.md](workos/IMPLEMENTATION_RISKS.md).

**Architecture**
- Derived value stored by accident (priority/health/ROI) → guarded by forbidden-column
  linter + [ADR 0023](adr/0023-workos-derived-state.md). Highest-severity invariant.
- Package boundary / cross-domain import drift → [test_dependencies.py](../apps/backend/tests/architecture/test_dependencies.py) is the gate.
- `MutationEvent` shape change → frozen; additive `entity_type` only.

**Implementation**
- Retrofitting `owner_id` / money type after WOS-1 data exists → mitigated by
  doing it in Phase 0 (current sprint).
- Capture idempotency & derived-priority-stored-by-accident → Phase 1 gate tests.

**Product**
- A surface that cannot name the founder decision it drives → banned by
  [Governance law #2](workos/IMPLEMENTATION_GOVERNANCE.md); the 30-second decision
  test is the acceptance criterion.

**Business**
- Scope breadth (11 phases, solo → team) → each phase is independently valuable;
  MLP is Phases 0–3 + partial 6.

---

# PART V · AUTHORITY & NAVIGATION

## 20. Frozen Design Stack

Every canonical design document. **Frozen** means immutable without a new ADR.

| Document | What it owns | Frozen | Location |
|---|---|:---:|---|
| Build Bible | Product philosophy & judgment | ✅ | [BUILD_BIBLE.md](BUILD_BIBLE.md) |
| Core Runtime Specification | How Nova executes | ✅ | [architecture/…RUNTIME…](architecture/NOVA_CORE_RUNTIME_SPECIFICATION_v1.md) |
| Engineering Specification | How code is organized | ✅ | [architecture/…ENGINEERING…](architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md) |
| Engineering Handbook | How code is written/reviewed/tested | ✅ | [NOVA_ENGINEERING_HANDBOOK_v1.md](NOVA_ENGINEERING_HANDBOOK_v1.md) |
| Implementation Roadmap (Core) | PR-by-PR plan for Nova Core v1 | ✅ | [NOVA_IMPLEMENTATION_ROADMAP_v1.md](NOVA_IMPLEMENTATION_ROADMAP_v1.md) |
| WorkOS Product Spec | WorkOS *what & how it fits* | ✅ | [NOVA_WORKOS_PRODUCT_SPEC_v1.md](NOVA_WORKOS_PRODUCT_SPEC_v1.md) |
| WorkOS Architecture | WorkOS package & boundary design | ✅ | [NOVA_WORKOS_ARCHITECTURE_v1.md](NOVA_WORKOS_ARCHITECTURE_v1.md) |
| WorkOS Data Model | Two-ledger data model | ✅ | [NOVA_WORKOS_DATA_MODEL_v1.md](NOVA_WORKOS_DATA_MODEL_v1.md) |
| WorkOS Execution Model | The daily decision loop | ✅ | [NOVA_WORKOS_EXECUTION_MODEL_v1.md](NOVA_WORKOS_EXECUTION_MODEL_v1.md) |
| WorkOS Product Experience | End-to-end product experience | ✅ | [NOVA_WORKOS_PRODUCT_EXPERIENCE_v1.md](NOVA_WORKOS_PRODUCT_EXPERIENCE_v1.md) |
| WorkOS UI/UX Specification | Screens, lenses, interactions | ✅ | [NOVA_WORKOS_UI_UX_SPECIFICATION_v1.md](NOVA_WORKOS_UI_UX_SPECIFICATION_v1.md) |

**Owner of the whole stack:** Principal Software Architect. **All frozen** — see
[`CLAUDE.md`](../CLAUDE.md) for the authority order.

---

## 21. Frozen vs Mutable

Removes all ambiguity about what may change and by whom.

| Document | Purpose | Frozen? | Owner | Editable? | Update frequency | Authority |
|---|---|:---:|---|---|---|---|
| ADRs 0000–0023 | Architecture decisions | ✅ Yes | Architect | Only via *new* ADR | Append-only | **Highest** |
| Core Runtime Spec | Execution model | ✅ Yes | Architect | ADR required | Rare | Highest |
| Engineering Spec | Code organization | ✅ Yes | Architect | ADR required | Rare | Highest |
| Engineering Handbook | Code standards | ✅ Yes | Architect | ADR/human review | Rare | High |
| Build Bible | Product convictions | ✅ Yes | Architect | Human decision | Rare | High |
| WorkOS design specs (6) | WorkOS design | ✅ Yes | Architect | ADR required | Rare | High |
| Core Impl. Roadmap | Core PR plan | ✅ Frozen | Architect | Human review | Rare | Medium |
| WorkOS Impl. Plan | Build order | ❌ No | Program lead | Yes | Per phase | Medium |
| WorkOS Governance | Engineering law | ❌ No (amend via ADR) | Architect | ADR to override | Rare | High |
| WorkOS Risks | Risk register | ❌ No | Program lead | Yes | As discovered | Medium |
| **This file** | Program control center | ❌ No | Program lead | Yes | Every sprint | Navigational |
| CLAUDE.md | Repo ground truth | ❌ No (guarded) | Architect | Human decision | Rare | High |

**Rule:** if a Frozen document changes, an **ADR must exist first**. This file is
updated *after* the ADR, never before.

---

## 22. Document Ownership

For every major document: who owns it, what it's for, its authority, what would
replace it, and how often it changes.

| Document | Owner | Purpose | Authority | Replacement if superseded | Cadence |
|---|---|---|---|---|---|
| [CLAUDE.md](../CLAUDE.md) | Architect | Repo ground truth & rules | Binding | New CLAUDE.md revision | Rare |
| [ADR Library](adr/README.md) | Architect | Frozen decisions | Highest | A *newer* ADR supersedes | Append-only |
| [Core Runtime Spec](architecture/NOVA_CORE_RUNTIME_SPECIFICATION_v1.md) | Architect | Execution model | Highest | `…RUNTIME…_v2` + ADR | Rare |
| [Engineering Spec](architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md) | Architect | Code organization | Highest | `…ENGINEERING…_v2` + ADR | Rare |
| [Engineering Handbook](NOVA_ENGINEERING_HANDBOOK_v1.md) | Architect | Code standards | High | `…HANDBOOK_v2` | Rare |
| [Build Bible](BUILD_BIBLE.md) | Architect | Product convictions | High | Human decision only | Rare |
| [WorkOS specs (×6)](NOVA_WORKOS_PRODUCT_SPEC_v1.md) | Architect | WorkOS design | High | `…_v2` + ADR | Rare |
| [WorkOS Impl. Plan](workos/IMPLEMENTATION_PLAN.md) | Program lead | Build order | Medium | Living — edited in place | Per phase |
| [WorkOS Governance](workos/IMPLEMENTATION_GOVERNANCE.md) | Architect | Engineering law | High | New ADR amends | Rare |
| [WorkOS Risks](workos/IMPLEMENTATION_RISKS.md) | Program lead | Risk register | Medium | Living | As needed |
| **Master Plan (this)** | Program lead | Control center | Navigational | This file evolves | Every sprint |

---

## 23. Canonical Documents

The navigation index. One row per important document.

| Document | Purpose | Status | Owner | Frozen | Location |
|---|---|---|---|:---:|---|
| Master Plan | Program control tower | Living | Program lead | ❌ | this file |
| CLAUDE.md | Repo ground-truth & authority order | Living | Architect | ❌ | [../CLAUDE.md](../CLAUDE.md) |
| ADR Library | Frozen decisions | Append-only | Architect | ✅ | [adr/README.md](adr/README.md) |
| Core Runtime Spec | Execution model | Frozen | Architect | ✅ | [architecture/…RUNTIME…](architecture/NOVA_CORE_RUNTIME_SPECIFICATION_v1.md) |
| Engineering Spec | Code organization | Frozen | Architect | ✅ | [architecture/…ENGINEERING…](architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md) |
| Engineering Handbook | Code style & review | Frozen | Architect | ✅ | [NOVA_ENGINEERING_HANDBOOK_v1.md](NOVA_ENGINEERING_HANDBOOK_v1.md) |
| Build Bible | Product convictions | Frozen | Architect | ✅ | [BUILD_BIBLE.md](BUILD_BIBLE.md) |
| Core Roadmap | Nova Core PR plan | Frozen | Architect | ✅ | [NOVA_IMPLEMENTATION_ROADMAP_v1.md](NOVA_IMPLEMENTATION_ROADMAP_v1.md) |
| WorkOS Product Spec | WorkOS what & fit | Frozen | Architect | ✅ | [Spec](NOVA_WORKOS_PRODUCT_SPEC_v1.md) |
| WorkOS Architecture | WorkOS design | Frozen | Architect | ✅ | [Architecture](NOVA_WORKOS_ARCHITECTURE_v1.md) |
| WorkOS Data Model | Two-ledger model | Frozen | Architect | ✅ | [Data Model](NOVA_WORKOS_DATA_MODEL_v1.md) |
| WorkOS Execution Model | Daily decision loop | Frozen | Architect | ✅ | [Execution Model](NOVA_WORKOS_EXECUTION_MODEL_v1.md) |
| WorkOS Product Experience | Felt experience | Frozen | Architect | ✅ | [Experience](NOVA_WORKOS_PRODUCT_EXPERIENCE_v1.md) |
| WorkOS UI/UX Spec | Screens & lenses | Frozen | Architect | ✅ | [UI/UX](NOVA_WORKOS_UI_UX_SPECIFICATION_v1.md) |
| WorkOS Impl. Plan | Build order | Living | Program lead | ❌ | [Plan](workos/IMPLEMENTATION_PLAN.md) |
| WorkOS Governance | Engineering law | Living | Architect | ❌ | [Governance](workos/IMPLEMENTATION_GOVERNANCE.md) |
| WorkOS Risks | Risk register | Living | Program lead | ❌ | [Risks](workos/IMPLEMENTATION_RISKS.md) |
| WorkOS Module Boundaries | Import rules | Frozen | Architect | ✅ | [Boundaries](workos/MODULE_BOUNDARIES.md) |
| WorkOS Database Structure | Ledger tables | Frozen | Architect | ✅ | [DB Structure](workos/DATABASE_STRUCTURE.md) |

---

## 24. Repository Map

| Path | What lives here | Canonical doc |
|---|---|---|
| [`docs/`](.) | All specs, ADRs, roadmaps, reviews | **this file** |
| [`docs/adr/`](adr/) | Accepted architecture decisions (immutable) | [adr/README.md](adr/README.md) |
| [`docs/architecture/`](architecture/) | Frozen runtime & engineering specs | [Engineering Spec](architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md) |
| [`docs/workos/`](workos/) | WorkOS implementation companions | [IMPLEMENTATION_PLAN.md](workos/IMPLEMENTATION_PLAN.md) |
| [`docs/roadmap/`](roadmap/) | Core phased roadmap notes | [ROADMAP.md](roadmap/ROADMAP.md) |
| [`docs/review/`](review/) | Structural reviews & reports | [review/](review/) |
| [`apps/backend/`](../apps/backend/) | Python backend (Nova Core + domains) | [backend README](../apps/backend/README.md) |
| `apps/backend/memory/` | The only package touching SQLite / LanceDB | [ADR 0004](adr/0004-memory-is-the-only-storage-owner.md) |
| `apps/backend/runtime/` | Conversation pipeline, MutationEvent, side effects | [Runtime Spec](architecture/NOVA_CORE_RUNTIME_SPECIFICATION_v1.md) |
| `apps/backend/domains/` | `finance/` (built), `work/` (Phase 0 scaffold) | [ADR 0011](adr/0011-domain-isolation.md) |
| `apps/backend/services/` | brain, api, planner, voice, calendar, knowledge, automation | [ADR 0010](adr/0010-service-isolation.md) |
| `apps/backend/tests/architecture/` | Boundary tests — the source of truth for imports | `test_dependencies.py` |
| `packages/`, `apps/desktop/` | Shared packages & Electron desktop | [ADR 0019](adr/0019-electron-desktop-separate-process.md) |

The single source of truth for *which package may import which* is
`apps/backend/tests/architecture/test_dependencies.py` — read it before adding a
cross-package import (see [`CLAUDE.md`](../CLAUDE.md)).

---

## 25. Master Index

Every canonical document, categorized, appearing exactly once. This is the full
table of contents for the repository's knowledge.

**Architecture**
- [ADR Library (0000–0023)](adr/README.md)
- [Core Runtime Specification](architecture/NOVA_CORE_RUNTIME_SPECIFICATION_v1.md)
- [Engineering Specification](architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md)
- [AI Contracts](architecture/AI_CONTRACTS.md)
- [Desktop Write Operations](architecture/DESKTOP_WRITE_OPERATIONS.md)
- [Architecture v1](architecture/ARCHITECTURE_v1.md) · [Architecture v2](architecture/ARCHITECTURE_v2.md)

**Product**
- [Build Bible](BUILD_BIBLE.md)
- [WorkOS Product Spec](NOVA_WORKOS_PRODUCT_SPEC_v1.md)
- [WorkOS Product Experience](NOVA_WORKOS_PRODUCT_EXPERIENCE_v1.md)
- [WorkOS UI/UX Specification](NOVA_WORKOS_UI_UX_SPECIFICATION_v1.md)

**Engineering**
- [Engineering Handbook](NOVA_ENGINEERING_HANDBOOK_v1.md)
- [CLAUDE.md (repo ground truth)](../CLAUDE.md)
- [WorkOS Governance](workos/IMPLEMENTATION_GOVERNANCE.md)
- [WorkOS Module Boundaries](workos/MODULE_BOUNDARIES.md)

**Implementation**
- [Core Implementation Roadmap](NOVA_IMPLEMENTATION_ROADMAP_v1.md)
- [WorkOS Implementation Plan](workos/IMPLEMENTATION_PLAN.md)
- [WorkOS Phase 1 Schema](workos/WORKOS_PHASE1_SCHEMA.md)

**Finance**
- [Finance Domain](architecture/FINANCE_DOMAIN.md)
- [Finance Data Model](architecture/FINANCE_DATA_MODEL.md)

**WorkOS**
- [WorkOS Architecture](NOVA_WORKOS_ARCHITECTURE_v1.md)
- [WorkOS Data Model](NOVA_WORKOS_DATA_MODEL_v1.md)
- [WorkOS Execution Model](NOVA_WORKOS_EXECUTION_MODEL_v1.md)
- [WorkOS Database Structure](workos/DATABASE_STRUCTURE.md)

**Business / Risk**
- [WorkOS Implementation Risks](workos/IMPLEMENTATION_RISKS.md)
- [§17 Next Decisions](#17-next-decisions) (pending business/product decisions)

**Roadmaps**
- [Program Roadmap](roadmap/ROADMAP.md)
- [Phase 1](roadmap/PHASE_1.md) · [Phase 2](roadmap/PHASE_2.md) · [Phase 3](roadmap/PHASE_3.md) · [Phase 4](roadmap/PHASE_4.md)

**Reviews**
- [Repository Structure Refactor](review/repository-structure-refactor.md)
- [Review reports](review/)

**Research**
- AI Chief of Staff — deferred, design in [Plan §9](workos/IMPLEMENTATION_PLAN.md)

---

## 26. Navigation

Fastest path to the right document:

- **"How does Nova execute?"** → [Core Runtime Spec](architecture/NOVA_CORE_RUNTIME_SPECIFICATION_v1.md)
- **"How is code organized / what can import what?"** → [Engineering Spec](architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md) · [test_dependencies.py](../apps/backend/tests/architecture/test_dependencies.py)
- **"How do I write & review code here?"** → [Engineering Handbook](NOVA_ENGINEERING_HANDBOOK_v1.md) · [CLAUDE.md](../CLAUDE.md)
- **"Why is Nova shaped this way?"** → [ADR Library](adr/README.md) · [Build Bible](BUILD_BIBLE.md)
- **"What is WorkOS and what does it do?"** → [Product Spec](NOVA_WORKOS_PRODUCT_SPEC_v1.md) · [Experience](NOVA_WORKOS_PRODUCT_EXPERIENCE_v1.md)
- **"What am I building next & in what order?"** → [WorkOS Impl. Plan](workos/IMPLEMENTATION_PLAN.md) · [§13 Current Sprint](#13-current-sprint)
- **"What are the rules I must not break?"** → [WorkOS Governance](workos/IMPLEMENTATION_GOVERNANCE.md)
- **"What could go wrong?"** → [WorkOS Risks](workos/IMPLEMENTATION_RISKS.md)

---

## 27. Maintenance Contract

> **This is the authoritative rule for how this file stays honest.** (Supersedes the
> shorter note that once lived at the top.)

**After every completed sprint, update — and only these:**

- [§1 Current Focus](#1-current-focus)
- [§2 Executive Summary](#2-executive-summary)
- [§3 Success Dashboard](#3-success-dashboard)
- [§4 Repository Metrics](#4-repository-metrics)
- [§10 Program Timeline](#10-program-timeline)
- [§11 Completed Milestones](#11-completed-milestones)
- [§12 Implementation Roadmap](#12-implementation-roadmap)
- [§13 Current Sprint](#13-current-sprint) (replace wholesale)
- [§16 Decision Log](#16-decision-log) (append any decision made)
- [§17 Next Decisions](#17-next-decisions) (retire resolved, add new)

**Never modify from this file** (they are owned elsewhere and only *linked* here):

- Architecture ([adr/](adr/README.md), frozen specs)
- ADRs
- Frozen specifications ([§20](#20-frozen-design-stack))
- Build Bible
- Engineering Handbook

**The iron rule:** if a frozen document must change, a **new ADR must exist first**.
This file is updated *after* the ADR is accepted — never before, never instead.

**Who maintains it:** the Program lead, at each sprint boundary. Structural changes
(adding/removing a section) are a deliberate act, not a routine update.

---

*This document is a navigation hub. It duplicates nothing it can link to. When it is
stale, the linked owner document is right — fix this file, not the other.*
