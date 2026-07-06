# Nova (formerly Rai) — AI Contracts

**Status:** Living document. Started at Milestone 2.6; grows one entry per AI milestone.
**Scope:** Every JSON structure that crosses the boundary between Brain and Claude, or between Brain and the rest of the system on an AI-mediated path.

> **Monorepo path note:** Source-of-truth files live under `apps/backend/`. Links below use the full monorepo path.

---

## 0. Why this document exists

Governing Rule 1 of Phase 2 (`ARCHITECTURE_v2.md`) is **Brain is the only Claude client.** A direct consequence: every place AI reasoning enters or leaves the system is a JSON contract at Brain's edge. Those contracts are load-bearing — a producer that mis-shapes its output, or a consumer that assumes a field that moved, breaks silently and at a distance. This document is the single place they are named.

### The one rule that keeps this document honest

**This file is an *index*, not a second definition.** Where a contract is already expressed as code (a schema list, a validator), that code is the **source of truth** and this document *points at it* — it never restates the fields, because two copies of a contract drift and a drifted contract doc is worse than none. This document only *defines* a contract outright when the contract has no single code home yet — and when that happens, it is flagged as debt to be made code-canonical, not left as prose forever.

Every AI milestone's Definition of Done gains one line: **"update `AI_CONTRACTS.md`."**

---

## 1. Contract registry

| Contract | Direction | Status | Source of truth | Milestone |
|---|---|---|---|---|
| Tool-calling schema | Brain → Claude (request) | **Live** | [`apps/backend/services/brain/tools.py`](../../apps/backend/services/brain/tools.py) `ASSISTANT_TOOLS` | Phase 1 (M3) |
| Tool result envelope | handler → Brain → Claude | **Live** | [`apps/backend/services/brain/tools.py`](../../apps/backend/services/brain/tools.py) `ToolHandler` | Phase 1 (M3) |
| Reflection output | Claude → Brain (response) | **Live, prose-canonical (debt)** | inline in [`apps/backend/services/brain/reflection.py`](../../apps/backend/services/brain/reflection.py) | Phase 1 (M7) |
| Entity & relationship extraction output | Claude → Brain (response) | **Live, code-canonical** | [`apps/backend/services/brain/extraction_contract.py`](../../apps/backend/services/brain/extraction_contract.py) | 2.7 |
| Learning insight output | Claude → Brain (response) | **Not yet defined** | — | 2.9 (planned) |

*(2.7 note: the registry originally reserved two rows — entity extraction and relationship extraction. They shipped as one contract, because relationships are validated against the entities declared in the same response; splitting them would have created two schemas that can only ever change together.)*

*(2.8 note: Milestone 2.8 shipped the **Context Engine** — `apps/backend/services/brain/context_engine/` now assembles everything Claude sees. It adds **no registry row**: the system prompt is prose at Brain's edge, not a JSON contract, and no new Claude-response shape was introduced. The section titles the engine renders are contract-adjacent in the §2.1 sense (editing them changes how Claude weighs context — treat them as contract text), and their code home is `context_engine/`'s provider `title` attributes. The Learning insight contract moves 2.8 → 2.9.)*

Rows marked *Not yet defined* are placeholders on purpose: specifying them before their milestone exists would be designing that milestone here, against the "one responsibility per milestone" rule. They are listed so they are not silently forgotten, not so they are pre-designed.

---

## 2. Live contracts

### 2.1 Tool-calling schema — `Brain → Claude`

**Source of truth:** `ASSISTANT_TOOLS` in [`apps/backend/services/brain/tools.py`](../../apps/backend/services/brain/tools.py). Do not restate the tool list here — it is a live Python structure handed directly to Claude's `tools` parameter, and it changes whenever a tool is added.

What is stable enough to record (the *envelope*, not the payload):

- Each tool is one Anthropic tool-definition object: `name`, `description`, `input_schema` (JSON Schema, `type: "object"`).
- Claude replies with zero or more `tool_use` blocks; Brain dispatches each through the injected `handlers` dict.
- A tool's `description` is a behavioral contract with Claude as much as a human-readable string — e.g. `open_app` says *"ONLY call this when the user explicitly wants to launch… NOT when merely mentioning."* Editing that wording changes routing behavior; treat it as contract text, not a comment.

