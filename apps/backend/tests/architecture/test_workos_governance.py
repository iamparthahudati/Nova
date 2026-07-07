"""WorkOS governance — schema and mutation vocabulary (Phase 0)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

from domains.work.value_objects import WORK_ENTITY_TYPES
from memory.work.migrations import FORBIDDEN_DERIVED_COLUMNS, assert_migration_source_governance
from runtime.mutation_event import MutationEvent

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def test_mutation_event_shape_is_frozen():
    """MutationEvent fields are additive-only — WorkOS extends entity_type, not shape."""
    fields = {field.name for field in dataclasses.fields(MutationEvent)}
    assert fields == {"event_type", "entity_type", "operation", "entity", "metadata"}


def test_work_entity_types_are_registered():
    """Every planned WorkOS entity_type is enumerated before WOS-1 builders ship."""
    assert "project" in WORK_ENTITY_TYPES
    assert "work_item" in WORK_ENTITY_TYPES
    assert "time_entry" in WORK_ENTITY_TYPES
    assert "priority_policy" in WORK_ENTITY_TYPES
    assert len(WORK_ENTITY_TYPES) >= 29


def test_work_migrations_forbid_derived_columns():
    source = (BACKEND_ROOT / "memory" / "work" / "migrations.py").read_text(encoding="utf-8")
    assert_migration_source_governance(source)


def test_forbidden_derived_columns_inventory():
    """ADR 0022/0023 forbidden names are centralized for migration linting."""
    assert "priority_score" in FORBIDDEN_DERIVED_COLUMNS
    assert "health_status" in FORBIDDEN_DERIVED_COLUMNS
    assert "completion_pct" in FORBIDDEN_DERIVED_COLUMNS
