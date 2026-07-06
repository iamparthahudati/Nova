"""Entity-extraction output contract — code-canonical (Milestone 2.7).

This module IS the contract AI_CONTRACTS.md §2.4 points at. Schema, validator,
and parser live here and nowhere else: the prompt in extraction.py promises
Claude will produce this shape, parse_extraction() is the only code that reads
it, and nothing downstream ever touches the raw JSON. This is the pattern the
reflection contract (§2.3) was flagged as lacking — declared in a prompt
sentence, parsed 20 lines away, validated nowhere.

The envelope Claude must return (one object per batched memory):

    {"memories": [
        {"key": "m1",
         "entities": [
             {"type": "person", "name": "Priya Sharma",
              "attributes": {"role": "designer"}}          # attributes optional
         ],
         "relationships": [
             {"from_type": "person", "from_name": "Priya Sharma",
              "to_type": "project",  "to_name": "Aurora rebrand",
              "relation": "WORKS_ON"}
         ]}
    ]}

Design decisions the validator enforces:

  * Keys, not memory UUIDs. The prompt labels each memory m1..mN and Claude
    echoes the label; extraction.py maps labels back to real ids. Short keys
    cost fewer tokens and cannot leak or hallucinate a plausible-looking UUID
    into provenance.
  * Strict envelope, lenient items. A response that isn't the envelope at all
    raises ExtractionParseError (the whole batch is retried later — attempts
    were already counted). But one malformed entity or relationship inside an
    otherwise-valid response is dropped with its memory still processed:
    losing one noun is cheaper than burning a retry on 9 good memories.
  * Closed entity-type set. ARCHITECTURE_v2 §4's nine types plus
    organization/place/topic (personal memories constantly reference
    employers, cities, and subjects; without these Claude shoehorns them into
    'project' and pollutes the graph). Unknown types are dropped, never
    stored: a free-typed graph degenerates into untyped string soup.
  * Relationships may only join entities declared in the same memory's entity
    list. This guarantees every edge endpoint has an id by the time
    link_entities() runs, and keeps one memory's extraction self-contained
    (re-declaring an already-known entity is free — create_entity() dedups).
  * The user and the assistant are never entities. Memories are written from
    the owner's perspective; an "I/me/user" node would end up linked to
    everything and mean nothing.
  * Dedup inside one response. The same (type, name) twice folds into one
    entity; the same (from, to, relation) twice folds into one relationship —
    otherwise a single verbose response would double-reinforce edge weights.

Canonicalization here (type → lower_snake, name → whitespace-collapsed,
relation → UPPER_SNAKE) deliberately mirrors memory/graph/service.py: the
graph re-canonicalizes on write as its own invariant, but the contract must
canonicalize too or its dedup/endpoint checks would miss case variants.

Pure module: stdlib + identity only. No Claude call, no persistence, no I/O —
that is what makes the contract unit-testable in isolation.
"""

import json
import re
from dataclasses import dataclass, field

from identity import ASSISTANT_NAME

# ── Schema constants ──────────────────────────────────────────────────────────

# ARCHITECTURE_v2 §4's nine canonical noun types + three additive ones (see
# module docstring). Extending this set is a contract change: update the
# prompt's type list in extraction.py in the same commit.
ENTITY_TYPES = frozenset(
    {
        "person",
        "project",
        "task",
        "goal",
        "habit",
        "meeting",
        "document",
        "conversation",
        "product",
        "organization",
        "place",
        "topic",
    }
)

# Names that can never be an entity: the owner, the assistant, and bare
# pronouns/generics that survive careless extraction. Compared case-folded
# against the canonicalized name.
FORBIDDEN_NAMES = frozenset(
    {
        "user",
        "the user",
        "owner",
        "me",
        "myself",
        "i",
        "you",
        "assistant",
        "the assistant",
        ASSISTANT_NAME.lower(),
        "rai",
    }
)

# Ceilings, not targets — a memory is one or two sentences; hitting these
# means Claude is inventing. Overflow is truncated, not fatal.
MAX_ENTITIES_PER_MEMORY = 10
MAX_RELATIONSHIPS_PER_MEMORY = 15
MAX_NAME_CHARS = 120
MAX_RELATION_CHARS = 64
MAX_ATTRIBUTES = 8
MAX_ATTRIBUTE_CHARS = 200

_RELATION_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")
_WS = re.compile(r"\s+")


class ExtractionParseError(ValueError):
    """The response is not the contract envelope at all (unparseable JSON, or
    JSON of the wrong shape). Item-level defects never raise this."""


@dataclass(frozen=True)
class ExtractedEntity:
    type: str  # canonical, member of ENTITY_TYPES
    name: str  # whitespace-collapsed display name
    attributes: dict = field(default_factory=dict)

    @property
    def identity(self) -> tuple[str, str]:
        """Dedup/endpoint-matching key — same case-insensitive identity rule
        as memory.create_entity()."""
        return (self.type, self.name.casefold())


@dataclass(frozen=True)
class ExtractedRelationship:
    from_identity: tuple[str, str]  # ExtractedEntity.identity of the source
    to_identity: tuple[str, str]  # ExtractedEntity.identity of the target
    relation: str  # canonical UPPER_SNAKE verb


