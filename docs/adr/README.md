# Nova Architecture Decision Records

This directory is the permanent record of the **irreversible and high-impact
architectural decisions** behind Nova Core v1.0. It exists so that a year-5 (or
year-10) engineer can understand *why* Nova is shaped the way it is without
re-litigating choices that were made deliberately and frozen.

## Reading rules

- These ADRs **document decisions already made**. They do not re-open the frozen
  architecture. The authoritative design lives in
  [`../architecture/`](../architecture/), the
  [Engineering Specification](../architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md),
  the [Core Runtime Specification](../architecture/NOVA_CORE_RUNTIME_SPECIFICATION_v1.md),
  and the [Engineering Handbook](../NOVA_ENGINEERING_HANDBOOK_v1.md). Each ADR
  links back to the section it records.
- ADRs are **append-only and immutable once accepted** (Handbook §8.3/§8.4). A
  reversed decision is a *new* ADR that supersedes the old one; both are linked,
  and neither is edited or deleted.
- Format for every ADR: **Context → Decision → Alternatives Considered →
  Consequences → Why Alternatives Were Rejected → Future Evolution**. One page.
- "Future Evolution" notes the *concrete, observable trigger* that would justify
  revisiting the decision. It is never a promise to change — it is the condition
  under which change would be legitimate.

## Index

| ADR | Title | Status |
|---|---|---|
| [0000](0000-record-architecture-decisions.md) | Record architecture decisions | Accepted |
| [0001](0001-local-first-architecture.md) | Local-first architecture | Accepted |
| [0002](0002-tiered-three-model-ai-architecture.md) | Tiered three-model AI architecture | Accepted |
| [0003](0003-brain-is-the-only-claude-client.md) | Brain is the only Claude client | Accepted |
| [0004](0004-memory-is-the-only-storage-owner.md) | Memory is the only storage owner | Accepted |
| [0005](0005-mutationevent-as-atomic-state-change.md) | MutationEvent as the atomic unit of state change | Accepted |
| [0006](0006-event-driven-single-process-runtime.md) | Event-driven single-process runtime | Accepted |
| [0007](0007-composition-root-owns-all-wiring.md) | Composition root owns all wiring | Accepted |
| [0008](0008-dependency-injection-over-imports.md) | Dependency injection over cross-boundary imports | Accepted |
| [0009](0009-layered-package-taxonomy.md) | Layered package taxonomy: Core / Services / Domains | Accepted |
| [0010](0010-service-isolation.md) | Service isolation (services are leaves) | Accepted |
| [0011](0011-domain-isolation.md) | Domain isolation (no domain calls another domain) | Accepted |
| [0012](0012-sqlite-as-system-of-record.md) | SQLite as the system of record | Accepted |
| [0013](0013-lancedb-as-vector-index.md) | LanceDB as the vector index | Accepted |
| [0014](0014-property-graph-in-sqlite.md) | Property graph in SQLite over dedicated graph DB / RDF | Accepted |
| [0015](0015-explainable-decision-making.md) | Explainable decision-making | Accepted |
| [0016](0016-explicit-uncertainty.md) | Explicit uncertainty | Accepted |
| [0017](0017-finance-as-the-first-domain.md) | Finance as the first domain | Accepted |
| [0018](0018-voice-first-interaction.md) | Voice-first interaction | Accepted |
| [0019](0019-electron-desktop-separate-process.md) | Electron desktop as a separate process | Accepted |
| [0020](0020-fastapi-facade.md) | FastAPI facade as the desktop boundary | Accepted |
| [0021](0021-workos-core-architecture.md) | WorkOS core architecture (WOS-ADR-001) | Accepted |
| [0022](0022-workos-two-ledger-architecture.md) | WorkOS two-ledger architecture (WOS-ADR-002) | Accepted |
| [0023](0023-workos-derived-state.md) | WorkOS derived state (WOS-ADR-003) | Accepted |

_WorkOS implementation companions (not ADRs):_
[`workos/MODULE_BOUNDARIES.md`](../workos/MODULE_BOUNDARIES.md) ·
[`workos/DATABASE_STRUCTURE.md`](../workos/DATABASE_STRUCTURE.md) ·
[`workos/IMPLEMENTATION_PLAN.md`](../workos/IMPLEMENTATION_PLAN.md) ·
[`workos/IMPLEMENTATION_RISKS.md`](../workos/IMPLEMENTATION_RISKS.md) ·
[`workos/IMPLEMENTATION_GOVERNANCE.md`](../workos/IMPLEMENTATION_GOVERNANCE.md)

_All ADRs recorded 2026-07-06 as the founding ADR library unless otherwise dated.
The decisions themselves were made during Nova Core v1.0 design and are frozen;
this library is the retroactive, permanent record of them._
