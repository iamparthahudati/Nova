# Desktop Write Operations — Architecture (Canonical)

**Status:** Gate A approved for implementation. Gates B–F pending.  
**Scope:** Structured writes from any producer through a single mutation pipeline.

---

## Canonical Mutation Architecture

Every write producer in Nova converges on one pipeline:

```
Producer (chat, REST, CLI, mobile, scheduler, …)
        ↓
   MutationEvent          ← pure domain object, no producer metadata
        ↓
 finalize_mutations()     ← path-agnostic orchestration
        ↓
   ┌────┴────┬──────────────────┐
   ▼         ▼                  ▼
Domain    Semantic           Graph
Events    Memory             Scheduling
          (remember)         (entity extraction)
```

---

## 0. Governing Rules

1. **`MutationEvent` is a pure domain object.** No `tool_name`, `planner_result`, `tool_args`, or chat metadata. Only business mutation fields.
2. **`finalize_mutations()` is pure orchestration.** It does not know whether events came from chat, REST, CLI, or a future producer.
3. **Translators stay thin.** `mutation_chat.py` and `mutation_builders.py` map inputs → `MutationEvent` only. No business logic, events, or memory.
4. **`memory_from_mutation()`** depends only on `(entity_type, operation)` plus structured `entity`. Never planner strings or tool output.
5. **`MutationEvent.event_type` is the canonical WebSocket event name.** Do not derive event names elsewhere.
6. **Future producers reuse the same pipeline.** Adding mobile, CLI, or scheduled jobs requires no changes to `finalize_mutations()`.

---

## 1. `MutationEvent`

Module: `runtime/mutation_event.py`

```python
@dataclass(frozen=True)
class MutationEvent:
    event_type: str    # Canonical WS name — e.g. "task.created"
    entity_type: str   # Domain noun — e.g. "task"
    operation: str     # Verb — e.g. "create", "complete"
    entity: dict       # Structured row or event snapshot
    metadata: dict     # Optional WS payload extensions (default {})
```

### Pure domain — prohibited fields

| Prohibited | Reason |
|-----------|--------|
| `tool_name` | Chat-specific |
| `tool_args` | Chat-specific |
| `planner_result` | Chat-specific |
| `conversation_id` | Chat-specific |
| `source_producer` | Belongs in HTTP headers or logs, not domain events |

---

## 2. Producers and Translators

### 2.1 Producer → translator → pipeline

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│ POST /chat  │  │ REST router │  │ CLI (future)│  │ Job (future)│
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │                │
       ▼                ▼                ▼                ▼
 mutation_chat.py  mutation_builders.py  (future)         (future)
       │                │                │                │
       └────────────────┴────────────────┴────────────────┘
                                │
                         list[MutationEvent]
                                │
                                ▼
                    finalize_mutations()
                                │
              ┌─────────────────┼─────────────────┐
              ▼                 ▼                 ▼
        Domain Events    Semantic Memory   Graph Scheduling
```

### 2.2 `mutation_chat.py` (chat translator only)

```
Tool output (name, args, result)
        ↓
MutationEvent
```

- Planner confirmation strings used **only here** to detect success/failure.
- Loads or constructs `entity` from structured data.
- Called exclusively from `conversation.py`.

### 2.3 `mutation_builders.py` (REST translator only)

```
Domain row (dict)
        ↓
MutationEvent
```

- Pure functions. No strings, no tools, no I/O.

---

## 3. `finalize_mutations()` — Pure Orchestration

Module: `runtime/side_effects.py`

```python
def finalize_mutations(events: list[MutationEvent]) -> None:
    publish_mutation_events(events)
    apply_memory_producers(events)
    schedule_entity_extraction()
```

| Step | Module | Input |
|------|--------|-------|
| Domain events | `domain_events.publish_mutation_events` | `event.event_type` + `metadata` |
| Semantic memory | `memory_producers.memory_from_mutation` → `remember()` → `memory.created` | `(entity_type, operation, entity)` |
| Graph scheduling | `schedule_entity_extraction()` | None (async batch sweep) |

No knowledge of chat, REST, or any producer.

---

## 4. Domain Events (Unchanged Names)

| `event_type` | Gate |
|-------------|------|
| `task.created` | A |
| `task.updated` | A |
| `reminder.created` | C |
| `spending.logged` | C |
| `product.created` | D |
| `product.updated` | D |
| `calendar.updated` | E |
| `memory.created` | All (via producers) |
| `reflection.completed` | F |
| `graph.updated` | All (via extraction) |
| `pomodoro.completed` | Automation callback |

---

## 5. Memory Producer Policy

`memory_from_mutation(event)` — keyed on `(entity_type, operation)` + `entity`:

| entity_type | operation | Memory? |
|-------------|-----------|---------|
| `task` | `complete` | Yes |
| `task` | `create` | No |
| `product` | `ship` | Yes |
| `product` | `log_sale` | Yes |
| `calendar_event` | `create` | Yes |
| `progress` | `log` | Yes (if note ≥ 3 words) |
| `journal` | `create` | Yes |
| `automation` | `complete` | Yes (pomodoro) |

---

## 6. REST API (Gate A — Tasks)

| Method | Route | Builder |
|--------|-------|---------|
| POST | `/tasks` | `build_task_created` |
| POST | `/tasks/{id}/complete` | `build_task_completed` |

Response: `{ item: TaskResponse, meta: { message: string } }`

---

## 7. Test Requirements (Gate A)

Parity tests must prove chat and REST paths produce identical side effects when given equivalent mutations:

```
Chat  → tool_calls_to_mutations → finalize_mutations
REST  → mutation_builders       → finalize_mutations
```

Assert identical:
- Domain events (`event_type`, payload shape)
- Memory producer output (`memory_from_mutation`)
- Graph scheduling invoked

Only translators differ.

---

## 8. Implementation Gates

| Gate | Scope | Status |
|------|-------|--------|
| **A** | Mutation pipeline + task REST + tests | **Approved — implement** |
| B | Desktop task mutations | Pending |
| C | Reminders + spending | Pending |
| D | Products | Pending |
| E | Calendar | Pending |
| F | Reflection | Pending |

---

## 9. Success Criteria (Gate A)

- [x] `MutationEvent` is pure domain — no chat fields
- [x] `finalize_mutations()` is producer-agnostic
- [x] Translators are thin — no business logic, events, or memory
- [x] `memory_from_mutation()` uses only `(entity_type, operation, entity)`
- [x] Event names unchanged; `event_type` is canonical
- [x] Chat parity tests pass
- [x] REST task endpoints + tests pass
- [x] `conversation.py` refactored to use shared pipeline
