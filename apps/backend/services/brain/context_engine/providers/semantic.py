"""Semantic memory provider — memory.recall(), relevance-gated (Milestone 2.3,
relocated unchanged into the provider pattern by 2.8).

The two-part relevance gate (absolute floor + relative margin from the top
hit) lives here because it is a *relevance* judgment about this source; the
token budget does not — budgeting is the engine's job, uniform across
providers. Each surviving item carries the full recall dict in
meta["memory"], which is how the exact-injected-memories list reaches the
reinforcement loop (reinforcement.py) after the reply exists.

Brain still touches Memory only through its public recall(); no vectors, no
tiers, no SQLite.
"""

from memory import recall

from ...config import (
    MEMORY_CONTEXT_TOKEN_BUDGET,
    MEMORY_MIN_SIMILARITY,
    MEMORY_RECALL_K,
    MEMORY_SIMILARITY_MARGIN,
    SEMANTIC_MEMORY_ENABLED,
)
from ..base import ContextItem, ContextProvider, ContextRequest


class SemanticContextProvider(ContextProvider):
    name = "semantic_memory"
    title = "Relevant Semantic Memories (long-term recall — use only if they fit the request)"
    budget = MEMORY_CONTEXT_TOKEN_BUDGET

    def collect(self, request: ContextRequest) -> list[ContextItem]:
        if not SEMANTIC_MEMORY_ENABLED or not request.query:
            return []
        candidates = recall(request.query, k=MEMORY_RECALL_K)
        if not candidates:
            return []

        # Relevance gate: absolute floor first, then a relative margin from the
        # best hit (recall returns score-ordered, so candidates[0] is the top).
        top_similarity = candidates[0].get("similarity", 0.0)
        cutoff = max(MEMORY_MIN_SIMILARITY, top_similarity - MEMORY_SIMILARITY_MARGIN)

        return [
            ContextItem(
                text=mem["text"],
                score=mem.get("score", 0.0),   # composite score → section order
                meta={"memory": mem},
            )
            for mem in candidates
            if mem.get("similarity", 0.0) >= cutoff
        ]
