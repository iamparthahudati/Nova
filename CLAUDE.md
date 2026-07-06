# CLAUDE.md

Ground truth for this repo, in order of authority:

1. `docs/adr/*.md` — accepted architecture decisions. Immutable once accepted.
2. `docs/architecture/NOVA_CORE_RUNTIME_SPECIFICATION_v1.md` — how Nova executes.
3. `docs/architecture/NOVA_ENGINEERING_SPECIFICATION_v1.md` — how code is organized.
4. `docs/NOVA_ENGINEERING_HANDBOOK_v1.md` — how code is written, reviewed, tested.
5. `docs/NOVA_IMPLEMENTATION_ROADMAP_v1.md` — the PR-by-PR plan.

**The architecture is frozen.** Implement inside it; do not propose a redesign, a
new package taxonomy, or a new philosophy document. If implementation exposes a
real problem with the architecture, say so explicitly and stop — that is a
human decision (usually an ADR), not something to route around silently.

## Where things actually live (apps/backend)

The idealized `nova.core` / `nova.domains` taxonomy in the Engineering
Specification has not been physically restructured into those directories yet.
The real, current layout is:

```
apps/backend/
├── nova.py                  # composition root — run-loop entry point
├── identity.py, paths.py, conversation_memory.py, memory_producers.py
│                             # tiny, dependency-free shared helpers (root utils)
├── memory/                   # the ONLY package that touches sqlite3 / lancedb
├── runtime/                  # conversation pipeline, MutationEvent, side effects
├── services/
│   ├── voice/  calendar/  automation/     # leaves — no memory/runtime/service imports
│   ├── knowledge/            # -> memory, services.brain
│   ├── brain/                # -> memory (the ONLY package that calls the Claude API)
│   ├── planner/              # -> memory, services.calendar
│   └── api/                  # FastAPI facade -> memory, runtime, brain, calendar, planner
└── tests/
    ├── architecture/         # boundary tests — see below, run these first
    └── test_*.py
```

`tests/architecture/test_dependencies.py` is the single source of truth for
which package may import which. Read it before adding a new cross-package
import — if the edge you need isn't in `ALLOWED_EDGES`, that is a signal to
stop and ask, not to add the edge yourself.

Known, documented deviations from the idealized spec (do not silently "fix"
these — they are tracked debt, see the docstrings in
`tests/architecture/test_dependencies.py`):
- `runtime/conversation.build_tool_handlers()` imports every service to build
  the tool-name -> service-call map, because two independent entry points
  (`nova.py`'s voice/REPL loop and `services/api/routers/chat.py`) both need
  the identical mapping — deliberate shared-factory location, not an
  accident. `process_message`/`process_transcript` do take `tool_handlers`
  as an explicit parameter now (no hidden module-level global).
- `services/api` issues writes directly (`finalize_mutations`) per
  `docs/architecture/DESKTOP_WRITE_OPERATIONS.md` — this supersedes the
  "read-only API" line in the v1 roadmap's Milestone 4 DoD.

## Hard rules (Handbook §1, §5.4, Appendix A)

- **Brain is the only Claude client.** No other package references
  `ANTHROPIC_API_URL`, an `x-api-key` header, or calls the Anthropic API.
- **Memory owns persistence.** No other package opens a `sqlite3` or
  `lancedb` connection. Only `memory/semantic/` imports `lancedb`.
- **No sideways deps** (service -> service outside the documented edges) and
  **no downward deps**. Nothing imports `services.api` — it is the top of
  the graph.
- **No mutation without a `MutationEvent`.** Every write goes through
  `runtime/mutation_builders.py` -> `runtime/side_effects.finalize_mutations()`.
- Verb lexicon, naming, size limits (file ≤ 500, function ≤ 75, nesting ≤ 4,
  params ≤ 6, ≤ 1 boolean param): Handbook §2–§3.
- `except: pass` is banned. SQL is always parameterized. No `datetime.now()`
  inline in pure logic — inject the clock.
- Never mock the database in a test — use a real temp SQLite (`tmp_path`).

## Before proposing a change as done

Run, from `apps/backend/`, with the venv active:

```bash
black --check . && isort --check-only . && flake8 . \
  && python ../../scripts/dev/check_limits.py \
  && python -m pytest tests/ -q
```

`mypy memory runtime services *.py` is currently report-only in CI (pre-existing
type debt, see `pyproject.toml`'s `[tool.mypy]` comment) — run it and don't make
the error count worse, but a clean gate today is the four commands above plus
pytest, all green.

## AI contribution rules (Handbook §11.4)

Do **not** change these without an explicit human decision and usually an ADR:
package boundaries, the dependency graph, `MutationEvent`'s shape, Claude tool
schemas, the database schema, or anything in `docs/adr/`, the frozen specs, or
this file. You may draft changes to any of them for a human to review — you
may not merge a change to them yourself.
