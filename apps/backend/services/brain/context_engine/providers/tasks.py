"""Open-tasks provider — the cheap, always-relevant flat query kept from
Phase 1 (v2 §2 explicitly preserves it: today's open tasks don't benefit from
semantic search). Highest dedup priority in the engine: an open task is the
authoritative copy of its own text, so a semantic memory echoing it yields.
"""

from memory import get_open_tasks

from ...config import TASKS_CONTEXT_TOKEN_BUDGET
from ..base import ContextItem, ContextProvider, ContextRequest


class TaskContextProvider(ContextProvider):
    name = "open_tasks"
    title = "Current Tasks"
    budget = TASKS_CONTEXT_TOKEN_BUDGET

    def collect(self, request: ContextRequest) -> list[ContextItem]:
        # score 0.0 for all: stable sort preserves Memory's row order exactly.
        return [ContextItem(text=t["text"]) for t in get_open_tasks()]
