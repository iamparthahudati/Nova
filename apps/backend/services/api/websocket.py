"""WebSocket hub — subscribes to runtime.events.publish() and fans out."""

from __future__ import annotations

import asyncio
import json
from typing import Literal

from fastapi import WebSocket, WebSocketDisconnect
from runtime.events import subscribe

Channel = Literal["chat", "events"]


class WebSocketHub:
    """Manages /ws/chat and /ws/events connections."""

    def __init__(self) -> None:
        self._chat: set[WebSocket] = set()
        self._events: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    def register(self) -> None:
        """Subscribe to runtime event bus (called once at app startup)."""
        subscribe(self._on_publish)

    def _on_publish(self, channel: Channel, event_type: str, payload: dict) -> None:
        if self._loop is None or not self._loop.is_running():
            return
        message = json.dumps({"event": event_type, "data": payload})
        asyncio.run_coroutine_threadsafe(
            self._broadcast(channel, message),
            self._loop,
        )

    async def _broadcast(self, channel: Channel, message: str) -> None:
        clients = self._chat if channel == "chat" else self._events
        dead: set[WebSocket] = set()
        for ws in clients:
            try:
                await ws.send_text(message)
            except Exception:
                dead.add(ws)
        clients -= dead

    async def connect(self, channel: Channel, websocket: WebSocket) -> None:
        await websocket.accept()
        pool = self._chat if channel == "chat" else self._events
        pool.add(websocket)
        try:
            while True:
                # Keep connection alive; clients may send pings later.
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            pool.discard(websocket)


hub = WebSocketHub()
