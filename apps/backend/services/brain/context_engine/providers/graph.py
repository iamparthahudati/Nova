"""Knowledge-graph provider — the first hot-path *reader* of the graph that
2.6 built and 2.7 populates (Milestone 2.8's motivating gap).

Entity matching is deliberately dumb and deterministic: sliding 1–3-word
n-grams of the query looked up via memory.find_entity(), which is exact
(case/whitespace-insensitive) — precision over recall, because a wrong graph
fact in the prompt is worse than a missing one. Fuzzy matching is semantic
recall's job, not this provider's. Longer n-grams run first so "Aurora
Rebrand" wins over "Aurora".

Each matched entity contributes its heaviest edges as one-line facts:

    Priya Sharma (person) —WORKS_ON→ Aurora Rebrand (project)

Read-only through Memory's public graph verbs (find_entity, entity_edges,
get_entity) — Rule: the Knowledge Graph stays read-only from Brain; edge and
entity writes happen only in the extraction sweep, through Memory.
"""

import re
from typing import Optional

from memory import entity_edges, find_entity, get_entity

from ...config import (
    GRAPH_CONTEXT_ENABLED,
    GRAPH_CONTEXT_MAX_EDGES,
    GRAPH_CONTEXT_MAX_ENTITIES,
    GRAPH_CONTEXT_TOKEN_BUDGET,
)
from ..base import ContextItem, ContextProvider, ContextRequest

_WORD_RE = re.compile(r"[A-Za-z0-9']+")


def _candidate_phrases(query: str) -> list[str]:
    """1–3-word n-grams, longest first; 1-grams under 3 chars are noise."""
    words = _WORD_RE.findall(query)
    phrases = []
    for n in (3, 2, 1):
        for i in range(len(words) - n + 1):
            phrase = " ".join(words[i : i + n])
            if n == 1 and len(phrase) < 3:
                continue
            phrases.append(phrase)
    return phrases


class GraphContextProvider(ContextProvider):
    name = "knowledge_graph"
    title = "Known Connections (from the knowledge graph)"
    budget = GRAPH_CONTEXT_TOKEN_BUDGET
    omit_when_empty = True  # no matched entities → no section, not "None"

    def collect(self, request: ContextRequest) -> list[ContextItem]:
        if not GRAPH_CONTEXT_ENABLED or not request.query:
            return []

        entities: list[dict] = []
        matched_ids: set[str] = set()
        for phrase in _candidate_phrases(request.query):
            if len(entities) >= GRAPH_CONTEXT_MAX_ENTITIES:
                break
            entity = find_entity(phrase)
            if entity is not None and entity["id"] not in matched_ids:
                matched_ids.add(entity["id"])
                entities.append(entity)

        items: list[ContextItem] = []
        seen_edges: set[str] = set()  # both endpoints matched → edge once
        entity_cache: dict[str, Optional[dict]] = {e["id"]: e for e in entities}

        def resolve(entity_id: str):
            if entity_id not in entity_cache:
                entity_cache[entity_id] = get_entity(entity_id)
            return entity_cache[entity_id]

        for entity in entities:
            for edge in entity_edges(entity["id"])[:GRAPH_CONTEXT_MAX_EDGES]:
                if edge["id"] in seen_edges:
                    continue
                seen_edges.add(edge["id"])
                source = resolve(edge["from_entity_id"])
                target = resolve(edge["to_entity_id"])
                if source is None or target is None:
                    continue
                fact = (
                    f"{source['canonical_name']} ({source['type']}) "
                    f"—{edge['relation_type']}→ "
                    f"{target['canonical_name']} ({target['type']})"
                )
                items.append(
                    ContextItem(
                        text=fact,
                        score=float(edge.get("weight", 1.0)),  # repetition = evidence
                    )
                )
        return items
