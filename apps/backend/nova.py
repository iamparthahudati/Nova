#!/usr/bin/env python3
"""
Nova (formerly Rai) — always-on voice-command app launcher for macOS.

This file is the composition root: it wires the seven services together
(dependency injection via the TOOL_HANDLERS map and direct calls below) and
owns application startup, the run loop, and shutdown. It contains no
business logic of its own — every domain rule (date parsing, storage,
Claude calls, AppleScript, audio) lives inside a service.
"""

import sys
import threading
import uuid
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv

import identity
from memory import init_db
from paths import REPO_ROOT
from runtime.conversation import process_transcript
from runtime.domain_events import publish_graph_updated
from runtime.events import publish
from services import brain, calendar, knowledge, planner, voice

load_dotenv(REPO_ROOT / ".env")  # reads repo-root .env into os.environ at startup


def _extract_entities_async() -> None:
    """Kick Brain's entity-extraction sweep on a background thread (§2.7)."""

    def sweep():
        try:
            result = brain.run_entity_extraction()
            if result:
                print(f"[extraction] {result}")
                publish("events", "entity_extraction.completed", {"summary": result})
                publish_graph_updated(reason="entity_extraction")
        except Exception as exc:
            print(f"[extraction] skipped: {exc}")

    threading.Thread(target=sweep, daemon=True).start()


class AssistantApp:
    """Owns the application lifecycle: startup, the run loop, and shutdown."""

    def __init__(self) -> None:
        self.model = None
        self.last_briefing_date: Optional[str] = None
        self.last_wrapup_date: Optional[str] = None
        self.announced_reminder_ids: set[int] = set()
        self.last_reminder_check_minute: Optional[str] = None

    def start(self) -> None:
        brain.check_api_config()
        init_db()
        brain.set_calendar_source(calendar.get_events)
        self._maybe_run_reflection()
        _extract_entities_async()

        print("Loading Whisper model (first run may download weights)…")
        self.model = voice.load_model()
        print("Whisper loaded.")
        print(f"{identity.ASSISTANT_NAME} is listening for the wake word…\n")

        self._run_loop()

    def stop(self) -> None:
        print(f"\n{identity.ASSISTANT_NAME} stopped.")
        sys.exit(0)

    def _maybe_run_reflection(self) -> None:
        if knowledge.should_run_reflection():
            print("[reflection] Running weekly reflection job…")
            try:
                result = knowledge.run_reflection()
                print(f"[reflection] {result}")
            except Exception as exc:
                print(f"[reflection] error: {exc}")

    def _check_scheduled_jobs(self, now: datetime) -> None:
        today_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M")

        if time_str == planner.BRIEFING_TIME and self.last_briefing_date != today_str:
            briefing = planner.build_morning_briefing(weather_provider=knowledge.get_weather)
            print(f"\nMorning briefing: {briefing}\n")
            voice.speak(briefing)
            self.last_briefing_date = today_str

        if (
            planner.EVENING_WRAPUP_TIME
            and time_str == planner.EVENING_WRAPUP_TIME
            and self.last_wrapup_date != today_str
        ):
            wrapup = planner.build_evening_wrapup()
            print(f"\nEvening wrap-up: {wrapup}\n")
            voice.speak(wrapup)
            self.last_wrapup_date = today_str

        if self.last_reminder_check_minute == time_str:
            return
        self.last_reminder_check_minute = time_str
        for reminder in planner.due_timed_reminders(now):
            if reminder["id"] in self.announced_reminder_ids:
                continue
            self.announced_reminder_ids.add(reminder["id"])
            announcement = f"Reminder: {reminder['text']}"
            print(f"\n{announcement}\n")
            voice.speak(announcement)
            publish(
                "events",
                "reminder.triggered",
                {
                    "id": reminder["id"],
                    "text": reminder["text"],
                },
            )

    def _run_loop(self) -> None:
        prev_hop = voice.new_listener_state()

        try:
            while True:
                self._check_scheduled_jobs(datetime.now())

                heard, prev_hop = voice.poll_wake_word(self.model, prev_hop)

                if heard:
                    conversation_id = str(uuid.uuid4())
                    process_transcript(voice.record_command(self.model), conversation_id)
                    prev_hop = voice.new_listener_state()

                    while voice.wait_for_followup(self.model):
                        process_transcript(voice.record_command(self.model), conversation_id)
                    brain.history.clear()
                    print("Going back to sleep.")
                    prev_hop = voice.new_listener_state()

        except KeyboardInterrupt:
            self.stop()


def chat_mode() -> None:
    """Text-only REPL: type commands instead of speaking them."""
    brain.check_api_config()
    init_db()
    brain.set_calendar_source(calendar.get_events)
    _extract_entities_async()
    conversation_id = str(uuid.uuid4())
    print(
        f"{identity.ASSISTANT_NAME} chat mode. Type a command (e.g. 'open chrome'), or 'quit' to exit.\n"
    )
    while True:
        try:
            line = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line in ("quit", "exit"):
            break
        if not line:
            continue
        process_transcript(line, conversation_id, speak_output=False)


def main() -> None:
    if "--chat" in sys.argv:
        chat_mode()
    else:
        AssistantApp().start()


if __name__ == "__main__":
    main()
