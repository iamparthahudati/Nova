"""Pomodoro/focus timer — fires a spoken message and a notification when done.

Takes the speak function as a parameter rather than importing services.voice,
keeping Automation a leaf dependency (same shape as Calendar and Voice).
`on_complete` follows the identical injection pattern: the composition root
uses it to record the finished session (Milestone 2.5) without Automation
gaining a memory dependency — completion is the only moment worth recording,
and only this timer knows when it happens.
"""

import threading
from typing import Callable, Optional

from .notifications import ASSISTANT_NAME, notify


def start_pomodoro(
    minutes: int,
    speak: Callable[[str], None],
    on_complete: Optional[Callable[[int], None]] = None,
) -> str:
    def _done():
        msg = f"Pomodoro done! {minutes} minutes are up. Take a break."
        speak(msg)
        notify(msg, f"{ASSISTANT_NAME} — Pomodoro")
        if on_complete is not None:
            try:
                on_complete(minutes)
            except Exception as exc:
                # The timer thread must never die on a callback failure — the
                # session already completed and was announced.
                print(f"[pomodoro] on_complete failed: {exc}")

    threading.Timer(minutes * 60, _done).start()
    return f"Pomodoro started. I'll let you know in {minutes} minutes."
