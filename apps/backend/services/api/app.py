"""FastAPI application factory for the Nova API facade."""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

import identity
import memory
from paths import REPO_ROOT
from runtime.events import publish
from services import brain, calendar
from services.api.errors import register_exception_handlers
from services.api.routers import calendar as calendar_router
from services.api.routers import (
    chat,
    finance,
    graph,
    health,
    home,
    memories,
)
from services.api.routers import memory as memory_router
from services.api.routers import (
    products,
    reminders,
    settings,
    spending,
    system,
    tasks,
)
from services.api.routers import work as work_router
from services.api.websocket import hub

load_dotenv(REPO_ROOT / ".env")

_initialized = False


def _ensure_runtime_ready() -> None:
    """One-time startup: DB, Brain DI, WebSocket hub."""
    global _initialized
    if _initialized:
        return
    memory.init_db()
    brain.set_calendar_source(calendar.get_events)
    hub.register()
    _initialized = True


def create_app() -> FastAPI:
    app = FastAPI(
        title=f"{identity.ASSISTANT_NAME} API",
        description="Thin facade over Nova backend services — no business logic here.",
        version="0.1.0",
    )

    register_exception_handlers(app)

    origins = os.environ.get("NOVA_API_CORS_ORIGINS", "http://localhost:5173").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(tasks.router)
    app.include_router(calendar_router.router)
    app.include_router(reminders.router)
    app.include_router(memory_router.router)
    app.include_router(memories.router)
    app.include_router(graph.router)
    app.include_router(spending.router)
    app.include_router(finance.router)
    app.include_router(work_router.router)
    app.include_router(products.router)
    app.include_router(settings.router)
    app.include_router(home.router)
    app.include_router(system.router)

    @app.on_event("startup")
    async def startup() -> None:
        _ensure_runtime_ready()
        hub.bind_loop(asyncio.get_running_loop())
        publish("events", "api.started", {"service": "nova-api"})

    @app.websocket("/ws/chat")
    async def ws_chat(websocket: WebSocket) -> None:
        await hub.connect("chat", websocket)

    @app.websocket("/ws/events")
    async def ws_events(websocket: WebSocket) -> None:
        await hub.connect("events", websocket)

    return app
