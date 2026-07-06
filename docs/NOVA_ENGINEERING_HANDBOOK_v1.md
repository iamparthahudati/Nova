# NOVA ENGINEERING HANDBOOK v1

**Status:** Mandatory Engineering Standard — Frozen Nova Core v1.0
**Scope:** How code is written, reviewed, tested, and maintained in Nova. This is the implementation bible.
**Abstraction level:** Implementation — *how to write code*, not *how the system is designed*.
**Audience:** Every human contributor and every AI coding assistant (Claude Code, Cursor, Copilot, ChatGPT).
**Authority:** Engineering Lead, Nova Core.
**Companions (do not duplicate, do not contradict):**
`NOVA_CORE_RUNTIME_SPECIFICATION_v1.md` (how the system executes),
`NOVA_ENGINEERING_SPECIFICATION_v1.md` (how code is organized),
`docs/architecture/ARCHITECTURE_v2.md`, `AI_CONTRACTS.md`, `FINANCE_DOMAIN.md`, `FINANCE_DATA_MODEL.md`.

---

## 0. How to use this handbook

This document does not describe the architecture. The architecture is frozen and lives in the specs above. This document tells you how to write code *inside* that architecture so that Nova is as clean in year 5 as it is today.

**Three rules govern everything that follows:**

1. **The architecture is law.** If this handbook and a frozen spec ever disagree about a boundary, the spec wins. If this handbook is silent, the spec's rules still apply.
2. **Boring is a feature.** Nova optimizes for the engineer who reads this code at 2 a.m. in three years with no context. Cleverness that saves you ten minutes today and costs them an hour then is a net loss.
3. **Every rule here is checkable.** If a rule cannot be enforced by a linter, a test, or a reviewer with a checklist, it is written as a checklist item, not a vibe.

**Conformance language.** "**MUST**" / "**MUST NOT**" are hard rules — a PR violating one does not merge. "**SHOULD**" / "**SHOULD NOT**" are strong defaults — deviating requires a one-line justification in the PR description. "**MAY**" is a genuine choice.

**Stack this handbook assumes** (from the frozen specs — not up for redesign here):
Python 3.9+ backend under `apps/backend/`; single-process, event-driven runtime; SQLite + LanceDB persistence; Anthropic Claude via a single Brain client; Electron + React + TypeScript desktop under `apps/desktop/`; `pytest`, `black`, `isort`, `flake8`, `mypy` as the toolchain.

---

## 1. Coding Philosophy

How Nova code should *feel*. These are not aspirations — each maps to a checklist item in §4.

### 1.1 Boring code wins

Prefer the obvious implementation. A `for` loop a junior can read beats a nested comprehension a senior has to decode. If two implementations are equally correct, ship the one with fewer concepts in it.

```python
# BAD — clever, dense, one line, unreadable at 2 a.m.
totals = {c: sum(m.amount for m in ms) for c, ms in groupby(sorted(money, key=cat), cat)}

# GOOD — boring, obvious, debuggable
totals: dict[str, float] = {}
for entry in money:
    totals[entry.category] = totals.get(entry.category, 0.0) + entry.amount
```

### 1.2 Explicit over implicit

- No hidden globals. State is passed in, not reached for.
- No magic strings for control flow — use the enums in `nova.core.contracts` (`Operation`, `EntityType`, domain codes). A raw `"create"` in domain code is a bug waiting to happen; `Operation.CREATE.value` is not.
- No implicit type coercion at boundaries. Parse and validate at the edge; trust types inside.
- Function signatures tell the whole truth. If a function reads the database, its dependency (a memory handle) is a parameter, not an import it grabs.

### 1.3 Readable over short

Line count is not a metric. Deleting a helper to save three lines and inlining a comment-worthy trick is a regression. Name intermediate values even when you could chain. Optimize for the diff a reviewer reads, not the character count.

### 1.4 Deterministic by default

The runtime spec's core invariant is **"No mutation without an event. No event without a mutation."** That determinism extends to your code:

- Given the same inputs, a function returns the same output. Mutation-building (`tool_calls_to_mutations`) is a pure function *because the spec requires it to be*.
- Non-determinism (clock, RNG, network, Claude, filesystem) is **injected**, never reached for inline. `now: datetime` is a parameter; `datetime.now()` in the middle of business logic is a defect.
- Anything that talks to Claude is non-deterministic *by nature* and is therefore quarantined in Brain. No other package may become non-deterministic by importing an LLM.

### 1.5 Side effects are isolated

Nova separates **decide** from **do**.

- Pure core: functions that compute mutations, plans, summaries, and context. No I/O.
- Effect edge: functions that write the DB, call Claude, speak audio, hit an API, spawn a thread.
- A function that both computes *and* persists in the same body is split. The runtime's own shape — `tool_calls_to_mutations()` (pure) → `finalize_mutations()` (effectful) — is the pattern every domain follows.

### 1.6 No hidden magic

- No metaclasses, no monkey-patching, no `__getattr__` routing, no decorators that silently rewrite behavior beyond the four sanctioned ones (§1.8).
- No reflection-based dispatch where a dict would do. Nova already dispatches tools through an explicit `TOOL_HANDLERS` dict — follow that pattern; do not invent a registry that auto-discovers handlers by naming convention.
- If a reader must run the code to know what it does, it is too magical.

### 1.7 Composition over inheritance

- Deep class hierarchies are banned. **Maximum inheritance depth is 1** (a class may extend one project-defined base or an stdlib/framework base; no `A → B → C`).
- Reuse by composing small functions and injecting collaborators, not by subclassing to override.
- Data is `@dataclass` (frozen where the spec says so, e.g. `MutationEvent`). Behavior is functions that take data. Prefer a module of functions over a "manager" class holding mutable state.
- ABCs / `Protocol` are allowed **only** to express an injection contract (e.g. a `ContextProvider` interface), never to share implementation.

### 1.8 Dependency injection rules

Nova is wired at exactly one place: the **composition root**, `apps/backend/nova/main.py`. Everything else receives its dependencies.

- **Constructor/parameter injection only.** A collaborator arrives as a function argument or an `__init__` parameter. No service locator, no global registry, no import-time singletons.
- **The composition root is the only place that knows the concrete graph.** It constructs Memory, Brain, Services, Domains and wires them. Nothing deep in the tree reaches back up to build its own dependencies.
- **Cross-boundary calls are injected, never imported.** Per the eng spec: Brain never imports Calendar — it receives `calendar.get_events` as a `context_provider`. Domains never import Services — the composition root hands them tool handlers. Services never import each other.
- **Only four decorators are sanctioned:** `@dataclass`, `@property`, `@staticmethod`/`@classmethod`, and `@functools.cached_property`/`@lru_cache` on pure functions. Any other decorator requires an ADR.
- **The direction of dependency is always inward/upward.** Services → Core only. Domains → Core (and injected Services). Never sideways (Service → Service, Domain → Domain), never downward (Core → Domain). This is enforced by the architecture test in §5.4.

---

## 2. Naming Conventions

Names are the cheapest documentation and the most-read part of the codebase. They are not negotiable per-author.

### 2.1 The master table

