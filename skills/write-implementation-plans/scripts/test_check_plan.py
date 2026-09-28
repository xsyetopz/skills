"""Tests for check_plan.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_plan as cp

GOOD = """\
- T1 [depends: -] [files: tests/test_a.py] [estimate: 1h] Pin behavior.
  Verify: `python3 -m unittest tests.test_a`
  Done when: new cases pass on the current code.
- T2 [depends: T1] [files: src/a.py] [estimate: 2h] Replace the counter.
  Verify: `python3 -m unittest tests.test_a`
  Done when: all cases pass.
- T3 [depends: T1] [files: bench.py] [estimate: 1d] Measure baseline.
  Verify: `python3 bench.py`
  Done when: baseline recorded.
"""


class PlanTests(unittest.TestCase):
    def test_good_plan_has_no_defects(self) -> None:
        defects, facts, commands = cp.analyze(cp.parse(GOOD))
        self.assertEqual(defects, [])
        self.assertIn("tasks=3", facts)
        self.assertIn("critical path: T1 -> T3 (9h)", facts)
        self.assertEqual(len(commands), 3)

    def test_forward_and_unknown_dependencies(self) -> None:
        text = GOOD.replace(
            "[depends: T1] [files: src/a.py]", "[depends: T3, T9] [files: src/a.py]"
        )
        defects = "\n".join(cp.analyze(cp.parse(text))[0])
        self.assertIn("T2: depends on later task T3", defects)
        self.assertIn("T2: depends on unknown T9", defects)

    def test_cycle_detected(self) -> None:
        text = GOOD.replace("[depends: -]", "[depends: T2]")
        defects = "\n".join(cp.analyze(cp.parse(text))[0])
        self.assertIn("cycle:", defects)

    def test_missing_parts_and_vague_verbs(self) -> None:
        text = "- T1 Refactor and clean up the module as needed.\n"
        defects = "\n".join(cp.analyze(cp.parse(text))[0])
        for expected in (
            "no [files:",
            "no Verify:",
            "no 'Done when:'",
            "vague verb 'refactor'",
            "vague verb 'clean up'",
            "vague verb 'as needed'",
        ):
            self.assertIn(expected, defects)

    def test_task_count_critical_path_without_estimates(self) -> None:
        text = GOOD.replace(" [estimate: 1h]", "")
        facts = cp.analyze(cp.parse(text))[1]
        self.assertIn("critical path: T1 -> T2 (2 tasks)", facts)

    def run_json(self, text: str) -> tuple[int, dict]:
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "PLAN.md"
            plan.write_text(text, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = cp.main(["--json", str(plan)])
        return status, json.loads(out.getvalue())

    def test_json_report_for_a_good_plan(self) -> None:
        status, report = self.run_json(GOOD)
        self.assertEqual(status, 0)
        self.assertEqual(report["tasks"], 3)
        self.assertEqual(
            report["critical_path"],
            {"tasks": ["T1", "T3"], "length": 9.0, "unit": "h"},
        )
        self.assertEqual(report["defects"], [])
        self.assertEqual(len(report["commands"]), 3)

    def test_json_report_lists_defects_by_task(self) -> None:
        status, report = self.run_json(GOOD.replace("[depends: -]", "[depends: T2]"))
        self.assertEqual(status, 1)
        self.assertIsNone(report["critical_path"])
        self.assertIn(
            {"task": "T1", "message": "depends on later task T2"}, report["defects"]
        )
        cycles = [d for d in report["defects"] if d["task"] is None]
        self.assertTrue(cycles and cycles[0]["message"].startswith("cycle: "))

    def test_unreadable_plan_is_input_error(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(cp.main(["/nonexistent/PLAN.md"]), 2)
        self.assertIn("cannot read plan", err.getvalue())


if __name__ == "__main__":
    unittest.main()
