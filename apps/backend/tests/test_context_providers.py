"""Per-provider tests (Milestone 2.8) — every provider tested in isolation.

Memory verbs and the calendar source are patched at the provider module
boundary, so these tests never open nova.db or LanceDB and never run
AppleScript. That isolation is the milestone's "independently testable"
requirement, demonstrated.

Run:  .venv/bin/python -m unittest discover tests
"""

import unittest
from datetime import datetime
from unittest.mock import patch

from services.brain.context_engine.base import ContextRequest
from services.brain.context_engine.providers import (
    activity, calendar, conversation, graph, profile, semantic, tasks,
)

REQ = ContextRequest(query="what is priya working on", now=datetime(2026, 7, 5, 9, 30))


class TestSemanticProvider(unittest.TestCase):
    def _mem(self, text, similarity, score, id_="m1"):
        return {"id": id_, "text": text, "similarity": similarity, "score": score}

    def test_relevance_gate_floor_and_margin(self):
        candidates = [
            self._mem("on topic", 0.80, 0.9, "m1"),
            self._mem("near topic", 0.72, 0.8, "m2"),   # within margin (0.12) of 0.80
            self._mem("drifting", 0.60, 0.7, "m3"),     # below 0.80 - 0.12
            self._mem("noise", 0.40, 0.6, "m4"),        # below absolute floor
        ]
        with patch.object(semantic, "recall", return_value=candidates), \
             patch.object(semantic, "MEMORY_MIN_SIMILARITY", 0.55), \
             patch.object(semantic, "MEMORY_SIMILARITY_MARGIN", 0.12):
            items = semantic.SemanticContextProvider().collect(REQ)
        self.assertEqual([i.meta["memory"]["id"] for i in items], ["m1", "m2"])
        self.assertEqual(items[0].score, 0.9)   # composite score drives ranking

    def test_disabled_or_empty_query_yields_nothing(self):
        with patch.object(semantic, "SEMANTIC_MEMORY_ENABLED", False):
            self.assertEqual(semantic.SemanticContextProvider().collect(REQ), [])
        with patch.object(semantic, "recall") as recall:
            empty = ContextRequest(query="", now=REQ.now)
            self.assertEqual(semantic.SemanticContextProvider().collect(empty), [])
            recall.assert_not_called()


class TestGraphProvider(unittest.TestCase):
    ENTITIES = {
        "e1": {"id": "e1", "type": "person", "canonical_name": "Priya Sharma"},
        "e2": {"id": "e2", "type": "project", "canonical_name": "Aurora Rebrand"},
    }

    def test_renders_edges_of_matched_entities(self):
        def find(name, entity_type=None):
            return self.ENTITIES["e1"] if name.lower() == "priya" else None

        edges = [{"id": "ed1", "from_entity_id": "e1", "to_entity_id": "e2",
                  "relation_type": "WORKS_ON", "weight": 3.0}]
        with patch.object(graph, "find_entity", side_effect=find), \
             patch.object(graph, "entity_edges", return_value=edges), \
             patch.object(graph, "get_entity", side_effect=lambda i: self.ENTITIES.get(i)):
            items = graph.GraphContextProvider().collect(REQ)
        self.assertEqual(len(items), 1)
        self.assertEqual(
            items[0].text,
            "Priya Sharma (person) —WORKS_ON→ Aurora Rebrand (project)",
        )
        self.assertEqual(items[0].score, 3.0)   # edge weight = evidence

    def test_shared_edge_between_two_matched_entities_appears_once(self):
        def find(name, entity_type=None):
            key = name.lower()
            if key == "priya":
                return self.ENTITIES["e1"]
            if key == "aurora":
                return self.ENTITIES["e2"]
            return None

        edge = {"id": "ed1", "from_entity_id": "e1", "to_entity_id": "e2",
                "relation_type": "WORKS_ON", "weight": 1.0}
        req = ContextRequest(query="is priya still on aurora", now=REQ.now)
        with patch.object(graph, "find_entity", side_effect=find), \
             patch.object(graph, "entity_edges", return_value=[edge]), \
             patch.object(graph, "get_entity", side_effect=lambda i: self.ENTITIES.get(i)):
            items = graph.GraphContextProvider().collect(req)
        self.assertEqual(len(items), 1)

    def test_disabled_returns_nothing_without_lookups(self):
        with patch.object(graph, "GRAPH_CONTEXT_ENABLED", False), \
             patch.object(graph, "find_entity") as find:
            self.assertEqual(graph.GraphContextProvider().collect(REQ), [])
            find.assert_not_called()

    def test_ngram_generation_longest_first(self):
        phrases = graph._candidate_phrases("Aurora Rebrand kickoff")
        self.assertEqual(phrases[0], "Aurora Rebrand kickoff")   # 3-gram first
        self.assertIn("Aurora Rebrand", phrases)
        self.assertNotIn("a", phrases)                            # short 1-grams dropped


