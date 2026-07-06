"""Pure domain mutation record — producer-agnostic."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MutationEvent:
    """One successful business mutation.

    Must not contain chat, REST, or producer-specific fields.
    """

    event_type: str
    entity_type: str
    operation: str
    entity: dict
    metadata: dict = field(default_factory=dict)
