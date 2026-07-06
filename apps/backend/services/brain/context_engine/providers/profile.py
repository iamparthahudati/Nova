"""User-profile provider — the reflection job's observed patterns, rendered
exactly as Phase 1 did ("- [category] observation"). Dedup identity is the
observation text alone, so a semantic memory restating a profile fact
collapses into this structured copy.
"""

from memory import get_profile_observations

from ...config import PROFILE_CONTEXT_TOKEN_BUDGET
from ..base import ContextItem, ContextProvider, ContextRequest


class ProfileContextProvider(ContextProvider):
    name = "user_profile"
    title = "Profile (observed patterns)"
    budget = PROFILE_CONTEXT_TOKEN_BUDGET

    def collect(self, request: ContextRequest) -> list[ContextItem]:
        return [
            ContextItem(
                text=o["observation"],
                render=f"- [{o['category']}] {o['observation']}",
            )
            for o in get_profile_observations()
        ]
