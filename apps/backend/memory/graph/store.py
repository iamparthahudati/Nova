"""SQLite CRUD for the `entities` and `edges` tables — the knowledge graph rows.

Same shape as semantic/ledger.py: thin functions over two tables, no
interpretation of the data. Name/relation canonicalization, the
duplicate-vs-reinforce policy, and referential checks live in service.py; this
file only reads and writes rows. The one non-trivial read here is
related_within(), the depth-limited recursive-CTE traversal — it lives in this
file because it is still just a query over the two tables, with no opinion
about what the result means.

Column semantics:
  entities.type            lowercase noun category ('person', 'project', …)
  entities.canonical_name  whitespace-normalized display name; unique per type
                           case-insensitively (enforced by idx_entities_identity)
  entities.attributes      free-form JSON dict
  edges.relation_type      UPPER_SNAKE verb ('WORKS_ON'); one row per
                           (from, to, relation) triple (idx_edges_identity)
  edges.weight             accumulated evidence — re-linking the same triple
                           adds to it instead of inserting a duplicate row
  edges.source_memory_id   provenance: the memories.id that justified this edge
"""

import json
from typing import Optional

from .. import _connection


def _entity_dict(row) -> dict:
    entity = dict(row)
    entity["attributes"] = json.loads(entity["attributes"] or "{}")
    return entity


# ── Entities ─────────────────────────────────────────────────────────────────


def insert_entity(entity_id: str, entity_type: str, canonical_name: str, attributes: dict) -> str:
    created_at = _connection.now()
    with _connection.connect() as con:
        con.execute(
            """INSERT INTO entities (id, type, canonical_name, attributes, created_at)
               VALUES (?, ?, ?, ?, ?)""",
            (entity_id, entity_type, canonical_name, json.dumps(attributes), created_at),
        )
    return created_at


def get_entity(entity_id: str) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM entities WHERE id = ?", (entity_id,)).fetchone()
    return _entity_dict(row) if row else None


def find_by_name(canonical_name: str, entity_type: Optional[str] = None) -> Optional[dict]:
    """Case-insensitive lookup by canonical name, optionally scoped to a type.

    Oldest match first: without a type filter the same name may legitimately
    exist under several types ('Mercury' the project vs. 'Mercury' the person),
    and the deterministic answer is the one that has been known longest.
    """
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """SELECT * FROM entities
               WHERE canonical_name = ? COLLATE NOCASE
                 AND (? IS NULL OR type = ?)
               ORDER BY created_at LIMIT 1""",
            (canonical_name, entity_type, entity_type),
        ).fetchone()
    return _entity_dict(row) if row else None


def update_attributes(entity_id: str, attributes: dict) -> None:
    with _connection.connect() as con:
        con.execute(
            "UPDATE entities SET attributes = ? WHERE id = ?",
            (json.dumps(attributes), entity_id),
        )


def delete_entity(entity_id: str) -> None:
    """Remove the entity row only — service.py cascades its edges first."""
    with _connection.connect() as con:
        con.execute("DELETE FROM entities WHERE id = ?", (entity_id,))


def list_entities(limit: Optional[int] = None, offset: int = 0) -> list[dict]:
    """All entity rows, oldest first."""
    if limit is None:
        query = "SELECT * FROM entities ORDER BY created_at OFFSET ?"
        params: tuple = (offset,)
    else:
        query = "SELECT * FROM entities ORDER BY created_at LIMIT ? OFFSET ?"
        params = (limit, offset)
    with _connection.connect(rows=True) as con:
        rows = con.execute(query, params).fetchall()
    return [_entity_dict(r) for r in rows]


def count_entities() -> int:
    with _connection.connect() as con:
        return con.execute("SELECT COUNT(*) FROM entities").fetchone()[0]


def count_entities_by_type() -> dict[str, int]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT type, COUNT(*) AS n FROM entities GROUP BY type ORDER BY type"
        ).fetchall()
    return {r["type"]: r["n"] for r in rows}


def list_edges(limit: Optional[int] = None, offset: int = 0) -> list[dict]:
    """All edge rows, heaviest first."""
    if limit is None:
        query = "SELECT * FROM edges ORDER BY weight DESC, created_at OFFSET ?"
        params: tuple = (offset,)
    else:
        query = "SELECT * FROM edges ORDER BY weight DESC, created_at LIMIT ? OFFSET ?"
        params = (limit, offset)
    with _connection.connect(rows=True) as con:
        rows = con.execute(query, params).fetchall()
    return [dict(r) for r in rows]


def count_edges() -> int:
    with _connection.connect() as con:
        return con.execute("SELECT COUNT(*) FROM edges").fetchone()[0]


def count_edges_by_relation() -> dict[str, int]:
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            "SELECT relation_type, COUNT(*) AS n FROM edges "
            "GROUP BY relation_type ORDER BY relation_type"
        ).fetchall()
    return {r["relation_type"]: r["n"] for r in rows}


