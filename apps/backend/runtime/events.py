"""Lightweight event bus for WebSocket push — services stay unaware.

Orchestration (runtime/conversation.py) calls publish(); the API WebSocket hub
registers as a subscriber on startup. No FastAPI imports here — keeps the
dependency arrow api → runtime, not the reverse.
"""

from __future__ import annotations

from typing import Callable, Literal

Channel = Literal["chat", "events"]
EventHandler = Callable[[Channel, str, dict], None]

_subscribers: list[EventHandler] = []


def subscribe(handler: EventHandler) -> None:
    """Register a callback invoked on every publish()."""
    _subscribers.append(handler)


def publish(channel: Channel, event_type: str, payload: dict | None = None) -> None:
    """Emit an event to all subscribers. Best-effort — never raises."""
    data = payload or {}
    for handler in list(_subscribers):
        try:
            handler(channel, event_type, data)
        except Exception:
            pass