| Thing | Convention | Example | Notes |
|---|---|---|---|
| **Python file / module** | `snake_case.py` | `mutation_builders.py` | One responsibility per file; filename names it. |
| **Package** | `snake_case`, singular for a concept, plural only for a collection | `nova.core.runtime`, `nova.domains.finance` | Matches the `nova.<tier>.<name>` taxonomy exactly. |
| **Directory** | `snake_case` | `context_engine/` | Matches its package. |
| **Class / dataclass / Enum type** | `PascalCase` | `MutationEvent`, `ConversationResult`, `Operation` | Nouns. No `Manager`/`Helper`/`Util` unless it truly is one. |
| **Function / method** | `snake_case`, **verb-first** | `add_task()`, `get_events()`, `build_daily_plan()` | See verb lexicon §2.2. |
| **Pure vs. effectful function** | effectful reads verb-of-action; pure reads verb-of-compute | `persist_task()` vs `build_task()` | A `get_`/`build_`/`compute_` name MUST NOT write. |
| **Variable** | `snake_case`, full words | `spending_summary`, `due_reminders` | No single letters except loop indices `i`, `j` and math. |
| **Boolean variable / function** | `is_`/`has_`/`should_`/`can_` prefix | `is_completed`, `should_run_reflection()` | Reads as a yes/no question. |
| **Constant** | `UPPER_SNAKE_CASE` | `NOVA_CONTEXT_TOKEN_BUDGET`, `EXTRACTION_MAX_ATTEMPTS` | Module-level; defined once. |
| **Private module member** | `_leading_underscore` | `_journal_mutations()`, `_tool_events` | Signals "not public API." |
| **Enum member** | `UPPER_SNAKE_CASE`, value is `snake_case` string | `Operation.CREATE = "create"` | Value is the wire/DB form. |
| **Interface / Protocol / ABC** | `PascalCase`, no `I` prefix | `ContextProvider`, `ToolHandler` | Name the role, not "interface." |
| **Type alias** | `PascalCase` | `ToolHandler = Callable[[dict], str]` | Lives in `contracts`. |
| **Event type** (MutationEvent) | `entity.pastverb`, dot-delimited, lowercase | `task.created`, `money.logged`, `habit.logged` | `<entity>.<operation-past-tense>`. Empty string `""` for non-WebSocket events. |
| **Domain mutation function** | `snake_case`, verb + entity | `log_task()`, `complete_task()`, `ship_product()` | Present-tense imperative. |
| **Claude tool name** | `snake_case`, verb-first, imperative | `open_app`, `get_spending_summary`, `create_event` | Matches the domain function it fronts; is a behavioral contract with Claude (see §2.4). |
| **Database table** | `snake_case`, **plural** | `tasks`, `money`, `habits`, `conversation_history`, `entities`, `edges` | One table per entity; name is the entity pluralized. `money` is a mass noun (no `moneys`). |
| **Database column** | `snake_case`, singular | `id`, `text`, `due`, `created_at`, `completed` | Timestamps end `_at`; booleans read as adjectives (`completed`), not `is_`. |
| **Foreign key column** | `<entity>_id` | `task_id`, `source_memory_id` | Always `<referent-singular>_id`. |
| **Migration script** | `NNN_snake_description.py` | `007_add_task_priority.py` | Zero-padded ordinal + what it does. |
| **Test file** | `test_<unit-under-test>.py` | `test_tool_dispatch.py`, `test_mutation_event_shape.py` | Mirrors the module it tests. |
| **Test function** | `test_<condition>_<expected>` | `test_complete_task_marks_done()` | Reads as a sentence. |
| **TypeScript file (desktop)** | `PascalCase.tsx` for components, `camelCase.ts` for modules | `SpendingCard.tsx`, `useMutations.ts` | React component files match the component. |
| **TS component / type / interface** | `PascalCase` | `SpendingCard`, `MutationEvent` | Mirror backend type names where they cross the WS boundary. |
| **TS variable / function** | `camelCase` | `spendingSummary`, `handleMutation()` | |
| **WebSocket channel** | `snake_case` | `mutations`, `notifications` | |
| **Env var** | `NOVA_UPPER_SNAKE` | `NOVA_DATA_DIR`, `NOVA_CONTEXT_TOKEN_BUDGET` | Always `NOVA_` prefixed. |
| **Branch** | `type/short-desc` | `feat/finance-budgets` | See §9. |

### 2.2 Verb lexicon (use the right verb, always the same verb)

Consistency of verbs lets a reader predict behavior from a name. Use exactly these:

| Verb | Means | Never means |
|---|---|---|
| `get_` | Read one/many, no side effects, no compute-heavy work | Anything that writes |
| `list_` | Read a collection | A single item |
| `build_` / `compute_` | Pure computation, returns a value | Anything that persists |
| `add_` / `create_` / `log_` / `save_` | Create + persist a new record | An update |
| `update_` | Mutate an existing record | A create |
| `complete_` / `ship_` / `acknowledge_` | Domain state transition | A generic update — use the specific verb |
| `delete_` / `remove_` | Remove a record | A soft-hide (use `archive_`) |
| `run_` | Execute a job/pipeline (may be async) | A pure getter |
| `route_` / `dispatch_` | Send to a handler | Business logic |
| `parse_` | Text/bytes → structured data, may raise | Anything that persists |
| `handle_` | Entry point for an event/tool/input | A pure helper |

**`get_` MUST be side-effect free.** If a reader sees `get_spending_summary()` they must be able to call it a thousand times with no consequence. A "getter" that writes is a defect caught in review.

### 2.3 Anti-names (rejected in review)

- `data`, `info`, `obj`, `item`, `temp`, `val`, `result` as a *final* name (fine as a genuinely-generic local in a 3-line helper).
- `Manager`, `Helper`, `Util`, `Handler` classes that are grab-bags. (`ToolHandler` is fine — it is a precise role.)
- `process()`, `do()`, `execute()` with no object. Say what it processes.
- Abbreviations that aren't domain-standard. `cfg`, `usr`, `btn` — no. `id`, `db`, `ws`, `api`, `ui` — yes (established).
- Numbered suffixes: `handle2()`, `TaskV2`. Version the package or migrate, don't fork the name.

### 2.4 Claude tool names are contracts, not labels

Per `AI_CONTRACTS.md` §2.1, a tool's `name` and `description` are a **behavioral contract with Claude** — changing them changes routing behavior. Therefore:

- A tool name MUST be a plain imperative verb phrase Claude can reason about (`get_spending_summary`, not `spendingSummaryV2`).
- A tool name MUST match the domain function it fronts (1:1). If `finance.get_spending_summary()` exists, the tool is `get_spending_summary`.
- Renaming a tool is a **contract change** — it follows §11's rules (register in `AI_CONTRACTS.md`, same PR).

---

## 3. File & Unit Size Limits

Size limits are proxies for "one responsibility." They are enforced by a CI check (§3.8). A number below is a **hard ceiling**, not a target — most files should be well under it.

### 3.1 The limits table

