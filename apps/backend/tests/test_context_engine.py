"""Context Engine pipeline tests (Milestone 2.8) — stub providers only.

These tests exercise the orchestration guarantees (merge, dedup, ranking,
budgets, deterministic ordering, graceful degradation) with in-memory stub
providers. No database, no LanceDB, no network — the engine never knows the
difference, which is itself the property under test.

Run:  .venv/bin/python -m unittest discover tests
"""

import unittest
from datetime import datetime

from services.brain.context_engine.base import ContextItem, ContextProvider, MessagesProvider
from services.brain.context_engine.engine import ContextEngine

NOW = datetime(2026, 7, 5, 9, 30)


class StubProvider(ContextProvider):
    def __init__(self, name, items, title=None, budget=400, omit_when_empty=False):
        self.name = name
        self.title = title or name
        self.items = items
        self.budget = budget
        self.omit_when_empty = omit_when_empty

    def collect(self, request):
        if isinstance(self.items, Exception):
            raise self.items
        return list(self.items)


class StubConversation(MessagesProvider):
    name = "recent_conversation"

    def __init__(self, messages=None, fail=False):
        self.messages = messages or []
        self.fail = fail

    def collect(self, request):
        if self.fail:
            raise RuntimeError("boom")
        return list(self.messages)


def build(providers, **kw):
    return ContextEngine(providers=providers, **kw)


