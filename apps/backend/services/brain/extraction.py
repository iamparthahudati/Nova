"""Entity extraction — memories → knowledge graph (Milestone 2.7).

The judgment half of the graph pipeline (Rule 1: extraction is reasoning, so
it lives in Brain). Memory hands over rows it hasn't processed; Claude reads
them and returns the contract shape (extraction_contract.py); this module
persists the result through Memory's public graph verbs and stamps the rows
done. Same precedent as reflection.py: Brain may *write through* Memory's
public API, it just never touches storage itself.

    memory.memories_pending_entity_extraction()      ← what still needs doing
      → one batched Claude call over up to BATCH_SIZE memories
      → extraction_contract.parse_extraction()       ← validate/canonicalize
      → memory.create_entity() / memory.link_entities(source_memory_id=…)
      → memory.mark_entities_extracted()             ← never processed again

Why a pending-sweep instead of extracting inline in remember():

  * Idempotency for free. The extracted-at stamp lives on the ledger row, so
    a memory is processed exactly once no matter how often the sweep runs —
    and since re-processing is what would double-reinforce edge weights, the
    stamp is also the "never duplicate relationships" guarantee's second half
    (the graph's own dedup being the first).
  * Failure recovery for free. Anything that dies — API call, parse,
    process — leaves the rows unstamped, and the next sweep retries them,
    up to MAX_ATTEMPTS (attempts are counted *before* the call, so even a
    crash consumes budget and a poison-pill memory can't wedge the pipeline).
  * Batching for free. One Claude call covers a batch, and the entire
    pre-2.7 backlog drains through the same code path at startup — no
    separate backfill script.
  * The turn stays fast. The composition root triggers the sweep after the
    reply is already spoken; extraction latency is invisible to the user.

Concurrency: the root fires the sweep from a background thread each turn, so
a non-blocking module lock collapses overlapping triggers into one run —
two concurrent sweeps could double-process a row between its SELECT and its
stamp. In-process only, which is all there is: nothing else extracts.
"""

import json
import threading
import urllib.request

from memory import (
    create_entity,
    link_entities,
    mark_entities_extracted,
    memories_pending_entity_extraction,
    record_entity_extraction_attempt,
)

from . import extraction_contract as contract
from .config import (
    ANTHROPIC_API_URL, CLAUDE_API_KEY, CLAUDE_MODEL,
    ENTITY_EXTRACTION_ENABLED, EXTRACTION_BATCH_SIZE,
    EXTRACTION_MAX_ATTEMPTS, EXTRACTION_MAX_BATCHES,
)

# Output ceiling for one batch response. Sized for BATCH_SIZE memories at the
# contract's per-memory caps; a response this long means runaway invention.
_MAX_TOKENS = 2000

# A memory's text is one or two sentences; journal entries can run longer.
# The prompt truncates so one essay-length entry can't crowd out its batch.
_MEMORY_TEXT_CHARS = 800

_run_lock = threading.Lock()

_SYSTEM = (
    "You build a personal knowledge graph from an assistant's memory records. "
    "Respond with JSON only — no prose, no markdown fence."
)

# The prompt is contract text (AI_CONTRACTS.md §2.1's rule applies): the type
# list must match extraction_contract.ENTITY_TYPES and the example must match
# the envelope in extraction_contract.py's docstring. Change them together.
_INSTRUCTIONS = """\
For each memory record below, extract the specific entities it mentions and \
the relationships between them.

Entity types — use exactly one of: person, project, task, goal, habit, \
meeting, document, conversation, product, organization, place, topic.

Relations are UPPER_SNAKE verb phrases, e.g. WORKS_ON, BELONGS_TO, INVOLVES, \
RELATES_TO, MENTIONS, SUPPORTS, PART_OF, USES, ATTENDS, LOCATED_IN.

Rules:
- Extract only what a record explicitly states. Never infer, never invent.
- Never create an entity for the records' owner ("I", "me", "the user") or \
for the assistant — records are written from the owner's perspective.
- Named, specific things only ("Priya Sharma", "the Aurora rebrand"); skip \
generic references ("a meeting", "someone").
- Both endpoints of every relationship must appear in that same record's \
"entities" list.
- Every record key must appear in your output. A record with nothing \
extractable gets empty lists.

Respond with exactly this JSON shape:
{"memories": [{"key": "m1", "entities": [{"type": "person", "name": "Priya \
Sharma", "attributes": {"role": "designer"}}], "relationships": [{"from_type": \
"person", "from_name": "Priya Sharma", "to_type": "project", "to_name": \
"Aurora rebrand", "relation": "WORKS_ON"}]}]}

Memory records:
"""


