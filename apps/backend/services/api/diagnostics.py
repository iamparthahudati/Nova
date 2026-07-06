"""Runtime health and subsystem diagnostics for GET /system/status."""

from __future__ import annotations

import sqlite3

import memory
from services.brain import config as brain_config

from .schemas import SubsystemDiagnostic, SystemStatusResponse
from .schemas.system import SubsystemStatus


def build_system_status(version: str = "0.1.0") -> SystemStatusResponse:
    subsystems: list[SubsystemDiagnostic] = []

    subsystems.append(_check_database())
    subsystems.append(_check_semantic_memory())
    subsystems.append(_check_graph())
    subsystems.append(_check_brain())
    subsystems.append(_check_calendar())

    overall: SubsystemStatus = "ok"
    if any(s.status == "unavailable" for s in subsystems):
        overall = "unavailable"
    elif any(s.status == "degraded" for s in subsystems):
        overall = "degraded"

    return SystemStatusResponse(status=overall, version=version, subsystems=subsystems)


def _check_database() -> SubsystemDiagnostic:
    try:
        memory.ping_database()
        return SubsystemDiagnostic(name="database", status="ok", message="SQLite reachable")
    except (sqlite3.Error, OSError) as exc:
        return SubsystemDiagnostic(
            name="database",
            status="unavailable",
            message=str(exc),
        )


def _check_semantic_memory() -> SubsystemDiagnostic:
    if not brain_config.SEMANTIC_MEMORY_ENABLED:
        return SubsystemDiagnostic(
            name="semantic_memory",
            status="degraded",
            message="Semantic memory disabled via NOVA_SEMANTIC_MEMORY",
        )
    if not memory.semantic_index_exists():
        return SubsystemDiagnostic(
            name="semantic_memory",
            status="degraded",
            message="LanceDB index not yet created",
        )
    try:
        count = memory.count_active_memories()
        return SubsystemDiagnostic(
            name="semantic_memory",
            status="ok",
            message=f"{count} active memories indexed",
        )
    except Exception as exc:
        return SubsystemDiagnostic(
            name="semantic_memory",
            status="degraded",
            message=str(exc),
        )


def _check_graph() -> SubsystemDiagnostic:
    try:
        stats = memory.graph_stats()
        return SubsystemDiagnostic(
            name="graph",
            status="ok",
            message=f"{stats['entity_count']} entities, {stats['edge_count']} edges",
        )
    except Exception as exc:
        return SubsystemDiagnostic(
            name="graph",
            status="degraded",
            message=str(exc),
        )


def _check_brain() -> SubsystemDiagnostic:
    if not brain_config.CLAUDE_API_KEY:
        return SubsystemDiagnostic(
            name="brain",
            status="degraded",
            message="NOVA_CLAUDE_API_KEY not configured",
        )
    return SubsystemDiagnostic(
        name="brain",
        status="ok",
        message=f"Model {brain_config.CLAUDE_MODEL}",
    )


def _check_calendar() -> SubsystemDiagnostic:
    try:
        from datetime import datetime

        from services import calendar

        calendar.get_events(datetime.now())
        return SubsystemDiagnostic(name="calendar", status="ok", message="Calendar accessible")
    except Exception as exc:
        return SubsystemDiagnostic(
            name="calendar",
            status="degraded",
            message=str(exc) or "Calendar unavailable",
        )
