"""Shared WorkOS validation — pure, no I/O."""

from __future__ import annotations

from .errors import WorkValidationError


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