# ── Edges ────────────────────────────────────────────────────────────────────


def insert_edge(
    edge_id: str,
    from_entity_id: str,
    to_entity_id: str,
    relation_type: str,
    weight: float,
    source_memory_id: Optional[str],
) -> str:
    created_at = _connection.now()
    with _connection.connect() as con:
        con.execute(
            """INSERT INTO edges
               (id, from_entity_id, to_entity_id, relation_type, weight,
                source_memory_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                edge_id,
                from_entity_id,
                to_entity_id,
                relation_type,
                weight,
                source_memory_id,
                created_at,
            ),
        )
    return created_at


def get_edge(edge_id: str) -> Optional[dict]:
    with _connection.connect(rows=True) as con:
        row = con.execute("SELECT * FROM edges WHERE id = ?", (edge_id,)).fetchone()
    return dict(row) if row else None


def find_edge(from_entity_id: str, to_entity_id: str, relation_type: str) -> Optional[dict]:
    """The one row for this (from, to, relation) triple, if it exists."""
    with _connection.connect(rows=True) as con:
        row = con.execute(
            """SELECT * FROM edges
               WHERE from_entity_id = ? AND to_entity_id = ? AND relation_type = ?""",
            (from_entity_id, to_entity_id, relation_type),
        ).fetchone()
    return dict(row) if row else None


def reinforce_edge(edge_id: str, weight_delta: float, source_memory_id: Optional[str]) -> None:
    """Add evidence to an existing edge; backfill provenance if it had none."""
    with _connection.connect() as con:
        con.execute(
            """UPDATE edges
               SET weight = weight + ?,
                   source_memory_id = COALESCE(source_memory_id, ?)
               WHERE id = ?""",
            (weight_delta, source_memory_id, edge_id),
        )


def edges_for_entity(
    entity_id: str, relation_type: Optional[str] = None, direction: str = "any"
) -> list[dict]:
    """Edges touching an entity: 'out' (from it), 'in' (to it), or 'any'."""
    clauses = {
        "out": "e.from_entity_id = :id",
        "in": "e.to_entity_id = :id",
        "any": ":id IN (e.from_entity_id, e.to_entity_id)",
    }
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            f"""SELECT e.* FROM edges AS e
                WHERE {clauses[direction]}
                  AND (:rel IS NULL OR e.relation_type = :rel)
                ORDER BY e.weight DESC, e.created_at""",
            {"id": entity_id, "rel": relation_type},
        ).fetchall()
    return [dict(r) for r in rows]


def delete_edge(edge_id: str) -> None:
    with _connection.connect() as con:
        con.execute("DELETE FROM edges WHERE id = ?", (edge_id,))


def delete_edges_for_entity(entity_id: str) -> int:
    """Remove every edge touching an entity (the delete_entity cascade)."""
    with _connection.connect() as con:
        cur = con.execute(
            "DELETE FROM edges WHERE ? IN (from_entity_id, to_entity_id)",
            (entity_id,),
        )
        return cur.rowcount


# ── Traversal ────────────────────────────────────────────────────────────────


def related_within(entity_id: str, depth: int, relation_type: Optional[str] = None) -> list[dict]:
    """Entities reachable within `depth` undirected hops, with their min depth.

    This is the recursive-CTE traversal ARCHITECTURE_v2 §4 chose SQLite for.
    Edges are walked undirected ('who works on this project' starts from the
    project, against the WORKS_ON arrows). Termination is guaranteed by the
    depth bound: UNION dedups (entity_id, depth) pairs and depth only grows, so
    a cycle cannot recurse forever. GROUP BY then keeps each entity once, at
    its shortest distance. The relation filter constrains which edges may be
    *walked*, so at depth > 1 it means 'reachable via that relation alone'.
    """
    with _connection.connect(rows=True) as con:
        rows = con.execute(
            """WITH RECURSIVE walk(entity_id, depth) AS (
                   SELECT :id, 0
                   UNION
                   SELECT CASE WHEN e.from_entity_id = w.entity_id
                               THEN e.to_entity_id ELSE e.from_entity_id END,
                          w.depth + 1
                   FROM edges AS e
                   JOIN walk AS w ON w.entity_id IN (e.from_entity_id, e.to_entity_id)
                   WHERE w.depth < :depth
                     AND (:rel IS NULL OR e.relation_type = :rel)
               )
               SELECT ent.*, MIN(w.depth) AS depth
               FROM walk AS w
               JOIN entities AS ent ON ent.id = w.entity_id
               WHERE w.entity_id <> :id
               GROUP BY ent.id
               ORDER BY depth, ent.canonical_name COLLATE NOCASE""",
            {"id": entity_id, "depth": depth, "rel": relation_type},
        ).fetchall()

    return [_entity_dict(row) for row in rows]
