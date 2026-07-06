"""The Context Engine — one orchestration pipeline for everything Claude sees.

Milestone 2.8. Every context source (semantic memory, knowledge graph, open
tasks, calendar, profile, recent activity, recent conversation) is a provider;
this engine is the only place their outputs meet. The pipeline, in order:

    collect     each provider runs inside its own try/except — a failing
                provider becomes an empty section and a recorded failure,
                never a broken turn (graceful degradation)
    dedup       one fact appears once, however many providers surfaced it;
                DEDUP_ORDER decides who owns a duplicated fact (structured
                sources outrank semantic echoes of themselves)
    rank        items sort by score within their section (stable, so equal
                scores keep provider order — determinism over cleverness)
    budget      per-section token ceilings, filled in score order, at least
                one item always survives; then a global ceiling trimmed in
                TRIM_ORDER (most speculative context gives way first)
    format      prompts.format_system_prompt renders the surviving sections —
                formatting is prompts.py's whole remaining job

Recent conversation is a provider too, but it feeds the `messages` channel,
not the system string — history threaded as messages is how Claude actually
consumes dialogue, and duplicating it into the system prompt would pay for it
twice. The engine owns its trimming policy.

Determinism: providers run in a fixed order, every sort is stable, every
tie-break is provider order, and the clock enters only through the request —
the same request against the same stores yields the same prompt, byte for byte.
"""

from datetime import datetime
from typing import Optional, Sequence

from ..prompts import format_system_prompt
from .base import (
    AssembledContext,
    ContextItem,
    ContextProvider,
    ContextRequest,
    MessagesProvider,
    Section,
    estimate_tokens,
)

# Who owns a fact that several providers surfaced. Structured, authoritative
# sources come first; semantic memory last, because its rows are frequently
# *derived from* the structured ones (a remembered task echoes the task row).
DEDUP_ORDER = (
    "open_tasks",
    "calendar",
    "recent_activity",
    "user_profile",
    "knowledge_graph",
    "semantic_memory",
)

# What gives way first when the whole prompt overruns the global budget:
# speculative enrichment before core state; open tasks are trimmed dead last.
TRIM_ORDER = (
    "knowledge_graph",
    "recent_activity",
    "user_profile",
    "semantic_memory",
    "calendar",
    "open_tasks",
)


class ContextEngine:
    """Orchestrates providers into one AssembledContext per turn."""

    def __init__(
        self,
        providers: Sequence[ContextProvider],
        conversation: Optional[MessagesProvider] = None,
        total_budget: int = 0,
        dedup_order: Sequence[str] = DEDUP_ORDER,
        trim_order: Sequence[str] = TRIM_ORDER,
    ) -> None:
        self.providers = list(providers)  # list order == render order
        self.conversation = conversation  # messages channel, not a section
        self.total_budget = total_budget  # 0 = no global ceiling
        self.dedup_order = list(dedup_order)
        self.trim_order = list(trim_order)

    # ── pipeline steps ────────────────────────────────────────────────────────

    def _collect(self, request: ContextRequest) -> tuple[dict[str, list[ContextItem]], list[str]]:
        collected: dict[str, list[ContextItem]] = {}
        failures: list[str] = []
        for provider in self.providers:
            try:
                collected[provider.name] = list(provider.collect(request))
            except Exception as exc:  # isolate: one bad source ≠ a bad turn
                print(f"[context-engine] {provider.name} failed, section omitted: {exc}")
                collected[provider.name] = []
                failures.append(provider.name)
        return collected, failures

    def _dedup(self, collected: dict[str, list[ContextItem]]) -> None:
        seen: set[str] = set()
        order = [n for n in self.dedup_order if n in collected] + [
            n for n in collected if n not in self.dedup_order
        ]
        for name in order:
            kept = []
            for item in collected[name]:
                if item.key in seen:
                    continue
                seen.add(item.key)
                kept.append(item)
            collected[name] = kept

    def _budget_section(
        self, provider: ContextProvider, items: list[ContextItem]
    ) -> list[ContextItem]:
        ordered = sorted(items, key=lambda i: -i.score)  # stable: ties keep order
        kept: list[ContextItem] = []
        used = 0
        for item in ordered:
            cost = estimate_tokens(item.display)
            if kept and used + cost > provider.budget:
                break
            kept.append(item)
            used += cost
        return kept

    def _trim_to_total(self, sections: list[Section]) -> None:
        if not self.total_budget:
            return

        def total() -> int:
            return sum(
                estimate_tokens(s.title) + estimate_tokens(s.rendered())
                for s in sections
                if s.include
            )

        by_name = {s.name: s for s in sections}
        for name in self.trim_order:
            section = by_name.get(name)
            if section is None:
                continue
            while section.items and total() > self.total_budget:
                section.items.pop()  # cheapest-signal tail first
            if total() <= self.total_budget:
                return

    # ── entry point ───────────────────────────────────────────────────────────

    def assemble(
        self,
        query: Optional[str] = None,
        history: Optional[list[dict]] = None,
        now: Optional[datetime] = None,
    ) -> AssembledContext:
        request = ContextRequest(
            query=(query or "").strip(),
            history=tuple(history or ()),
            now=now or datetime.now(),
        )

        collected, failures = self._collect(request)
        self._dedup(collected)

        sections = [
            Section(
                name=p.name,
                title=p.title,
                items=self._budget_section(p, collected[p.name]),
                omit_when_empty=p.omit_when_empty,
            )
            for p in self.providers
        ]
        self._trim_to_total(sections)

        # Messages channel: trimmed history, degrading to the raw history —
        # the one provider whose failure mode must not drop the conversation.
        messages = list(request.history)
        if self.conversation is not None:
            try:
                messages = [dict(m) for m in self.conversation.collect(request)]
            except Exception as exc:
                print(f"[context-engine] conversation trim failed, using raw history: {exc}")
                failures.append(self.conversation.name)

        memories = [
            item.meta["memory"]
            for section in sections
            if section.name == "semantic_memory"
            for item in section.items
            if "memory" in item.meta
        ]

        return AssembledContext(
            system=format_system_prompt(sections, request.now or datetime.now()),
            memories=memories,
            messages=messages,
            sections=sections,
            failures=failures,
        )
