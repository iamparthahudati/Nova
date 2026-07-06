"""Mutation events → memory write policy.

Pure heuristics + record construction. NO I/O and NO persistence.
Policy keyed on (entity_type, operation) and structured entity data only.
"""

from datetime import datetime, timezone
from typing import Optional

from runtime.mutation_event import MutationEvent

MIN_PROGRESS_WORDS = 3
SHIPPED_IMPORTANCE = 0.70
SALE_IMPORTANCE = 0.60


def _now_iso(now: Optional[datetime]) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


def _record(
    text: str,
    source_type: str,
    metadata: dict,
    importance: Optional[float] = None,
) -> dict:
    record: dict[str, object] = {
        "text": text,
        "source_type": source_type,
        "source_id": None,
        "metadata": metadata,
    }
    if importance is not None:
        record["importance"] = importance
    return record


def memory_from_mutation(  # noqa: C901 — DEBT(nova-ci-2): exceeds Handbook §3.1 complexity 12
    event: MutationEvent,
    now: Optional[datetime] = None,
) -> Optional[dict]:
    """One mutation event → remember() kwargs, or None to skip."""
    timestamp = _now_iso(now)
    entity = event.entity or {}

    if event.entity_type == "task" and event.operation == "complete":
        text = str(entity.get("text", "")).strip()
        if not text:
            return None
        return _record(f"Completed task: {text}", "task", {"timestamp": timestamp})

    if event.entity_type == "progress" and event.operation == "log":
        note = str(entity.get("note", "")).strip()
        if len(note.split()) < MIN_PROGRESS_WORDS:
            return None
        area = str(entity.get("area", "")).strip()
        text = f"Progress in {area}: {note}" if area else f"Progress: {note}"
        metadata = {"timestamp": timestamp}
        if area:
            metadata["area"] = area
        return _record(text, "progress", metadata)

    if event.entity_type == "product" and event.operation == "ship":
        name = str(entity.get("name", "")).strip()
        if not name:
            return None
        return _record(
            f"Shipped product: {name}",
            "milestone",
            {"timestamp": timestamp, "product": name},
            importance=SHIPPED_IMPORTANCE,
        )

    if event.entity_type == "product" and event.operation == "log_sale":
        name = str(entity.get("name", "")).strip()
        if not name:
            return None
        return _record(
            f"Sold a unit of {name}.",
            "milestone",
            {"timestamp": timestamp, "product": name},
            importance=SALE_IMPORTANCE,
        )

    if event.entity_type == "calendar_event" and event.operation == "create":
        detail = str(entity.get("detail", "")).strip()
        if not detail:
            title = str(entity.get("title", "")).strip()
            date = str(entity.get("date", "")).strip()
            time = entity.get("time")
            detail = f"{title} on {date}" + (f" at {time}" if time else "")
        if not detail:
            return None
        return _record(
            f"Calendar event created: {detail}.",
            "calendar_event",
            {"timestamp": timestamp},
        )

    if event.entity_type == "journal" and event.operation == "create":
        text = str(entity.get("text", "")).strip()
        if not text:
            return None
        return _record(text, "journal", {"timestamp": timestamp})

    if event.entity_type == "automation" and event.operation == "complete":
        minutes = int(entity.get("minutes", 0))
        if minutes <= 0:
            return None
        return _record(
            f"Completed a {minutes}-minute pomodoro focus session.",
            "automation",
            {"timestamp": timestamp, "duration_minutes": minutes, "workflow": "pomodoro"},
        )

    return None


def memories_from_mutations(
    events: list[MutationEvent],
    now: Optional[datetime] = None,
) -> list[dict]:
    records = []
    for event in events:
        record = memory_from_mutation(event, now)
        if record is not None:
            records.append(record)
    return records


def memory_from_tool_event(
    tool: str,
    args: dict,
    result: str,
    now: Optional[datetime] = None,
) -> Optional[dict]:
    """Deprecated — chat path uses mutation_chat → memory_from_mutation."""
    from runtime.mutation_chat import _tool_call_to_mutation

    event = _tool_call_to_mutation(tool, args or {}, result or "")
    if event is None:
        return None
    return memory_from_mutation(event, now)


def memories_from_events(
    events: list[tuple[str, dict, str]],
    now: Optional[datetime] = None,
) -> list[dict]:
    """Deprecated — prefer memories_from_mutations via mutation_chat translator."""
    from runtime.mutation_chat import tool_calls_to_mutations

    return memories_from_mutations(
        tool_calls_to_mutations([{"name": n, "args": a, "result": r} for n, a, r in events]), now
    )


def memory_from_pomodoro(minutes: int, now: Optional[datetime] = None) -> dict:
    minutes = int(minutes)
    return _record(
        f"Completed a {minutes}-minute pomodoro focus session.",
        "automation",
        {"timestamp": _now_iso(now), "duration_minutes": minutes, "workflow": "pomodoro"},
    )
