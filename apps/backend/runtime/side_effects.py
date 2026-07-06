"""Post-mutation orchestration — producer-agnostic."""

from __future__ import annotations

import threading

from memory import remember
from services import brain

from .domain_events import publish_memory_created, publish_mutation_events
from .mutation_event import MutationEvent

import memory_producers


def apply_memory_producers(events: list[MutationEvent]) -> bool:
    """Run semantic memory producers for mutation events. Returns True if any memory written."""
    wrote = False
    for record in memory_producers.memories_from_mutations(events):
        try:
            remember(**record)
            publish_memory_created(source=record.get("source_type", "tool"))
            wrote = True
        except Exception as exc:
            print(f"[memory] producer write skipped: {exc}")
    return wrote


def schedule_entity_extraction() -> None:
    """Background entity extraction sweep — same schedule as chat turns."""

    def sweep() -> None:
        try:
            from .domain_events import publish_graph_updated

            result = brain.run_entity_extraction()
            if result:
                print(f"[extraction] {result}")
                from .events import publish

                publish("events", "entity_extraction.completed", {"summary": result})
                publish_graph_updated(reason="entity_extraction")
        except Exception as exc:
            print(f"[extraction] skipped: {exc}")

    threading.Thread(target=sweep, daemon=True).start()


def finalize_mutations(events: list[MutationEvent]) -> None:
    """Single post-mutation pipeline for all producers."""
    if not events:
        return
    publish_mutation_events(events)
    apply_memory_producers(events)
    schedule_entity_extraction()