| Unit | Soft target | **Hard limit** | On breach |
|---|---|---|---|
| **File / module** | ≤ 300 lines | **500 lines** | Split by responsibility (§3.7). |
| **Function / method** | ≤ 40 lines | **75 lines** | Extract named helpers. |
| **Class** | ≤ 200 lines | **300 lines** | The class does too much; decompose. |
| **Nesting depth** | ≤ 3 | **4** | Guard-clause / early-return; extract inner block. |
| **Function parameters** | ≤ 4 | **6** | Group related params into a `@dataclass`. |
| **Cyclomatic complexity** | ≤ 8 | **12** | Split branches into named functions. |
| **Returns per function** | — | (no limit) | Early returns are *encouraged*, not counted. |
| **Direct imports per module** | ≤ 12 | **20** | High imports = the module coordinates too much. |
| **Public symbols per package `__init__`** | ≤ 15 | **25** | A wide public API is a wide blast radius. |
| **Decorators per function** | — | **2** (see §1.8) | Beyond the sanctioned set requires an ADR. |
| **Boolean params** | 0 | **1** | A second boolean flag means the function has two behaviors — split it. |

TypeScript/React (desktop) uses the same file/function/nesting numbers. A React component file over 300 lines is split into subcomponents; a component with more than ~8 props takes a typed props object.

### 3.2 Maximum file size — 500 lines

A file is one unit of understanding. Beyond ~500 lines a reader cannot hold it in their head. The runtime already models this: `conversation.py`, `mutation_builders.py`, `mutation_chat.py`, `side_effects.py`, `domain_events.py`, `events.py` are *separate files* because each is one job. When your file grows, that is the signal you have grown a second responsibility.

### 3.3 Maximum function size — 75 lines

If a function is longer, it is a paragraph that wants to be several. Extract the middle into a named helper — the helper's name becomes documentation. A 75-line function with a comment every 8 lines is 9 functions in a trench coat.

### 3.4 Maximum class size — 300 lines

Applies to the rare classes Nova has (data + light behavior). If a class exceeds 300 lines it is holding state that should be split, or logic that should be free functions. Recall §1.7: prefer a module of functions over a big class.

### 3.5 Maximum nesting — 4

```python
# BAD — 5 levels, unreadable
def f(items):
    for x in items:
        if x.ok:
            if x.amount:
                for y in x.parts:
                    if y.valid:
                        ...

# GOOD — guard clauses + extraction
def f(items):
    for x in items:
        if not x.ok or not x.amount:
            continue
        _process_parts(x.parts)
```

### 3.6 Maximum parameters — 6, maximum booleans — 1

Long signatures hide missing structure. Two booleans mean two functions.

```python
# BAD
def build_event(title, date, time, all_day, notify, recurring, private): ...

# GOOD
@dataclass
class EventSpec:
    title: str
    date: str
    time: str | None = None
    all_day: bool = False
    notify: bool = False

def build_event(spec: EventSpec): ...
```

### 3.7 When code MUST be split

Split when **any** of these is true — the size number is only the last of them:

1. The file/function has more than one reason to change (two responsibilities).
2. You cannot name it without "and" (`load_and_transcribe` → two functions).
3. A hard limit in §3.1 is exceeded.
4. Part of it is pure and part is effectful (§1.5) — split at that seam.
5. A subset of it is independently testable — that subset wants to be its own function.
6. Two callers each use a different half.

Split **along responsibility seams**, never mechanically at "line 250." A bad split (cutting a cohesive function in half) is worse than a long cohesive function — but a long cohesive function is rare; usually length *is* two responsibilities.

### 3.8 Enforcement

`scripts/dev/check_limits.py` runs in CI and fails the build on any hard-limit breach. `flake8` (with `max-complexity`) and `mypy` run alongside. Limits are not style opinions once merged — they are gates.

---

## 4. Code Review Checklist

Every PR is reviewed against this list. A reviewer who cannot check a box requests changes. **Approving a PR means you personally verified every applicable box.**

### 4.1 The checklist (copy into every PR review)

**Architecture & boundaries**
- [ ] No sideways deps (Service→Service, Domain→Domain) and no downward deps (Core→Domain). Cross-boundary collaborators are **injected**, not imported (§1.8).
- [ ] Domains persist only via the `nova.core.memory` public API — no direct DB access, no raw SQL in a domain.
- [ ] Brain is the only Claude client. No other package imports `anthropic` or calls the API.
- [ ] Every write produces a `MutationEvent`; no `MutationEvent` is fabricated without a real domain write (runtime invariant).
- [ ] New public API is exported deliberately in `__init__.py`; nothing else leaks.

**Readability**
- [ ] Names follow §2 (verb lexicon, tables plural, events `entity.pastverb`, no anti-names).
- [ ] Sizes within §3 hard limits; nesting ≤ 4; ≤ 1 boolean param.
- [ ] A stranger could read it top-to-bottom without running it (§1.6).

**Correctness & error handling**
- [ ] Errors handled per §6: expected failures return typed results or raise a Nova exception; nothing swallows an exception silently *except* the explicitly-sanctioned background paths.
- [ ] External calls (Claude, Calendar, network, DB) have a timeout and a degradation path (§6, §7).
- [ ] Edge cases named in the PR description are covered by tests.

**Testing**
- [ ] New pure logic has unit tests; new tool/mutation path has an integration test; new boundary has a contract test (§5).
- [ ] Tests assert behavior, not implementation. No test mocks the DB (§5.7).
- [ ] Golden tests updated intentionally, with the diff explained, if output shape changed.

**Performance**
- [ ] No N+1 query on a read path; queries are indexed (§7.3).
- [ ] Conversation-turn work stays within the latency budget (§7.1); heavy work is deferred to a background job.
- [ ] No unbounded allocation (e.g. loading a whole table to count rows).

**Security**
- [ ] No secrets in code, tests, logs, or fixtures. Secrets come from env (`NOVA_*`).
- [ ] All SQL is parameterized (no f-string SQL). All external input is validated at the edge.
- [ ] Subprocess / AppleScript / shell calls take no unsanitized user string.
- [ ] No user PII written to logs (§6.2).

**Documentation**
- [ ] Public functions have docstrings (§8.2). Package README updated if the public surface changed.
- [ ] An ADR exists if a non-obvious decision was made (§8.4).
- [ ] `AI_CONTRACTS.md` updated if a Claude-facing contract changed (tool, extraction, reflection).

**Logging & observability**
- [ ] Log lines are structured and leveled per §6.2; no `print` in library code.
- [ ] Failures are logged with enough context to diagnose (what op, what ids — never secrets/PII).

**Coupling & complexity**
- [ ] The change touches the minimum number of packages. A PR that edits Core + three Domains is a design smell — question it.
- [ ] No new duplication that §10 wouldn't allow; no premature abstraction §10 would reject.

### 4.2 PR size and scope

- A PR **SHOULD** be < 400 lines of diff (excluding generated files, lockfiles, golden fixtures). Larger needs a "why this can't be split" note.
- One PR = one intent. "Refactor + feature" is two PRs. "Fix + reformat the file" is two PRs (the reformat drowns the fix).
- A PR MUST leave the build green: `black --check`, `isort --check`, `flake8`, `mypy`, and the full test suite pass.

### 4.3 Example — a GOOD PR

> **Title:** `feat(finance): add monthly budget ceiling per category`
> **Diff:** ~180 lines across `nova/domains/finance/budgets.py` (new, 90 lines), `nova/core/memory/finance_queries.py` (+1 query), `tests/unit/test_budgets.py` (new), `tests/integration/test_budget_tool.py` (new), migration `012_add_budgets_table.py`, `AI_CONTRACTS.md` (new tool row), `finance/README.md` (+1 section).
> **Why it's good:** single intent; one new table via migration (additive, §5.5-style expand-only); pure `compute_budget_status()` unit-tested, tool path integration-tested; new `set_budget` tool registered as a contract; no boundary crossed (persists via memory API); names follow the verb lexicon; every function < 40 lines. Reviewer can check every box.

