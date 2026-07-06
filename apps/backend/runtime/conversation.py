"""Single conversation pipeline — shared by voice, chat REPL, and POST /chat.

Composition-root glue: wires Brain tool handlers to services, persists memories,
fires entity extraction, and publishes WebSocket events. No domain rules live here.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Optional

import conversation_memory
import identity
from memory import remember
from services import automation, brain, calendar, knowledge, planner, voice

from .mutation_chat import tool_calls_to_mutations
from .mutation_builders import build_pomodoro_completed
from .mutation_event import MutationEvent
from .side_effects import finalize_mutations, schedule_entity_extraction
from .events import publish

# --- Tool-handler wiring -------------------------------------------------------
# Brain only knows tool names and input dicts; each entry adapts a tool call to
# the service that performs it — dependency injection for brain.route().

TOOL_HANDLERS = {
    "send_whatsapp_message": lambda a: automation.send_whatsapp_message(a["contact"], a["message"]),
    "open_app": lambda a: automation.open_app(a.get("target", "").lower().strip()),
    "add_task": lambda a: planner.log_task(a["text"], a.get("due")),
    "complete_task": lambda a: planner.complete_task(a["text"]),
    "add_money": lambda a: planner.log_money(a["type"], float(a["amount"]), a.get("note", "")),
    "add_progress": lambda a: planner.log_progress(a["note"], a.get("area", "")),
    "add_product": lambda a: planner.add_product(a["name"], a.get("store", ""), a.get("price")),
    "ship_product": lambda a: planner.ship_product(a["name"]),
    "log_sale": lambda a: planner.log_sale(a["name"]),
    "add_calendar_event": lambda a: calendar.create_event(a["title"], a["date"], a.get("time")),
    "get_events": lambda a: calendar.describe_events(a.get("day")),
    "add_reminder": lambda a: planner.save_reminder(a["text"], a["remind_date"], a.get("remind_time")),
    "get_weather": lambda a: knowledge.get_weather(a.get("location", "")),
    "get_github_notifications": lambda a: knowledge.get_github_notifications(),
    "get_rss_updates": lambda a: knowledge.get_rss_updates(),
    "run_reflection": lambda a: knowledge.run_reflection(),
    "journal": lambda a: knowledge.handle_journal(a["text"]),
    "log_habit": lambda a: planner.log_habit(a["name"]),
    "get_habits": lambda a: planner.describe_habits_today(),
    "start_pomodoro": lambda a: automation.start_pomodoro(
        int(a.get("minutes") or 25), voice.speak, on_complete=_remember_pomodoro),
    "read_my_day": lambda a: planner.build_daily_plan(),
    "get_spending_summary": lambda a: planner.get_spending_summary(a.get("period", "this week")),
}

_tool_events: list[tuple[str, dict, str]] = []


def _instrument(name: str, handler):
    """Wrap one tool handler to record (tool, args, result) for the producer pass."""
    def call(args):
        result = handler(args)
        _tool_events.append((name, args, result))
        return result
    return call


INSTRUMENTED_HANDLERS = {name: _instrument(name, h) for name, h in TOOL_HANDLERS.items()}


def _journal_mutations(tools_called: list[dict]) -> list[MutationEvent]:
    """Journal has no domain WS event — memory producer only (empty event_type)."""
    events: list[MutationEvent] = []
    for tool in tools_called:
        if tool["name"] != "journal":
            continue
        text = str((tool.get("args") or {}).get("text", "")).strip()
        if not text:
            continue
        events.append(MutationEvent(
            event_type="",
            entity_type="journal",
            operation="create",
            entity={"text": text},
        ))
    return events


def _remember_pomodoro(minutes: int) -> None:
    finalize_mutations([build_pomodoro_completed(minutes)])


def _remember_exchange(transcript: str, reply: str, conversation_id: Optional[str]) -> None:
    for record in conversation_memory.memories_from_exchange(transcript, reply, conversation_id):
        try:
            remember(**record)
            from .domain_events import publish_memory_created
            publish_memory_created(source=record.get("source_type", "conversation"))
        except Exception as exc:
            print(f"[memory] write skipped: {exc}")


@dataclass
class ConversationResult:
    """Outcome of one turn through the conversation pipeline."""

    reply: str = ""
    conversation_id: str = ""
    error: Optional[str] = None
    tools_called: list[dict] = field(default_factory=list)


def process_message(
    transcript: str,
    conversation_id: Optional[str] = None,
    *,
    speak_output: bool = False,
    emit_events: bool = True,
) -> ConversationResult:
    """Route a transcript through Brain and persist side effects.

    Returns a structured result for API callers; voice/REPL use process_transcript()
    which wraps this and handles terminal I/O.
    """
    cid = conversation_id or str(uuid.uuid4())
    transcript = (transcript or "").strip()

    if not transcript:
        fallback = "I didn't catch that"
        if speak_output:
            voice.speak(fallback)
        if emit_events:
            publish("chat", "chat.error", {"conversation_id": cid, "message": fallback})
        return ConversationResult(reply=fallback, conversation_id=cid, error="empty_transcript")

    if emit_events:
        publish("chat", "chat.started", {"conversation_id": cid, "transcript": transcript})

    print(f'Heard: "{transcript}"')
    print("Routing…")
    if emit_events:
        publish("chat", "chat.routing", {"conversation_id": cid})

    _tool_events.clear()
    try:
        reply = brain.route(transcript, INSTRUMENTED_HANDLERS, brain.history.get())
        brain.history.add_turn(transcript, reply)

        tools_called = [
            {"name": name, "args": args, "result": result}
            for name, args, result in _tool_events
        ]
        if emit_events:
            for tool in tools_called:
                publish("chat", "chat.tool_called", {
                    "conversation_id": cid,
                    "tool": tool["name"],
                    "args": tool["args"],
                    "result": tool["result"],
                })
            publish("chat", "chat.reply", {"conversation_id": cid, "reply": reply})

        print(f'{identity.ASSISTANT_NAME}: "{reply}"')
        if speak_output:
            voice.speak(reply)

        mutations = tool_calls_to_mutations(tools_called) + _journal_mutations(tools_called)
        if mutations:
            finalize_mutations(mutations)
        else:
            _remember_exchange(transcript, reply, cid)
            schedule_entity_extraction()

        if emit_events:
            publish("chat", "chat.finished", {"conversation_id": cid, "reply": reply})

        return ConversationResult(
            reply=reply,
            conversation_id=cid,
            tools_called=tools_called,
        )
    except Exception as exc:
        msg = "Sorry, I couldn't process that right now"
        print(f"[error] routing failed: {exc}")
        if speak_output:
            voice.speak(msg)
        if emit_events:
            publish("chat", "chat.error", {
                "conversation_id": cid,
                "message": msg,
            })
        return ConversationResult(
            reply=msg,
            conversation_id=cid,
            error=str(exc),
        )


def process_transcript(
    transcript: str,
    conversation_id: Optional[str] = None,
    speak_output: bool = True,
) -> None:
    """Voice/REPL entry — terminal I/O wrapper around process_message()."""
    if not (transcript or "").strip():
        print("Heard nothing — try speaking clearly.\n")
    result = process_message(
        transcript,
        conversation_id,
        speak_output=speak_output,
        emit_events=False,
    )
    if not result.error or result.error == "empty_transcript":
        pass  # messages already printed/spoken inside process_message
    print()
