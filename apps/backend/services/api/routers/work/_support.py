"""Shared helpers for WorkOS REST routes."""

from __future__ import annotations

from fastapi import HTTPException

from services.planner import work_commands as work_cmd


def work_error(exc: Exception) -> HTTPException:
    if isinstance(exc, work_cmd.WorkNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, work_cmd.WorkConflictError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, work_cmd.WorkValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))
