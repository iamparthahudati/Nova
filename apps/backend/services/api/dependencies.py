"""FastAPI dependencies — auth placeholder for future middleware."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Optional

from fastapi import Header


@dataclass(frozen=True)
class RequestContext:
    """Per-request context. Auth fields are placeholders for Milestone 2.12+."""

    client_id: str = "local"
    authenticated: bool = False
    user_id: Optional[str] = None


async def get_request_context(
    x_client_id: Annotated[Optional[str], Header()] = None,
) -> RequestContext:
    """Resolve request context. Replace with JWT/session validation later."""
    return RequestContext(
        client_id=x_client_id or "local",
        authenticated=False,
        user_id=None,
    )
