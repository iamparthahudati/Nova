"""Composition-root runtime — shared orchestration for voice, chat REPL, and API.

This package sits above services and below entry points (nova.py, api_server.py).
It owns the single conversation pipeline and lightweight event publishing for
WebSocket push; it does not own business rules (those live in services).
"""

from .conversation import process_message, process_transcript
from .events import publish, subscribe

__all__ = ["process_message", "process_transcript", "publish", "subscribe"]
