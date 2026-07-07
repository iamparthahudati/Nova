"""Shared WorkOS validation — pure, no I/O."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from .errors import WorkValidationError
from .value_objects import (
    CaptureSource,
    DeadlineHardness,
    EstimateConfidence,
    ProjectStatus,
    WorkItemStatus,
)


def validate_non_empty_name(name: str, field: str = "name") -> str:
    cleaned = name.strip()
    if not cleaned:
        raise WorkValidationError(f"{field} is required")
    return cleaned


def validate_owner_id(owner_id: int | None) -> int | None:
    if owner_id is None:
        return None
    if owner_id <= 0:
        raise WorkValidationError("owner_id must be positive when set")
    return owner_id


def validate_capture_source(source: str) -> str:
    try:
        return CaptureSource(source).value
    except ValueError as exc:
        raise WorkValidationError(f"Invalid capture source: {source}") from exc


def validate_captured_on(captured_on: str, today: date) -> str:
    parsed = _parse_local_date(captured_on, "captured_on")
    if parsed > today + timedelta(days=1):
        raise WorkValidationError("captured_on cannot be more than one day in the future")
    return captured_on


def validate_project_status(status: str) -> str:
    try:
        return ProjectStatus(status).value
    except ValueError as exc:
        raise WorkValidationError(f"Invalid project status: {status}") from exc


def validate_project_dates(planned_start_on: Optional[str], planned_end_on: Optional[str]) -> None:
    if planned_start_on is not None:
        _parse_local_date(planned_start_on, "planned_start_on")
    if planned_end_on is not None:
        _parse_local_date(planned_end_on, "planned_end_on")
    if planned_start_on is not None and planned_end_on is not None:
        if planned_end_on < planned_start_on:
            raise WorkValidationError("planned_end_on must be on or after planned_start_on")


def validate_work_item_transition(to_status: str) -> str:
    try:
        return WorkItemStatus(to_status).value
    except ValueError as exc:
        raise WorkValidationError(f"Invalid work item status: {to_status}") from exc


def _parse_local_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise WorkValidationError(f"{field} must be a valid YYYY-MM-DD date") from exc


@dataclass(frozen=True)
class Estimate:
    """A commitment's effort facet — minutes never stand without confidence (WI3)."""

    minutes: int
    confidence: str

    @classmethod
    def create(cls, minutes: int, confidence: str) -> "Estimate":
        if minutes <= 0:
            raise WorkValidationError("estimate_minutes must be a positive integer")
        try:
            confidence_value = EstimateConfidence(confidence).value
        except ValueError as exc:
            raise WorkValidationError(f"Invalid estimate confidence: {confidence}") from exc
        return cls(minutes=minutes, confidence=confidence_value)


@dataclass(frozen=True)
class Deadline:
    """A commitment's time-pressure facet — a date never stands without hardness (WI4)."""

    on: str
    hardness: str

    @classmethod
    def create(cls, on: str, hardness: str) -> "Deadline":
        _parse_local_date(on, "deadline_on")
        try:
            hardness_value = DeadlineHardness(hardness).value
        except ValueError as exc:
            raise WorkValidationError(f"Invalid deadline hardness: {hardness}") from exc
        return cls(on=on, hardness=hardness_value)