### 2.2 Tool result envelope — `handler → Brain → Claude`

**Source of truth:** the `ToolHandler` type alias in [`apps/backend/services/brain/tools.py`](../../apps/backend/services/brain/tools.py): `Callable[[dict], str]`.

- A handler takes the tool's input dict and returns **one string** — the spoken/displayed confirmation. Brain feeds that string back to Claude as the `tool_result`.
- The return string is itself an implicit contract with two *other* consumers: Brain speaks it verbatim, and `memory_producers.py` pattern-matches its success wording (`"Task marked done."`, `"Event added: …"`) to decide what becomes a memory. This coupling is recorded as technical debt in `memory_producers.py`; it is noted here so the second consumer is visible from the contract side too.

### 2.3 Reflection output — `Claude → Brain`

This is the one contract this document currently **defines**, because it has no single code home — it is declared in a prompt sentence and parsed 20 lines away, with the valid-category list in a third place ([`apps/backend/services/brain/reflection.py`](../../apps/backend/services/brain/reflection.py)).

```json
{
  "observations": [
    { "text": "string — one specific behavioral observation",
      "category": "habits | work | finances | productivity | health | social",
      "confidence": 0.0 }
  ]
}
```

- Claude is instructed to return **JSON only**; Brain strips a ``` ```json ``` fence if present, then `json.loads`, then reads `data["observations"]` (defaulting to `[]` on absence).
- Consumer: `memory.replace_profile_observations(observations)` — a delete-and-reinsert today (2.8 is slated to make it versioned/superseding).
- **Debt:** the shape is not validated — a malformed `confidence` or an unknown `category` is written straight through. When 2.7/2.8 introduce their own Claude-output contracts, the intended pattern is to make them **code-canonical** (a schema + validator module in Brain, the way `ASSISTANT_TOOLS` is a code structure), and to retrofit this reflection contract onto the same mechanism rather than leave it prose-defined.

### 2.4 Entity & relationship extraction output — `Claude → Brain`

**Source of truth:** [`apps/backend/services/brain/extraction_contract.py`](../../apps/backend/services/brain/extraction_contract.py) — the first contract that is code-canonical from day one, as §3 intended. The envelope, the closed entity-type set (`ENTITY_TYPES`), every size ceiling, and the full validation policy are declared there (module docstring + constants) and enforced by `parse_extraction()`; this section deliberately restates none of them.

What belongs *here* is the envelope's role in the pipeline, not its fields:

- **Producer:** the batched prompt in [`apps/backend/services/brain/extraction.py`](../../apps/backend/services/brain/extraction.py). The prompt's type list and JSON example are contract text (same rule as §2.1's tool descriptions) — they must change in the same commit as `extraction_contract.py`.
- **Consumer:** `extraction.py` maps the response's short keys (`m1`…`mN`, never real memory UUIDs) back to ledger rows, then persists through `memory.create_entity()` / `memory.link_entities(source_memory_id=…)` — the provenance column built in 2.6 is populated exactly here.
- **Failure semantics:** strict envelope, lenient items. An envelope violation raises `ExtractionParseError` and the whole batch stays pending (retried up to `EXTRACTION_MAX_ATTEMPTS`); a malformed individual entity/relationship is dropped while its memory still completes. Idempotency state (`entities_extracted_at`, `extraction_attempts`) lives on the `memories` ledger, owned by Memory.
- **The §2.3 retrofit** (making the reflection contract code-canonical on this same mechanism) remains open debt — 2.7 built the pattern, it did not migrate reflection onto it.

---

## 3. Deferred contracts (named, not specified)

These will be filled in *by* their milestone, not before it. The one-line intent below exists only so the milestone knows what slot to fill; it is not a design.

- **2.8 Learning insight output.** Claude turns locally pre-filtered patterns into insight/nudge records written via `memory.remember(source_type="insight")`. Contract defined when the Learning Engine exists.

---

## 4. How to change a contract

1. Change the **source of truth** (the code), not this file, for any Live/code-canonical contract.
2. Update this file's registry row if a contract's status, direction, or source location changes.
3. For a prose-canonical contract (only §2.3 today), change both the prompt and the parser together, and update §2.3.
4. Adding a new AI-mediated Claude call = adding a contract. Register it here in the same PR — that is the milestone's DoD line.