class TestTaskAndProfileProviders(unittest.TestCase):
    def test_tasks_preserve_row_order(self):
        rows = [{"text": "ship the app"}, {"text": "call the bank"}]
        with patch.object(tasks, "get_open_tasks", return_value=rows):
            items = tasks.TaskContextProvider().collect(REQ)
        self.assertEqual([i.display for i in items], ["- ship the app", "- call the bank"])

    def test_profile_renders_category_prefix(self):
        rows = [{"category": "habits", "observation": "codes late at night"}]
        with patch.object(profile, "get_profile_observations", return_value=rows):
            items = profile.ProfileContextProvider().collect(REQ)
        self.assertEqual(items[0].display, "- [habits] codes late at night")
        self.assertEqual(items[0].text, "codes late at night")   # dedup on the fact


class TestActivityProvider(unittest.TestCase):
    def test_three_groups_same_rendering_as_phase1(self):
        with patch.object(activity, "get_recent_progress",
                          return_value=[{"note": "shipped v2"}]), \
             patch.object(activity, "get_recent_money",
                          return_value=[{"type": "expense", "amount": 40.0, "note": "coffee"}]), \
             patch.object(activity, "get_products",
                          return_value=[{"name": "Nova", "status": "live", "store": "",
                                         "price": None, "sold_count": 3}]):
            items = activity.RecentActivityProvider().collect(REQ)
        self.assertEqual(
            [(i.meta["group"], i.display) for i in items],
            [("Recent progress", "- shipped v2"),
             ("Recent money entries", "- expense 40.0 (coffee)"),
             ("Products", "- Nova [live] sales:3")],
        )


class TestCalendarProvider(unittest.TestCase):
    def tearDown(self):
        calendar.set_calendar_source(None)

    def test_unwired_contributes_nothing(self):
        calendar.set_calendar_source(None)
        self.assertEqual(calendar.CalendarContextProvider().collect(REQ), [])

    def test_wired_source_renders_and_caches(self):
        calls = []

        def fetch(day=None):
            calls.append(day)
            return [{"title": "Standup", "time": "9:00 AM"}]

        calendar.set_calendar_source(fetch)
        provider = calendar.CalendarContextProvider()
        first = provider.collect(REQ)
        second = provider.collect(REQ)
        self.assertEqual(first[0].display, "- 9:00 AM — Standup")
        self.assertEqual(len(calls), 1)   # second collect served from TTL cache
        self.assertEqual([i.text for i in second], [i.text for i in first])

    def test_disabled_never_calls_source(self):
        calls = []
        calendar.set_calendar_source(lambda day=None: calls.append(day) or [])
        with patch.object(calendar, "CALENDAR_CONTEXT_ENABLED", False):
            self.assertEqual(calendar.CalendarContextProvider().collect(REQ), [])
        self.assertEqual(calls, [])


class TestConversationProvider(unittest.TestCase):
    def test_trims_to_last_four_pairs(self):
        history = tuple(
            {"role": role, "content": f"turn {i}"}
            for i in range(6) for role in ("user", "assistant")
        )
        req = ContextRequest(query="q", history=history, now=REQ.now)
        messages = conversation.RecentConversationProvider().collect(req)
        self.assertEqual(len(messages), 8)                    # 4 pairs
        self.assertEqual(messages[-1], history[-1])           # newest kept


if __name__ == "__main__":
    unittest.main()