def run_entity_extraction() -> str:
    """Sweep pending memories into the knowledge graph. Returns a summary line,
    or "" when there was nothing to do (disabled / already running / no
    pending rows) so callers can print only when something happened."""
    if not ENTITY_EXTRACTION_ENABLED:
        return ""
    if not _run_lock.acquire(blocking=False):
        return ""                    # a sweep is already draining the queue
    try:
        return _sweep()
    finally:
        _run_lock.release()


def _sweep() -> str:
    done = entities_written = links_written = failed = 0
    seen: set[str] = set()           # never retry a failure within one run

    for _ in range(EXTRACTION_MAX_BATCHES):
        pending = [
            row for row in memories_pending_entity_extraction(
                limit=EXTRACTION_BATCH_SIZE, max_attempts=EXTRACTION_MAX_ATTEMPTS,
            )
            if row["id"] not in seen
        ]
        if not pending:
            break
        seen.update(row["id"] for row in pending)

        # m1..mN → ledger row, for mapping Claude's keys back to real ids.
        keyed = {f"m{i + 1}": row for i, row in enumerate(pending)}

        # Attempts are recorded BEFORE the call: a crash or timeout still
        # consumes retry budget, so nothing can be retried forever.
        record_entity_extraction_attempt([row["id"] for row in pending])

        try:
            raw = _call_claude(_build_prompt(keyed))
        except Exception as exc:
            print(f"[extraction] Claude call failed: {exc}")
            failed += len(pending)
            break                    # API trouble is systemic — stop this run

        try:
            parsed = contract.parse_extraction(raw, list(keyed))
        except contract.ExtractionParseError as exc:
            print(f"[extraction] contract violation, batch left for retry: {exc}")
            failed += len(pending)
            break                    # malformed envelope now likely means malformed next batch too

        for key, row in keyed.items():
            extraction = parsed.get(key)
            if extraction is None:   # Claude omitted the key → stays pending
                failed += 1
                continue
            try:
                n_entities, n_links = _persist(row["id"], extraction)
            except Exception as exc:
                print(f"[extraction] persist failed for memory {row['id']}: {exc}")
                failed += 1
                continue             # left unstamped → retried next sweep
            mark_entities_extracted([row["id"]])
            done += 1
            entities_written += n_entities
            links_written += n_links

    if not seen:
        return ""
    summary = (
        f"Entity extraction: {done}/{len(seen)} memories → "
        f"{entities_written} entities, {links_written} relationships."
    )
    if failed:
        summary += f" {failed} left pending for retry."
    return summary


def _persist(memory_id: str, extraction: contract.MemoryExtraction) -> tuple[int, int]:
    """Write one memory's extraction through Memory's public graph verbs.

    create_entity() dedups by (type, name) and link_entities() folds repeat
    triples into edge weight, so persisting the same *fact* from different
    memories reinforces rather than duplicates — the contract already
    guaranteed no duplicates within this one extraction.
    """
    entity_ids: dict[tuple[str, str], str] = {}
    for entity in extraction.entities:
        entity_ids[entity.identity] = create_entity(
            entity.type, entity.name, entity.attributes or None
        )

    links = 0
    for rel in extraction.relationships:
        from_id = entity_ids[rel.from_identity]
        to_id = entity_ids[rel.to_identity]
        if from_id == to_id:
            # Distinct in the contract but folded into one entity by the
            # graph's own canonicalization — an edge to itself is meaningless.
            continue
        link_entities(from_id, to_id, rel.relation, source_memory_id=memory_id)
        links += 1
    return len(entity_ids), links


def _build_prompt(keyed: dict[str, dict]) -> str:
    lines = []
    for key, row in keyed.items():
        text = " ".join(row["text"].split())
        if len(text) > _MEMORY_TEXT_CHARS:
            text = text[:_MEMORY_TEXT_CHARS] + "…"
        lines.append(f"{key} [{row['source_type']}]: {text}")
    return _INSTRUCTIONS + "\n".join(lines)


def _call_claude(prompt: str) -> str:
    """One un-tooled completion call. Third copy of this urllib block in Brain
    (client.py, reflection.py) — recorded as debt; extracting a shared helper
    is a refactor for its own milestone, not a side effect of this one."""
    payload = json.dumps({
        "model": CLAUDE_MODEL,
        "max_tokens": _MAX_TOKENS,
        "system": _SYSTEM,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(
        ANTHROPIC_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.loads(resp.read())
    return body["content"][0]["text"]
