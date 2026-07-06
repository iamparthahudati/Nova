"""Map domain mutations to explicit domain WebSocket events."""

from __future__ import annotations

from .events import publish
from .mutation_event import MutationEvent


def publish_mutation_events(events: list[MutationEvent]) -> None:
    """Emit one domain event per mutation. event_type is the canonical WS name."""
    seen: set[str] = set()
    for event in events:
        if not event.event_type or event.event_type in seen:
            continue
        seen.add(event.event_type)
        payload = {
            "entity_type": event.entity_type,
            "operation": event.operation,
            **event.metadata,
        }
        publish("events", event.event_type, payload)


def publish_memory_created(source: str = "conversation") -> None:
    """Emit after a successful memory.remember() — sole source for memory.created."""
    publish("events", "memory.created", {"source": source})


def publish_graph_updated(reason: str = "entity_extraction") -> None:
    publish("events", "graph.updated", {"reason": reason})


def publish_pomodoro_completed(minutes: int) -> None:
    publish("events", "pomodoro.completed", {"minutes": minutes})