@dataclass(frozen=True)
class MemoryExtraction:
    """Everything Claude found in one memory, validated and canonicalized."""

    key: str
    entities: tuple[ExtractedEntity, ...]
    relationships: tuple[ExtractedRelationship, ...]


# ── Canonicalization (mirrors memory/graph/service.py — see module docstring) ─


def _canonical_type(raw) -> str:
    return _WS.sub("_", str(raw).strip().lower()) if isinstance(raw, str) else ""


def _canonical_name(raw) -> str:
    return _WS.sub(" ", raw.strip()) if isinstance(raw, str) else ""


def _canonical_relation(raw) -> str:
    return _WS.sub("_", raw.strip().upper()) if isinstance(raw, str) else ""


# ── Parsing ───────────────────────────────────────────────────────────────────


def _strip_to_json(raw: str) -> dict:
    """json.loads with the two recoveries worth having: a ``` fence around the
    payload, and prose around one top-level object. Anything else is a
    contract violation, not something to guess at."""
    text = (raw or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text.strip())
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise ExtractionParseError("response contains no JSON object")
        try:
            data = json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise ExtractionParseError(f"unparseable JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ExtractionParseError(f"expected a JSON object, got {type(data).__name__}")
    return data


def _valid_attributes(raw) -> dict:
    """Attributes are optional color, never load-bearing: keep at most
    MAX_ATTRIBUTES scalar-valued string keys, drop everything else silently."""
    if not isinstance(raw, dict):
        return {}
    kept = {}
    for key, value in raw.items():
        if len(kept) >= MAX_ATTRIBUTES:
            break
        if not isinstance(key, str) or not key.strip():
            continue
        if isinstance(value, bool) or value is None:
            kept[key.strip()] = value
        elif isinstance(value, (int, float)):
            kept[key.strip()] = value
        elif isinstance(value, str) and value.strip():
            kept[key.strip()] = value.strip()[:MAX_ATTRIBUTE_CHARS]
    return kept


def _parse_entities(raw) -> list[ExtractedEntity]:
    """Validate one memory's entity list, dropping (never repairing) bad items."""
    if not isinstance(raw, list):
        return []
    entities: list[ExtractedEntity] = []
    seen: set[tuple[str, str]] = set()
    for item in raw:
        if len(entities) >= MAX_ENTITIES_PER_MEMORY:
            break
        if not isinstance(item, dict):
            continue
        entity_type = _canonical_type(item.get("type"))
        name = _canonical_name(item.get("name"))
        if entity_type not in ENTITY_TYPES:
            continue
        if not name or len(name) > MAX_NAME_CHARS:
            continue
        if name.casefold() in FORBIDDEN_NAMES:
            continue
        entity = ExtractedEntity(entity_type, name, _valid_attributes(item.get("attributes")))
        if entity.identity in seen:
            continue
        seen.add(entity.identity)
        entities.append(entity)
    return entities


def _parse_relationships(raw, declared: set[tuple[str, str]]) -> list[ExtractedRelationship]:
    """Validate one memory's relationships against its own declared entities."""
    if not isinstance(raw, list):
        return []
    relationships: list[ExtractedRelationship] = []
    seen: set[tuple[tuple[str, str], tuple[str, str], str]] = set()
    for item in raw:
        if len(relationships) >= MAX_RELATIONSHIPS_PER_MEMORY:
            break
        if not isinstance(item, dict):
            continue
        relation = _canonical_relation(item.get("relation"))
        if not _RELATION_RE.match(relation) or len(relation) > MAX_RELATION_CHARS:
            continue
        from_identity = (
            _canonical_type(item.get("from_type")),
            _canonical_name(item.get("from_name")).casefold(),
        )
        to_identity = (
            _canonical_type(item.get("to_type")),
            _canonical_name(item.get("to_name")).casefold(),
        )
        if from_identity not in declared or to_identity not in declared:
            continue  # endpoint not declared in this memory
        if from_identity == to_identity:
            continue  # self-link (possibly via case-folding)
        triple = (from_identity, to_identity, relation)
        if triple in seen:
            continue
        seen.add(triple)
        relationships.append(ExtractedRelationship(from_identity, to_identity, relation))
    return relationships


def parse_extraction(raw: str, expected_keys: list[str]) -> dict[str, MemoryExtraction]:
    """Parse and validate one batch response. The contract's single entry point.

    Returns {key: MemoryExtraction} for every expected key Claude answered
    validly — a key answered with empty lists is a valid "nothing extractable
    here" and IS included (the caller marks it extracted). Keys Claude omitted
    are simply absent, so the caller leaves them pending for a retry.

    Raises ExtractionParseError only for envelope-level violations; every
    item-level defect is dropped per the strict-envelope/lenient-items rule.
    """
    data = _strip_to_json(raw)
    memories = data.get("memories")
    if not isinstance(memories, list):
        raise ExtractionParseError('missing or non-list "memories" field')

    expected = set(expected_keys)
    parsed: dict[str, MemoryExtraction] = {}
    for item in memories:
        if not isinstance(item, dict):
            continue
        key = item.get("key")
        if key not in expected or key in parsed:  # unknown or duplicate key
            continue
        entities = _parse_entities(item.get("entities"))
        relationships = _parse_relationships(
            item.get("relationships"), {e.identity for e in entities}
        )
        parsed[key] = MemoryExtraction(key, tuple(entities), tuple(relationships))
    return parsed
