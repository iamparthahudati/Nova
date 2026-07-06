"""Semantic memory — internal to memory/. See service.py for the public surface.

Nothing outside memory/ imports this package directly; memory/__init__.py
re-exports the functions below at the top level, same as every other table's
functions. The split inside this package:

  service.py          coordinates the two stores (SQLite + LanceDB); public verbs
  ledger.py           SQLite CRUD for the `memories` table (source of truth)
  vector_store.py     LanceDB wrapper (derived index, rebuildable)
  embedding_provider  local embedding model behind a swappable interface
  ranking.py          all scoring math + tier policy (pure, no I/O)
  lifecycle.py        tier state machine over ledger rows (no scoring, no vectors)
"""

from .service import (
    remember,
    supersede_memory,
    recall,
    list_memories,
    count_active_memories,
    count_active_memories_by_tier,
    rebuild_index,
    maintenance,
    recalculate_scores,
    evaluate_memory,
    promote_memory,
    demote_memory,
    archive_memory,
    forget_memory,
    restore_memory,
    touch_memory,
    record_access,
    memories_pending_entity_extraction,
    record_entity_extraction_attempt,
    mark_entities_extracted,
)

__all__ = [
    "remember",
    "supersede_memory",
    "recall",
    "list_memories",
    "count_active_memories",
    "count_active_memories_by_tier",
    "rebuild_index",
    "maintenance",
    "recalculate_scores",
    "evaluate_memory",
    "promote_memory",
    "demote_memory",
    "archive_memory",
    "forget_memory",
    "restore_memory",
    "touch_memory",
    "record_access",
    "memories_pending_entity_extraction",
    "record_entity_extraction_attempt",
    "mark_entities_extracted",
]
