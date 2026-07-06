"""Public knowledge-graph API — the surface memory/__init__.py re-exports.

Callers never see store.py or SQLite. They see eight verbs:

  write:     create_entity(), link_entities()
  read:      get_entity(), find_entity(), entity_edges(), related_entities()
  delete:    delete_entity(), delete_edge()

Storage and queries only — no extraction, no Claude, no imports outside this
package and the stdlib. Whether a phrase in a conversation *is* an entity or a
relation is a judgment this package is forbidden to make (that's the next
milestone, and the judgment runs through Brain); by the time anything reaches
these functions it is already a typed name or a typed link.

Duplicate policy mirrors semantic memory's remember():

  * create_entity() for an existing (type, name) — case- and
    whitespace-insensitively — returns the existing id instead of inserting a
    second row, shallow-merging any newly supplied attribute keys over the old.
  * link_entities() for an existing (from, to, relation) triple adds the new
    weight onto the existing edge instead of inserting a duplicate — repetition
    is evidence, and weight is where it accumulates.

sqlite3 does not enforce foreign keys unless asked per-connection, and
memory/_connection deliberately stays minimal, so referential integrity is
enforced here instead: link_entities() rejects unknown entity ids, and
delete_entity() cascades to every edge touching the entity so no dangling edge
can survive. The UNIQUE indexes in schema.py back the dedup rules at the
storage layer as a final integrity backstop.
"""

import re
import uuid
from typing import Optional

from . import store

# Traversal ceiling: ARCHITECTURE_v2 §4 scopes graph queries to depth 1–2
# ("who else is on this project"). 3 leaves headroom for one indirection
# without letting a caller ask for an unbounded walk of the whole graph.
MAX_DEPTH = 3

_WS = re.compile(r"\s+")


def _canonical_name(name: str) -> str:
    """Whitespace-normalized display name ('  Priya   Sharma ' → 'Priya Sharma').

    Case is preserved for display; case-insensitive identity is handled by the
    NOCASE lookups/index, so 'priya sharma' still finds 'Priya Sharma'.
    """
    return _WS.sub(" ", name.strip())


def _canonical_type(entity_type: str) -> str:
    """Lowercase snake category ('Person' → 'person', 'code repo' → 'code_repo')."""
    return _WS.sub("_", entity_type.strip().lower())


def _canonical_relation(relation_type: str) -> str:
    """UPPER_SNAKE verb ('works on' → 'WORKS_ON'), so the same relation spelled
    differently by different producers still lands on the same edge row."""
    return _WS.sub("_", relation_type.strip().upper())


# ── Entities ─────────────────────────────────────────────────────────────────


def create_entity(entity_type: str, name: str,
                  attributes: Optional[dict] = None) -> str:
    """Create an entity, or fold into the existing one. Returns its id.

    Duplicate detection is by (type, canonical name), case-insensitive: creating
    ('person', 'priya sharma') when ('person', 'Priya Sharma') exists returns
    the existing id. Newly supplied attribute keys are shallow-merged over the
    stored ones (new values win), so repeated sightings can enrich an entity
    without ever forking it.
    """
    entity_type = _canonical_type(entity_type)
    name = _canonical_name(name)
    if not entity_type or not name:
        raise ValueError("create_entity() requires a non-empty type and name")

    existing = store.find_by_name(name, entity_type)
    if existing is not None:
        if attributes:
            merged = {**existing["attributes"], **attributes}
            if merged != existing["attributes"]:
                store.update_attributes(existing["id"], merged)
        return existing["id"]

    entity_id = str(uuid.uuid4())
    store.insert_entity(entity_id, entity_type, name, attributes or {})
    return entity_id


def get_entity(entity_id: str) -> Optional[dict]:
    """The entity row (attributes parsed to a dict), or None."""
    return store.get_entity(entity_id)


def find_entity(name: str, entity_type: Optional[str] = None) -> Optional[dict]:
    """Look an entity up by name (case/whitespace-insensitive), optionally by type.

    Without a type, the same name may exist under several types; the oldest
    match wins deterministically. Returns None rather than fuzzy-matching —
    'close enough' is a similarity judgment that belongs to semantic recall,
    not to a canonical-identity store.
    """
    name = _canonical_name(name)
    if not name:
        return None
    return store.find_by_name(
        name, _canonical_type(entity_type) if entity_type else None
    )