class TestPipeline(unittest.TestCase):
    def test_merges_providers_into_ordered_sections(self):
        engine = build(
            [
                StubProvider("a", [ContextItem(text="alpha")], title="A"),
                StubProvider("b", [ContextItem(text="beta")], title="B"),
            ]
        )
        ctx = engine.assemble("q", now=NOW)
        self.assertIn("A:\n- alpha", ctx.system)
        self.assertIn("B:\n- beta", ctx.system)
        self.assertLess(ctx.system.index("A:"), ctx.system.index("B:"))
        self.assertEqual([s.name for s in ctx.sections], ["a", "b"])

    def test_deduplicates_across_providers_by_priority(self):
        # same fact from a structured source and a semantic echo — the
        # structured copy must win regardless of provider list order.
        engine = build(
            [
                StubProvider(
                    "semantic_memory",
                    [ContextItem(text="Ship  the App", meta={"memory": {"id": "m1"}})],
                ),
                StubProvider("open_tasks", [ContextItem(text="ship the app")]),
            ],
            dedup_order=("open_tasks", "semantic_memory"),
        )
        ctx = engine.assemble("q", now=NOW)
        by_name = {s.name: s for s in ctx.sections}
        self.assertEqual(len(by_name["open_tasks"].items), 1)
        self.assertEqual(len(by_name["semantic_memory"].items), 0)
        self.assertEqual(ctx.memories, [])  # dropped echo earns no reinforcement

    def test_ranks_by_score_stable_on_ties(self):
        engine = build(
            [
                StubProvider(
                    "s",
                    [
                        ContextItem(text="low", score=0.1),
                        ContextItem(text="tie one", score=0.5),
                        ContextItem(text="tie two", score=0.5),
                        ContextItem(text="high", score=0.9),
                    ],
                )
            ]
        )
        ctx = engine.assemble("q", now=NOW)
        texts = [i.text for i in ctx.sections[0].items]
        self.assertEqual(texts, ["high", "tie one", "tie two", "low"])

    def test_section_budget_truncates_but_keeps_first_item(self):
        big = ContextItem(text="x" * 400)  # ~100 tokens alone
        engine = build([StubProvider("s", [big, ContextItem(text="second")], budget=10)])
        ctx = engine.assemble("q", now=NOW)
        self.assertEqual(len(ctx.sections[0].items), 1)  # oversize first item survives
        self.assertEqual(ctx.sections[0].items[0].text, big.text)

    def test_global_budget_trims_in_trim_order(self):
        engine = build(
            [
                StubProvider("open_tasks", [ContextItem(text="t" * 200)]),
                StubProvider(
                    "knowledge_graph", [ContextItem(text="g" * 200)], omit_when_empty=True
                ),
            ],
            total_budget=60,
            trim_order=("knowledge_graph", "open_tasks"),
        )
        ctx = engine.assemble("q", now=NOW)
        by_name = {s.name: s for s in ctx.sections}
        self.assertEqual(len(by_name["knowledge_graph"].items), 0)  # trimmed first
        self.assertEqual(len(by_name["open_tasks"].items), 1)  # core state kept

    def test_provider_failure_degrades_to_empty_section(self):
        engine = build(
            [
                StubProvider("broken", RuntimeError("source down"), title="Broken"),
                StubProvider("fine", [ContextItem(text="still here")], title="Fine"),
            ]
        )
        ctx = engine.assemble("q", now=NOW)
        self.assertIn("still here", ctx.system)
        self.assertIn("broken", ctx.failures)
        self.assertIn("Broken:\nNone", ctx.system)  # degraded, not vanished

    def test_deterministic_output(self):
        def providers():
            return [
                StubProvider(
                    "a",
                    [ContextItem(text="one", score=0.3), ContextItem(text="two", score=0.7)],
                ),
                StubProvider("b", [ContextItem(text="three")]),
            ]

        first = build(providers()).assemble("same query", now=NOW).system
        second = build(providers()).assemble("same query", now=NOW).system
        self.assertEqual(first, second)

    def test_omit_when_empty_sections_disappear(self):
        engine = build(
            [
                StubProvider("calendar", [], title="Today's Calendar", omit_when_empty=True),
                StubProvider("open_tasks", [], title="Current Tasks"),
            ]
        )
        ctx = engine.assemble("q", now=NOW)
        self.assertNotIn("Today's Calendar", ctx.system)
        self.assertIn("Current Tasks:\nNone", ctx.system)

    def test_semantic_memories_surface_for_reinforcement(self):
        mem = {"id": "m1", "text": "user prefers dark roast"}
        engine = build(
            [
                StubProvider(
                    "semantic_memory",
                    [ContextItem(text=mem["text"], meta={"memory": mem})],
                )
            ]
        )
        ctx = engine.assemble("q", now=NOW)
        self.assertEqual(ctx.memories, [mem])

    def test_messages_channel_and_fallback(self):
        history = [{"role": "user", "content": "hi"}] * 12
        trimmed = history[-4:]
        ok = build([], conversation=StubConversation(trimmed))
        self.assertEqual(ok.assemble("q", history=history, now=NOW).messages, trimmed)

        failing = build([], conversation=StubConversation(fail=True))
        ctx = failing.assemble("q", history=history, now=NOW)
        self.assertEqual(len(ctx.messages), 12)  # raw history fallback
        self.assertIn("recent_conversation", ctx.failures)

    def test_grouped_section_renders_titled_subblocks(self):
        engine = build(
            [
                StubProvider(
                    "recent_activity",
                    [
                        ContextItem(text="shipped v2", meta={"group": "Recent progress"}),
                        ContextItem(
                            text="expense 40.0 (coffee)", meta={"group": "Recent money entries"}
                        ),
                    ],
                    title="Recent Context",
                )
            ]
        )
        ctx = engine.assemble("q", now=NOW)
        self.assertIn(
            "Recent Context:\nRecent progress:\n- shipped v2\n\n"
            "Recent money entries:\n- expense 40.0 (coffee)",
            ctx.system,
        )


class TestPromptFrame(unittest.TestCase):
    def test_header_and_footer_preserved(self):
        ctx = build([]).assemble("q", now=NOW)
        self.assertIn(f"Today is {NOW.strftime('%A, %B %d, %Y')}.", ctx.system)
        self.assertIn("The current time is 9:30 AM.", ctx.system)
        self.assertIn("Never ask the user for the current date or time.", ctx.system)
        self.assertIn("Keep replies short and natural", ctx.system)


if __name__ == "__main__":
    unittest.main()