### 4.4 Example — a BAD PR (and why it's rejected)

> **Title:** `misc fixes and cleanup`
> **Diff:** ~1,600 lines. Renames `MutationEvent.entity` → `.payload` across 40 files; adds a `finance` import into `wellness`; introduces a `BaseDomain` class every domain now inherits from; adds a `datetime.now()` inside `build_daily_plan()`; wraps a DB call in `try: ... except: pass`; adds SQL built with an f-string; no new tests; "will add tests later."
> **Why it's rejected, line by line:**
> - **Multi-intent** — rename + feature + refactor in one PR (§4.2).
> - **Sideways dependency** — `wellness` importing `finance` breaks the boundary (§1.8, §4.1).
> - **Inheritance for reuse** — `BaseDomain` violates composition-over-inheritance (§1.7).
> - **Hidden non-determinism** — `datetime.now()` inside pure logic (§1.4); inject `now`.
> - **Swallowed exception** — `except: pass` outside a sanctioned background path (§6).
> - **SQL injection** — f-string SQL (§4.1 security).
> - **Contract renamed silently** — `MutationEvent` field rename touches a frozen contract with no ADR, no `AI_CONTRACTS.md`/spec update.
> - **No tests** — every clause above is untested.

---

## 5. Testing Standards

Tests exist to let a future engineer change Nova without fear. They test **behavior and contracts**, not internals.

### 5.1 The test pyramid (and where Nova's live)

```
apps/backend/tests/
├── conftest.py            # shared pytest fixtures (real temp DB, fake Claude)
├── unit/                  # pure logic, no I/O — the widest layer
├── integration/           # tool → mutation → memory, real SQLite temp DB
├── contract/              # Brain↔Claude JSON contracts, WS event shapes
├── golden/                # stable-output snapshots (briefings, prompts)
├── architecture/          # boundary/dependency enforcement
└── e2e/                   # full pipeline, thin (a handful)
```

### 5.2 Unit tests — the foundation

- Test **pure functions** in isolation: `tool_calls_to_mutations()`, `build_daily_plan()`, `compute_budget_status()`, date/amount parsers, context ranking.
- No database, no network, no threads, no Claude. If a unit test needs a mock, the code under test probably isn't pure — fix the code, not the test.
- Fast: the whole unit suite runs in seconds. One assertion-concept per test.

### 5.3 Integration tests — the real spine

- Exercise a **real path** end of one seam to another: a tool call → mutation → a real write to a **real temp SQLite DB** → a read-back assertion. `test_tool_dispatch.py` is the archetype.
- Use a real temporary database (a `tmp_path` fixture), never a mocked DB. The DB is the thing most likely to break; mocking it tests nothing.
- Claude is the one thing faked here (a scripted fake that returns canned tool_use blocks) — because it is non-deterministic and costs money.

### 5.4 Architecture tests — boundaries as code

The dependency rules in §1.8 are not honor-system; they are tested.

- `tests/architecture/test_dependencies.py` imports each package and asserts its import set: `nova.services.*` MUST NOT import `nova.domains.*` or another service; `nova.domains.X` MUST NOT import `nova.domains.Y`; nothing but Brain imports `anthropic`; `nova.core.contracts` imports only stdlib.
- A boundary violation **fails CI**. This is the single most important test category for 5-year maintainability — it is what stops erosion.

### 5.5 Contract tests — the AI edge and the WS edge

- Every contract in `AI_CONTRACTS.md` has a test: the extraction envelope validates via `parse_extraction()`; the reflection JSON parses to the documented shape; each `MutationEvent` → WebSocket event mapping produces the documented `event_type`.
- Contract tests assert the **shape at the boundary**, decoupled from either side's internals. They are what let Brain and the desktop evolve independently.

### 5.6 Golden tests — stable outputs

- For outputs whose exact form matters (morning briefing text, assembled system prompt structure, evening wrap-up), store a golden snapshot and diff against it.
- A golden diff MUST be reviewed as a deliberate change — updating the snapshot without reading the diff defeats the test. Golden fixtures live in `tests/golden/fixtures/` and are regenerated by an explicit `--update-golden` flag, never automatically.

### 5.7 E2E tests — thin and few

- A small number covering the whole pipeline (wake → transcribe(fake) → route(fake Claude) → mutate → persist → event). They catch wiring breaks the composition root introduces.
- Kept few because they are slow and broad. E2E failures point you at integration/unit tests for the real diagnosis.

### 5.8 Mocking philosophy

**Mock the boundary, never the interior.**

| Mock this | Because |
|---|---|
| Claude / the Anthropic client | Non-deterministic, costs money, slow. Use a scripted fake. |
| External HTTP APIs (weather, GitHub, RSS) | Network, flaky, rate-limited. |
| Wall clock / RNG | Injected already (§1.4); pass a fixed value. |
| Audio hardware, AppleScript, macOS app control | No hardware in CI. |

**Never mock these** (mocking them tests the mock, not Nova):

- **The database.** Use a real temp SQLite. This is a hard rule (§5.3).
- **`nova.core.contracts`** types — they are pure data; construct real instances.
- **Pure functions under test** — if you're mocking a pure function, you're testing the wrong layer.
- **The function under test itself**, or its private helpers via patching internals. Test through the public API.

Prefer **fakes** (a small real implementation, e.g. an in-memory scripted Claude) over **mocks** (assertion-on-calls). Fakes survive refactors; call-count mocks break on every refactor and test nothing about behavior.

### 5.9 Coverage expectations

Coverage is a floor to catch *untested code*, not a target to game.

| Layer | Line coverage floor | Notes |
|---|---|---|
| `nova.core.*` (runtime, memory, contracts) | **90%** | The foundation; everything depends on it. |
| `nova.domains.*` | **85%** | Business logic + persistence. |
| `nova.services.*` | **75%** | Hardware/OS edges partly uncoverable in CI. |
| Composition root, `main.py` | **60%** | Wiring; covered mostly by E2E. |
| Overall repo gate | **80%** | CI fails below this. |

A PR MUST NOT lower a package below its floor. 100% coverage is never a goal — a test that exists only to touch a line is noise.

### 5.10 What a test must and must not do

- MUST assert observable behavior (return value, DB row written, event emitted).
- MUST be deterministic — no reliance on real time, real network, sleep-based timing, or test ordering.
- MUST NOT assert private internals, log strings (unless the log *is* the contract), or call counts of pure helpers.
- MUST clean up (temp DBs via `tmp_path`; no writes to `data/`).

---

## 6. Error Handling Standards

Nova's error posture follows the runtime spec exactly: **the conversation pipeline must survive**, and **background failures are logged, not fatal**. The rules below make that concrete.

### 6.1 Exceptions

**Three tiers of failure:**

1. **Expected, recoverable** (validation failure, "task not found," empty input). Do **not** raise across a boundary — return a typed result the caller can act on (a `Result`/`Optional`, or a domain confirmation string per the tool contract). Tools return their confirmation string even on the "nothing to do" path.
2. **Unexpected but survivable** (a memory-producer throws mid-turn, a WS subscriber errors, an API is down). **Catch at the boundary, log, degrade** (§6.5). The turn continues. This is the runtime's "best-effort, logged on exception" rule for `finalize_mutations`.
3. **Fatal / cannot-continue** (DB file corrupt at boot, model weights corrupt, config missing at startup). Raise, log fatally, exit. Better a clean crash at boot than silent wrongness at runtime.

