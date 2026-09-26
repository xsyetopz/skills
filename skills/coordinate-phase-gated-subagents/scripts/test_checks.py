"""Tests for check_work_items.py and check_gate.py (stdlib only)."""

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

import check_gate
import check_work_items as cwi


def item(name, owns, deps=(), phase="implementation"):
    return {"id": name, "phase": phase, "owns": list(owns), "depends_on": list(deps)}


def plan(*items):
    return {"phase": "implementation", "items": list(items)}


class WorkItemTests(unittest.TestCase):
    def test_waves_follow_dependencies(self) -> None:
        errors, waves = cwi.check(
            plan(
                item("a", ["src/a/"]),
                item("b", ["src/b/"]),
                item("c", ["src/c.py"], ["a", "b"]),
            )
        )
        self.assertEqual((errors, waves), ([], [["a", "b"], ["c"]]))

    def test_directory_contains_file_is_an_overlap(self) -> None:
        errors, _ = cwi.check(plan(item("a", ["src/"]), item("b", ["src/x.py"])))
        self.assertEqual(len(errors), 1)
        self.assertIn("can run in parallel", errors[0])

    def test_sibling_prefixes_do_not_overlap(self) -> None:
        errors, _ = cwi.check(plan(item("a", ["src/api/"]), item("b", ["src/api2/"])))
        self.assertEqual(errors, [])

    def test_dependent_items_may_share_paths(self) -> None:
        errors, _ = cwi.check(
            plan(item("a", ["src/x.py"]), item("b", ["src/x.py"], ["a"]))
        )
        self.assertEqual(errors, [])

    def test_transitive_dependency_orders_items(self) -> None:
        errors, _ = cwi.check(
            plan(item("a", ["f"]), item("b", ["g"], ["a"]), item("c", ["f"], ["b"]))
        )
        self.assertEqual(errors, [])

    def test_cycle_unknown_and_other_phase(self) -> None:
        errors, _ = cwi.check(plan(item("a", [], ["b"]), item("b", [], ["a"])))
        self.assertIn("dependency cycle", errors[0])
        errors, _ = cwi.check(plan(item("a", [], ["zzz"])))
        self.assertEqual(errors, ["a: unknown dependency 'zzz'"])
        errors, _ = cwi.check(plan(item("a", [], phase="release")))
        self.assertIn("not the current phase", errors[0])


def gate(conditions, requirements=()):
    return {"phase": "p", "conditions": conditions, "requirements": list(requirements)}


def condition(cid, status, required=True, command="make test"):
    evidence = {"status": status, "command": command} if status else None
    return {"id": cid, "required": required, "evidence": evidence}


class GateTests(unittest.TestCase):
    def test_all_passed_and_traced_closes(self) -> None:
        reasons = check_gate.evaluate(
            gate([condition("C1", "passed")], [{"id": "R1", "verified_by": ["C1"]}])
        )
        self.assertEqual(reasons, [])

    def test_each_non_pass_status_keeps_gate_open(self) -> None:
        for status in ("failed", "unavailable", "not_run"):
            with self.subTest(status=status):
                reasons = check_gate.evaluate(gate([condition("C1", status)]))
                self.assertEqual(reasons, [f"C1: {status}"])

    def test_missing_evidence_counts_as_not_run(self) -> None:
        self.assertEqual(
            check_gate.evaluate(gate([condition("C1", None)])), ["C1: not_run"]
        )

    def test_optional_failure_allowed_but_requirement_needs_a_pass(self) -> None:
        reasons = check_gate.evaluate(
            gate(
                [condition("C1", "passed"), condition("C2", "failed", required=False)],
                [{"id": "R2", "verified_by": ["C2"]}],
            )
        )
        self.assertEqual(reasons, ["R2: no passed verification"])

    def test_pass_without_command_is_suspicious(self) -> None:
        reasons = check_gate.evaluate(gate([condition("C1", "passed", command="")]))
        self.assertEqual(reasons, ["C1: passed without a recorded command"])

    def test_unknown_status_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            check_gate.evaluate(gate([condition("C1", "mostly")]))


def run_main(main, document: object, *flags: str) -> tuple[int, str, str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "input.json"
        path.write_text(json.dumps(document))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = main([str(path), *flags])
    return status, out.getvalue(), err.getvalue()


class CommandLineTests(unittest.TestCase):
    def test_gate_json_report(self) -> None:
        record = gate(
            [condition("C1", "failed")], [{"id": "R1", "verified_by": ["C1"]}]
        )
        status, out, _ = run_main(check_gate.main, record, "--json")
        self.assertEqual(status, 1)
        self.assertEqual(
            json.loads(out),
            {
                "phase": record.get("phase", "?"),
                "may_close": False,
                "reasons": ["C1: failed", "R1: no passed verification"],
            },
        )

    def test_gate_usage_and_malformed_input_return_2(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(check_gate.main([]), 2)
        status, _, err = run_main(check_gate.main, {"requirements": []})
        self.assertEqual(status, 2)
        self.assertIn("missing key 'conditions'", err)

    def test_work_items_missing_id_is_explained(self) -> None:
        status, _, err = run_main(cwi.main, {"phase": "p", "items": [{"phase": "p"}]})
        self.assertEqual(status, 2)
        self.assertIn("lacks the 'id' key", err)


if __name__ == "__main__":
    unittest.main()
