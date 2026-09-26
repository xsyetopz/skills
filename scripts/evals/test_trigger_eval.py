"""Tests for trigger query loading, trigger-rate thresholds, and split summaries."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import harness
import trigger_eval
from trigger_eval import Query


def query(
    should: bool, split: str = "train", expected: str | None = None, index: int = 0
) -> Query:
    return Query("go", index, "q", should, split, expected)


class LoadTests(unittest.TestCase):
    def load(self, data: object) -> list[Query]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "eval_queries.json"
            path.write_text(json.dumps(data))
            return trigger_eval.load_queries("go", path)

    def test_valid_queries(self) -> None:
        loaded = self.load(
            [
                {"query": "fix mallocgc", "should_trigger": True, "split": "train"},
                {
                    "query": "rust",
                    "should_trigger": False,
                    "split": "validation",
                    "expected_skill": "rust",
                },
            ]
        )
        self.assertEqual([q.index for q in loaded], [0, 1])
        self.assertEqual(loaded[1].expected_skill, "rust")

    def test_invalid_queries(self) -> None:
        bad = [
            {"should_trigger": True, "split": "train"},
            {"query": "x", "should_trigger": "yes", "split": "train"},
            {"query": "x", "should_trigger": True, "split": "test"},
            {
                "query": "x",
                "should_trigger": True,
                "split": "train",
                "expected_skill": 3,
            },
        ]
        for item in bad:
            with self.subTest(item=item), self.assertRaises(harness.UsageError):
                self.load([item])
        with self.assertRaises(harness.UsageError):
            self.load({"query": "x"})

    def test_select_by_split_and_limit(self) -> None:
        queries = [
            query(True, "train", index=0),
            query(True, "validation", index=1),
            query(False, "train", index=2),
        ]
        self.assertEqual(
            [q.index for q in trigger_eval.select_queries(queries, "train", None)],
            [0, 2],
        )
        self.assertEqual(
            [q.index for q in trigger_eval.select_queries(queries, "all", 2)], [0, 1]
        )


class ScoreTests(unittest.TestCase):
    def test_should_trigger_threshold(self) -> None:
        scored = trigger_eval.score_query(query(True), ["go", "go", None], 0.5)
        self.assertAlmostEqual(scored["trigger_rate"], 0.6667)
        self.assertTrue(scored["passed"])
        self.assertFalse(
            trigger_eval.score_query(query(True), ["go", None, "rust"], 0.5)["passed"]
        )

    def test_threshold_boundary(self) -> None:
        self.assertFalse(trigger_eval.query_passed(True, 0.5, 0.5))
        self.assertFalse(trigger_eval.query_passed(False, 0.5, 0.5))
        self.assertTrue(trigger_eval.query_passed(True, 0.51, 0.5))
        self.assertTrue(trigger_eval.query_passed(False, 0.49, 0.5))

    def test_other_skills_and_expected_skill(self) -> None:
        scored = trigger_eval.score_query(
            query(False, expected="rust"), ["rust", "rust", "go"], 0.5
        )
        self.assertTrue(scored["passed"])
        self.assertEqual(scored["other_skills_fired"], {"rust": 2})
        self.assertAlmostEqual(scored["expected_skill_rate"], 0.6667)

    def test_summary_per_skill_and_split(self) -> None:
        results = [
            trigger_eval.score_query(query(True, "train"), ["go"], 0.5),
            trigger_eval.score_query(query(True, "validation"), [None], 0.5),
            trigger_eval.score_query(query(False, "validation"), [None], 0.5),
        ]
        summary = trigger_eval.summarize(results)
        self.assertEqual(summary["overall"]["passed"], 2)
        self.assertEqual(summary["per_split"]["train"]["pass_rate"], 1.0)
        self.assertEqual(summary["per_split"]["validation"]["pass_rate"], 0.5)
        go = summary["per_skill"]["go"]
        self.assertEqual(go["validation"]["should_trigger_passed"], 0)
        self.assertEqual(go["validation"]["should_not_trigger_passed"], 1)
        empty = trigger_eval.summarize(results[:1])["per_split"]["validation"]
        self.assertEqual(empty["queries"], 0)
        self.assertIsNone(empty["pass_rate"])


if __name__ == "__main__":
    unittest.main()
