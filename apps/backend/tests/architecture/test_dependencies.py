"""Boundary/dependency enforcement — Handbook §5.4, Eng Spec dependency rules.

This test encodes the *actual* import graph of `apps/backend` as it exists
today, not the fully-idealized `nova.core`/`nova.domains` taxonomy from
NOVA_ENGINEERING_SPECIFICATION_v1 (that package layout does not exist yet —
domain logic currently lives inside `memory/` and `services/planner/`).

Two things this test intentionally does NOT try to do, and why:

1. It does not require `runtime` to receive services purely via injection
   from a composition root external to `runtime/`. In the real codebase,
   `runtime/conversation.py` builds `TOOL_HANDLERS` itself by importing all
   services directly. This is a deviation from Eng Spec's "Runtime never
   imports Domains or Services" rule.
   DEBT(nova-arch-1): tracked for a follow-up PR to move TOOL_HANDLERS
   construction into `nova.py` (the actual composition root) and pass it
   into `runtime.conversation.process_message()` as a parameter.

2. It does not forbid `services.api` from importing `runtime` and issuing
   writes (`finalize_mutations`) directly from REST routers. That is the
   *documented, approved* design in `docs/architecture/DESKTOP_WRITE_OPERATIONS.md`
   ("every write producer ... converges on one pipeline"), which supersedes
   the stray "API is read-only" line in the v1 roadmap's Milestone 4 DoD.

Every other sideways edge (Service -> Service outside the pairs below,
anything -> `services.api`) is a real, enforced violation.
"""

from __future__ import annotations

import ast
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]

# First-party top-level names. Anything else (stdlib, third-party) is ignored.
FIRST_PARTY_ROOTS = {
    "memory",
    "runtime",
    "services",
    "identity",
    "paths",
    "conversation_memory",
    "memory_producers",
}

# Tiny, dependency-free shared helpers with no I/O and no business logic.
# Not yet split into a `core`/`contracts` package (Eng Spec's aspirational
# taxonomy), but behave like one today: any unit may import these.
ROOT_UTILS = {"identity", "paths", "conversation_memory", "memory_producers"}

# unit name -> allowed first-party dependencies (beyond ROOT_UTILS, always allowed)
ALLOWED_EDGES: dict[str, set[str]] = {
    "services.voice": set(),
    "services.calendar": set(),
    "services.automation": set(),
    "services.knowledge": {"memory", "services.brain"},
    "services.brain": {"memory"},
    "services.planner": {"memory", "services.calendar"},
    "services.api": {
        "memory",
        "runtime",
        "services.brain",
        "services.calendar",
        "services.planner",
    },
    "memory": set(),
    "runtime": {
        "memory",
        "services.voice",
        "services.calendar",
        "services.automation",
        "services.knowledge",
        "services.brain",
        "services.planner",
    },
}

# Root-level composition/entry-point scripts are exempt — they are allowed
# to see the whole graph by design (same role as `nova/main.py` in the spec).
EXEMPT_UNITS = {"root", "tests"}


def _unit_for(path: Path) -> str:
    """Classify a source file into the package/unit it belongs to."""
    rel = path.relative_to(BACKEND_ROOT)
    parts = rel.parts
    if parts[0] == "tests":
        return "tests"
    if parts[0] == "services" and len(parts) > 1:
        return f"services.{parts[1]}"
    if parts[0] in ("memory", "runtime"):
        return parts[0]
    return "root"


def _first_party_imports(path: Path) -> set[str]:
    """Return the set of first-party units this file imports."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                if root in FIRST_PARTY_ROOTS:
                    imports.add(_normalize(alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue  # relative import — always within-unit, not a boundary crossing
            if node.module is None:
                continue
            root = node.module.split(".")[0]
            if root not in FIRST_PARTY_ROOTS:
                continue
            if node.module == "services":
                # `from services import brain, calendar` — each name is a submodule.
                for alias in node.names:
                    imports.add(f"services.{alias.name}")
            else:
                imports.add(_normalize(node.module))

    return imports


def _normalize(dotted: str) -> str:
    """`services.brain.context_engine` -> `services.brain`; `memory.tasks` -> `memory`."""
    parts = dotted.split(".")
    if parts[0] == "services" and len(parts) > 1:
        return f"services.{parts[1]}"
    return parts[0]


def _all_source_files() -> list[Path]:
    files = []
    for path in BACKEND_ROOT.rglob("*.py"):
        rel = path.relative_to(BACKEND_ROOT)
        if any(part in (".venv", "__pycache__", "data", "models") for part in rel.parts):
            continue
        files.append(path)
    return files


def test_no_undocumented_cross_package_imports():
    """Every first-party import crossing a package boundary must be a
    documented edge in ALLOWED_EDGES (or a ROOT_UTILS import, always allowed).
    """
    violations = []

    for path in _all_source_files():
        unit = _unit_for(path)
        if unit in EXEMPT_UNITS:
            continue

        allowed = ALLOWED_EDGES.get(unit)
        if allowed is None:
            continue  # unit not yet modeled (e.g. a future package) — nothing to assert

        for imported in _first_party_imports(path):
            if imported == unit:
                continue  # importing your own package's public API
            if imported in ROOT_UTILS:
                continue
            if imported not in allowed:
                rel = path.relative_to(BACKEND_ROOT)
                violations.append(f"{rel}: {unit} -> {imported} (not an allowed edge)")

    assert not violations, "Undocumented cross-package imports:\n" + "\n".join(sorted(violations))


def test_nothing_imports_services_api():
    """`services.api` is the top of the graph (the FastAPI facade). Nothing
    else may import it — a service or runtime importing api would be a
    circular/downward dependency.
    """
    violations = []
    for path in _all_source_files():
        unit = _unit_for(path)
        if unit in EXEMPT_UNITS or unit == "services.api":
            continue
        if "services.api" in _first_party_imports(path):
            violations.append(str(path.relative_to(BACKEND_ROOT)))

    assert not violations, "Package(s) importing services.api:\n" + "\n".join(violations)


def test_leaf_services_have_no_dependencies():
    """voice, calendar, and automation are documented leaves (ARCHITECTURE_v1
    §5): hardware/OS edges with no knowledge of memory, runtime, or other
    services.
    """
    for unit in ("services.voice", "services.calendar", "services.automation"):
        assert ALLOWED_EDGES[unit] == set(), f"{unit} is documented as a leaf"
