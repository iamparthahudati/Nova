#!/usr/bin/env python3
"""Enforce the Handbook §3.1 hard size limits — file and function length.

Scope (intentionally): the two limits that are cheap, unambiguous, and catch
the bulk of real "this file/function is doing too much" drift — max file
length (500 lines) and max function length (75 lines). Nesting depth, param
count, and cyclomatic complexity are already covered by flake8 (mccabe via
`max-complexity` in .flake8); adding a bespoke checker for those too is a
follow-up, not a blocker for standing up this gate.

Usage:
    python scripts/dev/check_limits.py [root ...]

Exits non-zero if any file/function exceeds its hard limit and isn't listed
in KNOWN_DEBT below. New debt requires a `# DEBT(id)` justification per
Handbook §8.3 — add it inline in code, not just in this allowlist.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

MAX_FILE_LINES = 500
MAX_FUNCTION_LINES = 75

EXCLUDED_DIRS = {".venv", "data", "models", "__pycache__", "node_modules", ".git"}

# DEBT(nova-ci-3): pre-existing violations at the time the limit gate was
# introduced. Do not add to this list without a `# DEBT(id)` comment at the
# violation site and a tracking note in the PR description.
KNOWN_DEBT_FILES = {
    "apps/backend/dashboard.py",  # 765 lines — dev-only diagnostics CLI, not a package module.
}

# DEBT(nova-ci-3): pre-existing function-length violations, same rule as above.
KNOWN_DEBT_FUNCTIONS = {
    "apps/backend/memory/schema.py:init_db",
    "apps/backend/memory_producers.py:memory_from_mutation",
    "apps/backend/runtime/conversation.py:process_message",
    "apps/backend/runtime/mutation_chat.py:_entity_for_tool",
    "apps/backend/services/api/projections/home.py:build_home_response",
    "apps/backend/services/brain/reflection.py:run_reflection_job",
}


def _iter_python_files(roots: list[Path]) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        for path in root.rglob("*.py"):
            if any(part in EXCLUDED_DIRS for part in path.parts):
                continue
            files.append(path)
    return files


def _check_file_length(path: Path, repo_root: Path) -> list[str]:
    rel = path.relative_to(repo_root).as_posix()
    if rel in KNOWN_DEBT_FILES:
        return []
    line_count = sum(1 for _ in path.open(encoding="utf-8"))
    if line_count > MAX_FILE_LINES:
        return [f"{rel}: {line_count} lines (hard limit {MAX_FILE_LINES})"]
    return []


def _check_function_lengths(path: Path, repo_root: Path) -> list[str]:
    rel = path.relative_to(repo_root).as_posix()
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError as exc:
        return [f"{rel}: could not parse ({exc})"]

    violations = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end_line = getattr(node, "end_lineno", None)
        if end_line is None:
            continue
        length = end_line - node.lineno + 1
        if length > MAX_FUNCTION_LINES and f"{rel}:{node.name}" not in KNOWN_DEBT_FUNCTIONS:
            violations.append(
                f"{rel}:{node.lineno}: {node.name}() is {length} lines "
                f"(hard limit {MAX_FUNCTION_LINES})"
            )
    return violations


def main(argv: list[str]) -> int:
    repo_root = Path(__file__).resolve().parents[2]
    roots = [Path(a).resolve() for a in argv] or [repo_root / "apps" / "backend"]

    violations: list[str] = []
    for path in _iter_python_files(roots):
        violations.extend(_check_file_length(path, repo_root))
        violations.extend(_check_function_lengths(path, repo_root))

    if violations:
        print("Size-limit violations (Handbook §3.1):")
        for v in sorted(violations):
            print(f"  - {v}")
        print(f"\n{len(violations)} violation(s).")
        return 1

    print("check_limits: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
