"""PriorityPolicyService — tunable weights for the deterministic queue."""

from __future__ import annotations

from typing import Optional

from ..aggregates import PriorityPolicy
from ..errors import WorkConflictError, WorkValidationError
from ..repositories import PriorityPolicyRepository
from ..repository_adapters import SqlitePriorityPolicyRepository

DEFAULT_OWNER_ID = 1


class PriorityPolicyService:
    def __init__(self, policies: Optional[PriorityPolicyRepository] = None) -> None:
        self._policies = policies or SqlitePriorityPolicyRepository()

    def get_active_policy(self, owner_id: int = DEFAULT_OWNER_ID) -> PriorityPolicy:
        policy = self._policies.get_active(owner_id)
        if policy is None:
            return self._policies.ensure_default(owner_id)
        return policy

    def reweight(
        self,
        deadline_weight: int,
        decay_weight: int,
        expected_updated_at: str,
        owner_id: int = DEFAULT_OWNER_ID,
    ) -> PriorityPolicy:
        if deadline_weight < 0 or decay_weight < 0:
            raise WorkValidationError("Priority weights must be non-negative")
        updated = self._policies.update_weights(
            {
                "owner_id": owner_id,
                "expected_updated_at": expected_updated_at,
                "deadline_weight": deadline_weight,
                "decay_weight": decay_weight,
            },
        )
        if updated is None:
            raise WorkConflictError("Priority policy was modified concurrently")
        return updated