def delete_entity(entity_id: str) -> bool:
    """Remove an entity and every edge touching it. True if it existed.

    Hard delete, unlike semantic memory's tombstones: the milestone schema has
    no lifecycle columns, and an entity (a canonical noun) is not a ranked,
    decaying observation — the *memories* that mentioned it keep their own
    soft-delete history independently. The edge cascade runs first so a
    dangling edge can never outlive its endpoint.
    """
    if store.get_entity(entity_id) is None:
        return False
    store.delete_edges_for_entity(entity_id)
    store.delete_entity(entity_id)
    return True


# ── Edges ────────────────────────────────────────────────────────────────────


def link_entities(from_entity_id: str, to_entity_id: str, relation_type: str,
                  weight: float = 1.0,
                  source_memory_id: Optional[str] = None) -> str:
    """Create (or reinforce) a directed edge. Returns the edge id.

    One row exists per (from, to, relation) triple: linking an existing triple
    adds `weight` onto the stored edge instead of duplicating it, and backfills
    source_memory_id if the edge had no provenance yet (the earliest cited
    memory is otherwise kept). Direction is meaningful (person WORKS_ON
    project), but traversal in related_entities() ignores it, so choosing the
    natural reading order costs nothing at query time.
    """
    relation_type = _canonical_relation(relation_type)
    if not relation_type:
        raise ValueError("link_entities() requires a non-empty relation_type")
    if weight <= 0:
        raise ValueError("link_entities() requires a positive weight")
    if from_entity_id == to_entity_id:
        raise ValueError("link_entities() cannot link an entity to itself")
    for entity_id in (from_entity_id, to_entity_id):
        if store.get_entity(entity_id) is None:
            raise ValueError(f"link_entities(): unknown entity id {entity_id!r}")

    existing = store.find_edge(from_entity_id, to_entity_id, relation_type)
    if existing is not None:
        store.reinforce_edge(existing["id"], weight, source_memory_id)
        return existing["id"]

    edge_id = str(uuid.uuid4())
    store.insert_edge(edge_id, from_entity_id, to_entity_id, relation_type,
                      weight, source_memory_id)
    return edge_id


def entity_edges(entity_id: str, relation_type: Optional[str] = None,
                 direction: str = "any") -> list[dict]:
    """Edge rows touching an entity, heaviest first.

    `direction` is 'out' (edges from it), 'in' (edges to it), or 'any'. This is
    the discovery surface delete_edge() needs — related_entities() answers
    "what is nearby", this answers "via exactly which links".
    """
    if direction not in ("out", "in", "any"):
        raise ValueError("direction must be 'out', 'in', or 'any'")
    return store.edges_for_entity(
        entity_id, _canonical_relation(relation_type) if relation_type else None,
        direction,
    )


def delete_edge(edge_id: str) -> bool:
    """Remove one edge. True if it existed. Entities are never affected."""
    if store.get_edge(edge_id) is None:
        return False
    store.delete_edge(edge_id)
    return True


# ── Traversal ────────────────────────────────────────────────────────────────


def related_entities(entity_id: str, relation_type: Optional[str] = None,
                     depth: int = 1) -> list[dict]:
    """Entities within `depth` undirected hops, nearest first.

    Each result is an entity dict plus its `depth` (shortest hop count, 1-based).
    With a relation_type, only edges of that relation are walked — at depth 1
    that means direct neighbours via that relation; deeper, reachability through
    that relation alone. depth is clamped to [1, MAX_DEPTH]; an unknown
    entity_id yields [] (a read of nothing, not an error, matching get/find).
    """
    depth = max(1, min(int(depth), MAX_DEPTH))
    return store.related_within(
        entity_id, depth,
        _canonical_relation(relation_type) if relation_type else None,
    )


def list_graph_snapshot(
    entity_limit: Optional[int] = 500,
    edge_limit: Optional[int] = 500,
) -> dict:
    """Full graph snapshot for desktop browse — entities and edges."""
    return {
        "entities": store.list_entities(limit=entity_limit),
        "edges": store.list_edges(limit=edge_limit),
    }


def graph_stats() -> dict:
    """Lightweight graph metrics for dashboard diagnostics."""
    return {
        "entity_count": store.count_entities(),
        "edge_count": store.count_edges(),
        "entities_by_type": store.count_entities_by_type(),
        "edges_by_relation": store.count_edges_by_relation(),
    }
