"""Knowledge graph — internal to memory/. See service.py for the public surface.

Same discipline as memory/semantic/: nothing outside memory/ imports this
package directly; memory/__init__.py re-exports the functions below at the top
level, same as every other table's functions. The split inside this package:

  service.py   canonicalization, dedup-vs-reinforce policy, referential checks;
               the public verbs
  store.py     SQLite CRUD for the `entities` and `edges` tables (incl. the
               recursive-CTE traversal — a read query, not policy)

The graph is an extension of Memory, not a second database: both tables live in
nova.db next to `memories`, and edges cite their originating memory via
source_memory_id. This package holds storage and queries ONLY — deciding what
counts as an entity or a relation is extraction (a Brain job, next milestone),
and never happens here.
"""

from .service import (
    create_entity,
    get_entity,
    find_entity,
    delete_entity,
    link_entities,
    entity_edges,
    delete_edge,
    related_entities,
    list_graph_snapshot,
    graph_stats,
)

__all__ = [
    "create_entity",
    "get_entity",
    "find_entity",
    "delete_entity",
    "link_entities",
    "entity_edges",
    "delete_edge",
    "related_entities",
    "list_graph_snapshot",
    "graph_stats",
]
