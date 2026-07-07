"""Input value objects that bundle commitment facets — keep service arity low."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .validation import Deadline, Estimate, validate_non_empty_name


@dataclass(frozen=True)
class TaskDraft:
    """The facets needed to record a task commitment (schema §6.3)."""

    project_id: int
    title: str
    estimate: Optional[Estimate] = None
    deadline: Optional[Deadline] = None
    source: str = "manual"

    def to_item_fields(self, owner_id: int) -> dict:
        """Flatten to a storage field dict for the WorkItem writer."""
        clean_title = validate_non_empty_name(self.title, "title")
        fields: dict = {
            "owner_id": owner_id,
            "project_id": self.project_id,
            "title": clean_title,
            "source": self.source,
        }
        if self.estimate is not None:
            fields["estimate_minutes"] = self.estimate.minutes
            fields["estimate_confidence"] = self.estimate.confidence
        if self.deadline is not None:
            fields["deadline_on"] = self.deadline.on
            fields["deadline_hardness"] = self.deadline.hardness
        return fields