**Rules:**
- Define Nova exceptions in `nova.core.contracts` (e.g. `ExtractionParseError`, `MemoryWriteError`). Domains raise **domain-specific** exceptions, never bare `Exception`.
- **`except: pass` is banned.** Every `except` either handles, degrades-with-log, or re-raises. The *only* sanctioned silent-ish path is a background daemon thread (§6.7), and even there it logs.
- Never catch broader than you handle. Catch `sqlite3.OperationalError`, not `Exception`, unless you are the top-of-turn boundary whose job is "never let the turn die."
- Never use exceptions for normal control flow.
- Exception messages state **what failed and what was being attempted**, with ids — never secrets or PII.

### 6.2 Logging

- Use Python `logging` with a module logger (`logger = logging.getLogger(__name__)`). **No `print`** in library code (the run loop's user-facing lines are the one exception, and they go through the voice/console output layer, not `logging`).
- **Levels:**
  - `DEBUG` — developer detail (RMS levels, token budget math, per-tool timing).
  - `INFO` — lifecycle events (boot phases, reflection scheduled, N mutations finalized).
  - `WARNING` — degraded but handled (API retry, context trimmed to budget, extraction batch retried).
  - `ERROR` — an operation failed and was abandoned (memory producer threw, WS publish failed).
  - `CRITICAL` — startup-fatal (DB corrupt, weights corrupt).
- **Structured context:** log the operation and identifiers (`logger.error("memory producer failed", extra={"event_type": e.event_type, "entity_id": e.entity["id"]})`). Enough to diagnose, never enough to leak.
- **PII/secrets never logged.** No transcripts at INFO+, no amounts tied to identity in shared logs, no API keys, ever. Voice transcripts are DEBUG-only and off in production.

### 6.3 Retries

- Retry **only** idempotent, transient-failure operations: a Claude call that timed out, an HTTP GET to weather/GitHub, an extraction batch (already bounded by `EXTRACTION_MAX_ATTEMPTS`).
- **Bounded and backed-off:** max attempts is a named constant; use exponential backoff with jitter. Never retry in a tight loop.
- **Never retry a write that may have partially applied** unless it is idempotent by construction. Nova's mutation atomicity (all-or-nothing per turn) is what makes the turn safe to *not* retry.
- Retrying is a `WARNING`; exhausting retries is an `ERROR` plus the degradation path.

### 6.4 Recovery

- Recover to a **known-good state**, not a guessed one. If context assembly fails, fall back to the minimal always-on context (calendar + profile), never to an empty prompt that changes Claude's behavior invisibly.
- On a failed write, the turn's mutations are atomic — either the whole set committed or none did; there is no half-state to reconcile (runtime guarantee).

### 6.5 Graceful degradation

Nova degrades toward "less capable but honest," never "silently wrong":

| Subsystem down | Degrade to |
|---|---|
| Weather API | Briefing omits weather, says so; does not block the briefing. |
| Semantic recall (LanceDB) | Fall back to recent conversation history only; log WARNING. |
| Entity extraction | Skip; memories persist un-extracted, retried later (idempotent). |
| Calendar service | Tools that need it return a clear "calendar unavailable" confirmation; other tools unaffected. |
| Claude | See §6.9 — the turn cannot proceed; fail honestly to the user. |

Degradation MUST be user-honest when it changes an answer ("I couldn't reach the calendar just now"), and silent-but-logged when it doesn't (a dropped memory producer).

### 6.6 Fatal errors

Reserved for boot-time invariants (per runtime spec: network down / disk full / corrupt weights halt startup). Fatal = log `CRITICAL` with the exact cause and remediation, then exit non-zero. Do **not** limp forward in a degraded boot that produces subtly wrong behavior.

### 6.7 Background-thread failures

The runtime spawns daemon threads (entity extraction, reflection sweep). Per spec, their failures are **logged, not re-raised** — they must never crash the main run loop.

- Every background thread body is wrapped in a top-level `try/except Exception` that **logs at ERROR with full context** and exits the thread cleanly.
- A background failure MUST leave persistent state consistent (idempotency markers like `extraction_attempts` let the work be retried next cycle).
- A background thread MUST NOT write to shared mutable state without the ownership rules in the runtime spec (append-only lists, replace-only caches). No new locks without an ADR.

### 6.8 Database failures

- All DB access is through `nova.core.memory`. Each op is its own connection + transaction (per runtime spec: open → transaction → commit/rollback → close, ~1–10ms).
- On `OperationalError`/`IntegrityError`: roll back, log ERROR with the operation and entity, raise a `MemoryWriteError` to the caller boundary. The domain surfaces an honest failure confirmation; the pipeline survives.
- A corrupt DB at boot is fatal (§6.6). A single failed write at runtime is survivable and never corrupts the turn (atomicity).
- **No partial commits.** One turn's mutations commit together or not at all.

### 6.9 Claude failures

Claude is the one dependency the conversation turn cannot degrade around — if reasoning is unavailable, there is no answer to give.

- **Timeout** every Claude call (a named constant). On timeout: one bounded retry (§6.3), then fail the turn honestly ("I'm having trouble thinking right now — try again in a moment"). Never fabricate a response.
- **Malformed structured output** (extraction/reflection JSON): apply the contract's failure semantics from `AI_CONTRACTS.md` — **strict envelope, lenient items**. An envelope violation raises the contract error and the batch stays pending for retry; a single malformed item is dropped while the rest proceed. Never write unvalidated Claude output straight to the DB.
- **Rate limit / API error:** log WARNING, back off, surface an honest "try again" to the user; do not spin.
- Claude output is **never trusted as safe input**: tool arguments Claude produces are validated against the tool's `input_schema` before dispatch; a tool handler validates its own inputs again before it acts (defense in depth).

---

## 7. Performance Standards

Nova is a single-process, on-device assistant. Performance is judged by **perceived responsiveness of a conversation turn** and by **not melting the user's laptop**. Numbers below are budgets, checked in review, not micro-optimization mandates.

### 7.1 Latency budgets (per conversation turn)

The turn is synchronous on the main thread up to the spoken reply; everything else is deferred. Budgets for the code Nova owns (excluding Claude's own thinking time and first-run model download):

| Phase | Budget (owned code) | Notes |
|---|---|---|
| Context assembly (gather, rank, budget, format) | **≤ 150 ms** | DB reads + LanceDB query + formatting. |
| Tool dispatch + mutation build (per turn) | **≤ 50 ms** | Pure transform + writes. |
| DB write per mutation | **≤ 10 ms** | Matches runtime spec's transaction lifetime. |
| `finalize_mutations` (validation + WS publish, sync part) | **≤ 30 ms** | Memory production + extraction are deferred, not counted. |
| **Total owned overhead per turn (excl. Claude, excl. audio I/O)** | **≤ 250 ms** | If a change pushes past this, defer work to background. |

Claude round-trip and audio capture/TTS are inherent latency, not Nova's overhead — but they MUST NOT be made worse (e.g. don't send a bloated system prompt; respect the token budget).

### 7.2 Do-not-block rules

- The main run loop MUST NOT block on anything deferrable. Entity extraction, reflection, and memory production run in background threads exactly because they are off the critical path (runtime spec). New heavy work follows the same rule: if it isn't needed to produce *this* reply, it is a background job.
- Wake-word polling yields ~50 ms/iteration and stays CPU-local — do not add I/O to that loop.

### 7.3 Database query expectations

- **No N+1.** Loading N tasks then querying each one's detail in a loop is a review reject. Batch or join.
- Every query on a growing table hits an **index** (id, foreign keys, `created_at`, and any column used in a `WHERE`/`ORDER BY` on a read path). Adding a query that scans a full table on a hot path requires an index in the same PR.
- **Read only what you need.** No `SELECT *` into memory to compute a count; ask the DB to count. No unbounded `get_all()` on an append-only table — bound by time window or limit (`get_money_since(period)`, not `get_all_money()`).
- Each op is one short transaction (§6.8). Do not hold a transaction open across a Claude call or any I/O.

### 7.4 Caching rules

- Cache only what is **expensive and stable**: the loaded Whisper model, the profile-observations cache, brain history (bounded to ~20 turns, oldest dropped — per runtime spec). These are loaded once at init and updated in place.
- Every cache has a defined **invalidation/refresh** rule and a **bound**. An unbounded cache is a memory leak; a cache with no invalidation is a correctness bug.
- Do **not** cache to paper over an N+1 or a slow query — fix the query.
- `functools.lru_cache` only on **pure** functions with hashable args and a `maxsize`.

### 7.5 Threading rules

- Concurrency model is fixed by the runtime spec: **main thread owns the run loop; background daemon threads do deferred work.** Do not introduce a new long-lived thread, a thread pool, or `asyncio` in the backend without an ADR — it changes the concurrency model the spec froze.
- Shared state between main and background threads follows the spec's ownership rules: append-only lists, replace-only caches, idempotent background writes. No new shared mutable state without a documented ownership + synchronization rule.
- Background threads are `daemon=True`, wrapped per §6.7, and never block shutdown.

### 7.6 Async rules (desktop / frontend)

- The desktop (Electron/React/TS) is async by nature. Rules: never block the UI thread; all backend calls go over the WebSocket/IPC boundary; render from `MutationEvent`s pushed by the backend, don't poll.
- No unbounded state growth in the renderer — the mutation stream is consumed and reduced, not accumulated forever.

### 7.7 Memory usage

- Steady-state backend RSS SHOULD stay modest (dominated by the Whisper model, ~hundreds of MB). A change that adds a large in-memory structure that grows with usage (an unbounded list, a per-turn accumulation) is a leak — bound it.
- Load large artifacts (models, embeddings) **once** at init; never per turn.
- LanceDB / vector data lives on disk and is queried, not fully loaded into RAM.

### 7.8 When to optimize

Measure first. Optimize a path only when a budget in §7.1 is breached or a profiler shows it hot. Speculative optimization that costs readability is rejected under §1.1. Correct-and-boring beats fast-and-clever until a number proves otherwise.

---

## 8. Documentation Standards

Documentation is code's memory. Nova documents at four levels: package README, docstrings, ADRs, and inline comments. Each has a job; none repeats another.

### 8.1 Package README (every package)

Every `nova.<tier>.<name>` package has a `README.md` answering, in order:

1. **Responsibility** — one sentence: what this package owns (mirror the eng spec's "Owns" line).
2. **Public API** — the functions other packages may call, each one line. This is the contract.
3. **Depends on / may be called by** — the boundary (copy from the eng spec's dependency table).
4. **Never does** — the explicit non-responsibilities (the eng spec lists these; restate them).
5. **Key files** — a one-line map of the modules.

If a PR changes the public API, it updates the README in the same PR (checklist §4.1).

### 8.2 Docstrings

- **Every public function/class** has a docstring: one-line summary (imperative — "Log a completed task."), then Args/Returns/Raises when non-obvious.
- Docstrings describe **contract and intent** (what it guarantees, what it raises, side effects), not mechanics the code already shows.
- Private helpers (`_name`) need a docstring only when their purpose isn't obvious from name + body.
- Type hints are **mandatory** on every public signature (`mypy` enforces). A docstring never restates a type the signature already gives.

```python
def complete_task(task_id: int, *, now: datetime) -> str:
    """Mark a task done and return the spoken confirmation.

    Persists via memory.update_task. Produces a `task.completed`
    MutationEvent upstream in the runtime.

    Raises:
        TaskNotFoundError: if no task has this id.
    """
```

### 8.3 Comments

- Comment **why**, never **what**. `# retry: weather API is flaky at the top of the hour` earns its place; `# increment i` does not.
- A comment that explains *what* the code does is a signal to rename or extract until the code says it itself.
- Mark debt precisely: `# DEBT(nova-1234): reflection contract is prose-canonical; migrate onto extraction_contract mechanism.` — with a tracking id, matching how `AI_CONTRACTS.md` records debt. Bare `# TODO` with no id is rejected.
- No commented-out code in a merged PR. Delete it; git remembers.

### 8.4 Architecture Decision Records (ADRs)

- An ADR is required for any decision that is **non-obvious, hard to reverse, or crosses a boundary**: a new dependency, a new thread/async, a new decorator beyond the sanctioned set, a schema change, a contract change, a deviation from a SHOULD.
- Location: `docs/adr/NNNN-short-title.md`. Format: **Context → Decision → Consequences → Alternatives considered**. One page.
- ADRs are append-only and immutable once accepted; a reversed decision is a *new* ADR that supersedes the old one (link both). This is the record that keeps year-5 engineers from re-litigating year-1 choices.
- An ADR records the *decision and its trade-off*; it does **not** re-open the frozen architecture.

### 8.5 Examples

- Public APIs with any subtlety carry a runnable example in the docstring or README.
- Examples MUST stay correct — an example in a docstring is verified by a doctest or an integration test if it's load-bearing. A wrong example is worse than none.

### 8.6 What NOT to document

- Do not restate a contract that has a code source of truth — point at it (`AI_CONTRACTS.md`'s cardinal rule: index, don't re-define).
- Do not write architecture prose here that belongs in the frozen specs — link to them.

---

## 9. Git Standards

### 9.1 Branch naming

`type/short-kebab-description`, where `type` ∈ `feat | fix | refactor | test | docs | chore | perf | hotfix`.

Examples: `feat/finance-budgets`, `fix/calendar-timezone`, `hotfix/db-boot-crash`, `refactor/split-mutation-builders`. One branch = one intent (matches §4.2).

### 9.2 Commit messages

Conventional Commits, imperative mood:

```
<type>(<scope>): <summary ≤ 72 chars>

<body: what and why, wrapped at 72 cols. Not "how" — the diff shows how.>

<footer: refs #issue, BREAKING CHANGE:, contract/ADR references>
```

- `type` matches the branch types. `scope` is the package/domain (`finance`, `runtime`, `memory`, `desktop`).
- Summary describes the change, not the file (`fix(memory): parameterize task query` not `edit memory.py`).
- **Atomic commits:** each commit builds and passes tests. No "wip" / "fix typo" / "address review" noise in the final history — squash-clean before merge.
- A commit that changes a Claude contract references `AI_CONTRACTS.md`; a commit implementing an ADR references it.

### 9.3 PR naming & description

- PR title = the primary commit summary (`feat(finance): add monthly budget ceiling per category`).
- PR body: **What / Why / How tested / Risk / Contracts touched**. The §4.1 checklist is the review template.
- Link the issue/roadmap item. A PR with no "why" is incomplete.

### 9.4 Merge strategy

- **Squash-merge** to `main` by default — one clean commit per PR, message per §9.2. History on `main` reads as a changelog.
- `main` is always releasable and always green. No direct pushes to `main`; everything is a reviewed PR.
- Rebase feature branches on `main`; do not create merge-commit spaghetti.

### 9.5 Versioning & release tags

- **Semantic Versioning** `MAJOR.MINOR.PATCH` for Nova Core.
  - **MAJOR** — a frozen contract or boundary breaks (should be extraordinarily rare; the architecture is frozen — see §12).
  - **MINOR** — a new domain, service, tool, or additive schema column (backward compatible).
  - **PATCH** — bug fix, no interface change.
- Release tags: `v1.4.0`, annotated, on `main`. The tag message is the release note (built from squash commits).
- Schema changes obey the spec's **expand-only within a version cycle** rule: add columns/tables, never remove them mid-cycle; a removal is a MAJOR with a migration + deprecation window.

### 9.6 Hotfix process

1. Branch `hotfix/<desc>` from the **release tag** (not `main` head, if `main` has unreleased work).
2. Minimal fix + a regression test that fails before, passes after. No refactors, no scope creep.
3. Fast-track review (still needs one approval and green CI — never skip the gate, even under pressure).
4. Tag a PATCH release; **forward-port** the fix to `main` in the same session so it can't regress.
5. A post-incident ADR or note if the root cause was systemic.

---

## 10. Refactoring Rules

Refactoring keeps Nova clean; *reckless* refactoring is how frozen architectures rot. These rules bound both.

### 10.1 When duplication is acceptable

- **Rule of three:** duplicate twice freely. On the **third** occurrence, consider abstracting — and only if the three cases are truly the same *concept*, not coincidentally-similar code.
- **Duplication across boundaries is preferred to coupling across boundaries.** Two domains that both format a date the same way SHOULD each keep their own small helper rather than one importing the other (that would be a banned sideways dependency). Shared truly-generic utility goes in `nova.core.contracts`/a sanctioned util, never in a peer domain.
- A little duplication that keeps two things independently changeable beats an abstraction that couples them. WET-but-decoupled > DRY-but-coupled at a boundary.

### 10.2 When abstraction is acceptable

- Abstract only when you have **three real cases** and a **stable shared concept** — never speculatively for "future flexibility." Speculative abstraction is rejected under §1.1.
- An abstraction MUST reduce total complexity, not relocate it. If the base class/generic is harder to understand than the duplication it removed, it fails.
- Abstractions live at the right tier: shared vocabulary in `contracts`, shared infra in `core`. Never abstract by having peers depend on each other.

### 10.3 When to delete code

- Delete dead code the moment it's dead — no `# in case we need it`. Git is the archive.
- Delete a feature's code with the feature. Orphaned code is a maintenance tax and a security surface.
- Removing public API follows §9.5 deprecation (mark deprecated → migrate callers → remove in a later cycle). Removing private/dead code is immediate.

### 10.4 When to rewrite

- Rewrite a **module** (not the system) only when: it repeatedly breaks, no one understands it, and it has test coverage to rewrite *against*. Write the characterization tests first, then rewrite behind them.
- Rewrites are their own PR (§4.2), boundary-preserving (same public API), and reviewed against golden/contract tests to prove behavior is unchanged.
- **Never** rewrite across a frozen boundary or "improve" the architecture — that is out of scope by decree (§0). A rewrite that changes the public contract is a contract change (§11/§9.5), not a refactor.

### 10.5 When to leave it alone

- If it works, is tested, is within size limits, and no one is changing that area — **leave it**. Churn for aesthetics is risk with no reward.
- Do not reformat/rename in a PR whose purpose is a fix — it drowns the diff (§4.2).
- "I would have written it differently" is not a reason to change working, tested code. Consistency with the surrounding code beats your personal preference (write code that reads like its neighbors).

### 10.6 The refactor safety rule

Every refactor is **behavior-preserving and test-guarded**: green tests before, the same green tests after, no new behavior in the same PR. If you can't prove behavior is unchanged, you're not refactoring — you're changing the product, and that's a feature PR with its own tests.

---

## 11. AI Coding Rules

Most Nova code will be touched by an AI assistant. AI is a force multiplier for *this handbook*, not an exception to it. **Generated code is held to every standard above — the author of record is the human who opens the PR, and they own every line.**

### 11.1 The universal rule

> An AI assistant is a fast junior engineer with no memory and no accountability. It proposes; a human disposes. Every AI-produced line is reviewed by the §4 checklist exactly as if a human wrote it. "The AI wrote it" is never a defense in review.

### 11.2 How to instruct the assistants (all of them)

Point the assistant at this handbook and the frozen specs as ground truth. A good prompt includes:

- The **boundary** the change lives in (which package, what it may/may not import).
- The **contract** it must honor (tool schema, MutationEvent shape, DB schema).
- "**Follow `NOVA_ENGINEERING_HANDBOOK_v1`**: verb lexicon, size limits, inject dependencies, no sideways deps, tests required."
- The **tests** it must make pass.

The repo carries assistant config so this is automatic, not per-prompt discipline:

- **Claude Code** — `CLAUDE.md` at repo root + per-package `CLAUDE.md` where a package has sharp rules. It states the boundaries, the verb lexicon, "Brain is the only Claude client," and "run `black/isort/flake8/mypy/pytest` before proposing done."
- **Cursor** — `.cursor/rules/*.mdc` encoding the same boundaries and size limits, scoped by path glob (e.g. a `domains/**` rule that forbids importing another domain).
- **GitHub Copilot** — `.github/copilot-instructions.md` with the naming table and the "no f-string SQL / inject the clock / no `except: pass`" hard rules.
- **ChatGPT / other** — paste this handbook's §1–§3 and the relevant spec section into context; it has no repo access, so treat its output as a first draft to be reconciled with the real code by hand.

Keep these config files **in sync with this handbook** — when a rule here changes, the assistant configs change in the same PR (they are documentation of the same rules).

### 11.3 How generated code MUST be reviewed

AI output has characteristic failure modes; check them explicitly:

- **Invented APIs / hallucinated imports** — does every function/module it calls actually exist? (AI confidently calls `memory.get_all_tasks()` that was never defined.)
- **Boundary violations it can't see** — it will happily `import nova.domains.finance` from `wellness` because it doesn't know the rule. Run the architecture test.
- **Plausible-but-wrong logic** — off-by-one, wrong sign on an amount, timezone bugs, a `get_` that writes. Read it; don't skim.
- **Silent broadening** — it "helpfully" adds a `try/except Exception: pass`, a `datetime.now()`, an extra parameter, a second responsibility. Reject scope creep.
- **Stale patterns** — it may reproduce an old pattern from its training rather than the current codebase idiom. Match the neighbors.
- **Tests that test the mock** — AI loves mocking the DB. Reject per §5.8; demand a real temp-DB integration test.
- **Contract drift** — it edits a tool description or MutationEvent field without touching `AI_CONTRACTS.md`. Block it.

Run the full gate (`black --check`, `isort`, `flake8`, `mypy`, `pytest`, architecture + contract tests) on AI output before review, not after.

### 11.4 What AI MUST NEVER change automatically

Require an explicit human decision (and usually an ADR) for:

- **Anything in the frozen architecture** — package boundaries, the dependency graph, the "Brain is the only Claude client" rule, the MutationEvent invariant. AI may implement *within* the architecture; it may not redesign it.
- **Contracts** — Claude tool names/descriptions/schemas, extraction/reflection JSON shapes, WebSocket event types, MutationEvent fields. These are load-bearing across the whole system (`AI_CONTRACTS.md`).
- **Database schema** — no auto-generated migrations applied without human review; expand-only rule (§9.5) enforced by a human.
- **Security-sensitive code** — SQL construction, subprocess/AppleScript calls, secret handling, input validation at the edge. AI drafts; a human verifies parameterization and sanitization.
- **The composition root (`main.py`)** — the wiring is the one place the whole graph is knowable; changes are reviewed with extra care.
- **Deleting tests or lowering coverage floors** — never automatic.
- **Dependencies / `requirements.txt`** — a new third-party package is an ADR and a supply-chain review, not an AI import.
- **This handbook and the frozen specs** — AI may draft edits; only the Engineering Lead accepts them.

### 11.5 The one-sentence contract for AI contributions

> AI writes drafts inside the frozen architecture; humans own the merge, the boundaries, the contracts, and the consequences.

---

## 12. Long-term Maintainability

The architecture is frozen so that Nova can *grow* for a decade without a rewrite. This section is how the code stays as clean as the architecture, at each horizon.

### 12.1 The mechanisms that keep it clean (always on)

These run in CI on every PR, forever. They are what make cleanliness the default instead of a heroic effort:

1. **Architecture tests** (§5.4) — boundaries can't erode because a violated boundary fails the build.
2. **Size-limit gate** (§3.8) — files/functions can't bloat unnoticed.
3. **Coverage floors** (§5.9) — untested code can't sneak in.
4. **Contract tests** (§5.5) + `AI_CONTRACTS.md` DoD line — the AI edge can't drift silently.
5. **Expand-only schema rule** (§9.5) — the DB grows without breaking old data.
6. **One-intent PRs + squash history** (§4.2, §9.4) — `main` stays legible.
7. **ADRs** (§8.4) — decisions are remembered, not re-litigated.

Nova's growth model (new domains added as packages, no core changes — per the eng spec) means the codebase gets **wider, not deeper**. Maintainability is about keeping each new package as clean as the first, not about managing ever-growing entanglement.

### 12.2 Year 1 — establish the reflexes

- Every rule in this handbook is enforced by a check, not by memory. If a rule is being violated repeatedly, either the check is missing (add it) or the rule is wrong (change it via ADR) — never leave a rule that's honored only in spirit.
- New domains are the proving ground: each new `nova.domains.X` is added *without touching core* (eng spec §5 scenarios). If adding a domain requires a core change, stop — the change is either wrong or an ADR-worthy architecture question.
- Onboarding = read this handbook + the frozen specs + ship one small PR through the full gate.

### 12.3 Year 3 — resist entropy

- **Boundary audit** each cycle: run the architecture tests' report; any package whose import set is creeping toward its ceiling (§3.1) gets attention before it breaks a rule.
- **Debt ledger:** every `# DEBT(id)` and every prose-canonical contract (like §2.3 reflection) is tracked and burned down deliberately — turn prose contracts into code-canonical ones as the pattern in `extraction_contract.py` intended.
- **Dependency hygiene:** third-party deps are reviewed each cycle for staleness/CVE. Nova's small dependency surface (stdlib-heavy core, `anthropic`, `sqlite3`, `lancedb`, audio libs) is a feature — keep it small.
- **Test suite health:** flaky tests are fixed or deleted the week they appear; a tolerated flaky test trains engineers to ignore red, which is fatal.

### 12.4 Year 5 — the codebase outlives its authors

- **Docs are the memory.** By year 5 the original authors may be gone; the READMEs, ADRs, `AI_CONTRACTS.md`, and the frozen specs must still answer "why is it this way." Doc drift is treated as a bug (§8, checklist §4.1).
- **The architecture is still frozen.** Five years in, the pressure to "modernize the architecture" is strong and usually wrong. A genuine need is a MAJOR-version ADR with a migration plan — extraordinary, not routine. The default answer is: add a package, don't reshape the core.
- **Assistant configs are current.** The `CLAUDE.md` / Cursor / Copilot rules are still in lockstep with this handbook, so the AI writing most of the code in year 5 writes it to the year-1 standard.

### 12.5 Year 10 — graceful evolution

- A ten-year codebase survives by **replacing leaves, not the trunk.** A service (Voice's Whisper model, Calendar's AppleScript bridge) can be swapped wholesale because it is a leaf behind a stable public API — that is exactly why the architecture made services leaves. Domains can be deprecated and removed as a whole. The core runtime, memory abstraction, contracts, and the MutationEvent invariant are the trunk and change least.
- **Big migrations are staged, never big-bang:** deprecate → dual-run → migrate data → remove, each a reviewed step with tests, per the spec's schema-versioning discipline.
- The measure of success at year 10 is unchanged from year 1: *a new engineer, with this handbook and the specs, can ship a correct, tested, boundary-respecting change on their first week — without understanding the whole system.* If that's still true, the handbook did its job.

### 12.6 The maintainability contract

> Nova stays clean not because engineers are disciplined, but because the rules are checked, the boundaries are tested, the contracts are code, the decisions are recorded, and the architecture is frozen. Cleverness is optional. These mechanisms are not.

---

## Appendix A — The one-page rule card

Pin this. Everything above compresses to:

- **Boring, explicit, deterministic. Inject dependencies. No hidden magic.**
- **Boundaries:** Service→Core only. Domain→Core (+injected). Never sideways, never downward. Brain is the only Claude client. Domains persist only via `memory`. (Tested — §5.4.)
- **Naming:** verb-first functions, `PascalCase` types, plural `snake_case` tables, `entity.pastverb` events, `NOVA_` env vars. (§2.)
- **Size:** file ≤ 500, function ≤ 75, nesting ≤ 4, params ≤ 6, ≤ 1 boolean param. (§3.)
- **Errors:** no `except: pass`; parameterize SQL; the turn survives; background failures log, not crash; Claude output is validated, never trusted. (§6.)
- **Tests:** real temp DB (never mock it), mock only boundaries, contract-test the AI edge, coverage floors hold. (§5.)
- **Perf:** ≤ 250 ms owned overhead/turn; no N+1; defer heavy work to background threads. (§7.)
- **Git:** one-intent PRs, conventional commits, squash-merge, expand-only schema, SemVer. (§9.)
- **Refactor:** rule of three; decoupled-duplication > coupled-abstraction; behavior-preserving + test-guarded; leave working tested code alone. (§10.)
- **AI:** drafts inside the architecture; humans own boundaries, contracts, and the merge; generated code meets every rule here. (§11.)
- **The architecture is frozen. Add packages; don't reshape the core.** (§0, §12.)

---

*End of NOVA_ENGINEERING_HANDBOOK_v1. Mandatory for every contributor, human and AI. Changes to this handbook are made only by the Engineering Lead, via PR + ADR, and are mirrored into the assistant config files in the same change.*
