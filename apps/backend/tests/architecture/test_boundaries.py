"""Non-import boundaries — Handbook §4.1 checklist items that a plain import
graph can't catch: "Brain is the only Claude client" and "Memory owns
persistence" (ADR 0003, ADR 0004).

These scan source *text* rather than the import graph because the relevant
signal is a literal (the Anthropic endpoint, the `x-api-key` header, a
`sqlite3.connect(`/`lancedb.connect(` call) rather than a module import —
e.g. `services/api/diagnostics.py` legitimately does `import sqlite3` to
catch `sqlite3.Error` as an exception type without ever opening a connection.
"""

from __future__ import annotations

from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[2]

EXCLUDED_DIR_PARTS = {".venv", "__pycache__", "data", "models"}


def _source_files(exclude_dirs: set[str] = frozenset()) -> list[Path]:
    files = []
    for path in BACKEND_ROOT.rglob("*.py"):
        rel = path.relative_to(BACKEND_ROOT)
        if any(part in EXCLUDED_DIR_PARTS or part in exclude_dirs for part in rel.parts):
            continue
        files.append(path)
    return files


def test_only_brain_calls_the_claude_api():
    """Per ADR 0003: only `services/brain` may call the Anthropic API. Brain
    calls it via raw `urllib.request` (no `anthropic` SDK in use today), so
    the signal is the literal endpoint / auth header, not an import.
    """
    markers = ("ANTHROPIC_API_URL", "anthropic.com", "x-api-key")
    violations = []

    for path in _source_files(exclude_dirs={"tests"}):
        rel = path.relative_to(BACKEND_ROOT)
        if rel.parts[:2] == ("services", "brain"):
            continue
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in markers):
            violations.append(str(rel))

    assert not violations, "Claude API markers found outside services/brain:\n" + "\n".join(
        violations
    )


def test_only_memory_opens_database_connections():
    """Per ADR 0004: `memory` is the only storage owner. Other packages may
    reference `sqlite3`/`lancedb` exception types (e.g. a health check) but
    must never call `.connect(`.
    """
    connect_calls = ("sqlite3.connect(", "lancedb.connect(")
    violations = []

    for path in _source_files(exclude_dirs={"tests"}):
        rel = path.relative_to(BACKEND_ROOT)
        if rel.parts[0] == "memory":
            continue
        text = path.read_text(encoding="utf-8")
        if any(call in text for call in connect_calls):
            violations.append(str(rel))

    assert not violations, "Database connections opened outside memory/:\n" + "\n".join(violations)


def test_only_memory_semantic_imports_lancedb():
    """LanceDB is a derived index rebuildable from the SQLite ledger (ADR
    0013) — its wrapper is intentionally confined to one file.
    """
    violations = []
    for path in _source_files(exclude_dirs={"tests"}):
        rel = path.relative_to(BACKEND_ROOT)
        if rel.parts[:2] == ("memory", "semantic"):
            continue
        text = path.read_text(encoding="utf-8")
        if "import lancedb" in text:
            violations.append(str(rel))

    assert not violations, "`import lancedb` found outside memory/semantic/:\n" + "\n".join(
        violations
    )
