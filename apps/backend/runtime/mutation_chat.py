"""Chat-side translator — tool output to MutationEvent. No side effects."""

from __future__ import annotations

from typing import Optional

import memory

from .mutation_event import MutationEvent

# Tool name → (event_type, entity_type, operation)
_CHAT_TOOL_MUTATIONS: dict[str, tuple[str, str, str]] = {
    "add_task": ("task.created", "task", "create"),
    "complete_task": ("task.updated", "task", "complete"),
    "add_money": ("spending.logged", "money", "log"),
    "add_progress": ("progress.logged", "progress", "log"),
    "add_product": ("product.created", "product", "create"),
    "ship_product": ("product.updated", "product", "ship"),
    "log_sale": ("product.updated", "product", "log_sale"),
    "add_calendar_event": ("calendar.updated", "calendar_event", "create"),
    "add_reminder": ("reminder.created", "reminder", "create"),
    "log_habit": ("habit.logged", "habit", "log"),
    "run_reflection": ("reflection.completed", "profile", "reflect"),
}


def tool_mutation_succeeded(tool: str, args: dict, result: str) -> bool:
    """True when a chat tool handler confirms a successful mutation."""
    result = (result or "").strip()
    args = args or {}

    if tool == "add_task":
        return result.startswith("Task logged.")
    if tool == "complete_task":
        return result == "Task marked done."
    if tool == "add_money":
        return result in ("Logged earnings.", "Logged expense.")
    if tool == "add_progress":
        return result == "Progress logged."
    if tool == "add_product":
        return result == "Product added."
    if tool == "ship_product":
        return result == "Product marked shipped."
    if tool == "log_sale":
        return result == "Sale logged."
    if tool == "add_calendar_event":
        return result.startswith("Event added: ")
    if tool == "add_reminder":
        return result.startswith("Reminder saved:")
    if tool == "log_habit":
        return result.startswith("Habit logged:")
    if tool == "run_reflection":
        return result.startswith("Reflection complete.")
    return False


def tool_calls_to_mutations(tools_called: list[dict]) -> list[MutationEvent]:
    """Translate successful chat tool calls into domain mutation events."""
    mutations: list[MutationEvent] = []
    for tool in tools_called:
        event = _tool_call_to_mutation(
            tool["name"],
            tool.get("args") or {},
            tool.get("result") or "",
        )
        if event is not None:
            mutations.append(event)
    return mutations


def _tool_call_to_mutation(tool: str, args: dict, result: str) -> Optional[MutationEvent]:
    if not tool_mutation_succeeded(tool, args, result):
        return None

    mapping = _CHAT_TOOL_MUTATIONS.get(tool)
    if mapping is None:
        return None

    event_type, entity_type, operation = mapping
    entity = _entity_for_tool(tool, args, result)
    if entity is None:
        return None

    metadata: dict = {}
    entity_id = entity.get("id")
    if entity_id is not None:
        metadata["entity_id"] = entity_id

    return MutationEvent(
        event_type=event_type,
        entity_type=entity_type,
        operation=operation,
        entity=entity,
        metadata=metadata,
    )


def _entity_for_tool(  # noqa: C901 — DEBT(nova-ci-2): exceeds Handbook §3.1 complexity 12
    tool: str, args: dict, result: str
) -> Optional[dict]:
    if tool == "add_task":
        row = memory.find_task_by_text(str(args.get("text", "")).strip(), status="open")
        if row is not None:
            return row
        return {
            "text": str(args.get("text", "")).strip(),
            "due": args.get("due"),
            "status": "open",
        }

    if tool == "complete_task":
        text = str(args.get("text", "")).strip()
        row = memory.find_task_by_text(text, status="done")
        if row is not None:
            return row
        return {"text": text, "status": "done"}

    if tool == "add_money":
        row = memory.get_latest_money(
            type_=str(args.get("type", "")),
            amount=float(args.get("amount", 0)),
        )
        if row is not None:
            return row
        return {
            "type": str(args.get("type", "")),
            "amount": float(args.get("amount", 0)),
            "note": str(args.get("note", "")),
        }

    if tool == "add_progress":
        return {
            "note": str(args.get("note", "")).strip(),
            "area": str(args.get("area", "")).strip(),
        }

    if tool == "add_product":
        name = str(args.get("name", "")).strip()
        row = memory.find_product_by_name(name)
        if row is not None:
            return row
        return {
            "name": name,
            "store": str(args.get("store", "")),
            "price": args.get("price"),
            "status": "building",
        }

    if tool == "ship_product":
        name = str(args.get("name", "")).strip()
        row = memory.find_product_by_name(name)
        if row is not None:
            return row
        return {"name": name, "status": "shipped"}

    if tool == "log_sale":
        name = str(args.get("name", "")).strip()
        row = memory.find_product_by_name(name)
        if row is not None:
            return row
        return {"name": name}

    if tool == "add_calendar_event":
        detail = result[len("Event added: ") :].rstrip(".")
        return {
            "title": str(args.get("title", "")).strip(),
            "date": str(args.get("date", "")).strip(),
            "time": args.get("time"),
            "detail": detail,
        }

    if tool == "add_reminder":
        row = memory.get_latest_reminder(str(args.get("text", "")).strip())
        if row is not None:
            return row
        return {
            "text": str(args.get("text", "")).strip(),
            "remind_date": str(args.get("remind_date", "")).strip(),
            "remind_time": args.get("remind_time"),
        }

    if tool == "log_habit":
        name = str(args.get("name", "")).strip()
        row = memory.get_latest_habit(name)
        if row is not None:
            return row
        return {"name": name}

    if tool == "run_reflection":
        return {"summary": result}

    return None
