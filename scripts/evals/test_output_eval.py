"""Tests for evals.json parsing, deterministic checks, grading, and benchmarks."""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import harness
import output_eval
from output_eval import Assertion


def write(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))
    return path


class LoadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "evals.json"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_string_and_check_assertions(self) -> None:
        write(
            self.path,
            {
                "skill_name": "demo",
                "evals": [
                    {
                        "id": 1,
                        "prompt": "do it",
                        "expected_output": "done",
                        "files": ["evals/files/data/in.csv"],
                        "assertions": [
                            "Says done.",
                            {"text": "out.txt exists", "check": "test -f out.txt"},
                        ],
                    },
                    {"id": "edge", "prompt": "p", "expected_output": ""},
                ],
            },
        )
        name, cases = output_eval.load_evals(self.path)
        self.assertEqual(name, "demo")
        self.assertEqual([c.id for c in cases], ["1", "edge"])
        self.assertEqual(
            cases[0].assertions,
            (Assertion("Says done."), Assertion("out.txt exists", "test -f out.txt")),
        )
        self.assertEqual(cases[1].assertions, ())
        self.assertFalse(cases[0].network)

    def test_network_opt_in(self) -> None:
        write(
            self.path,
            {
                "skill_name": "demo",
                "evals": [{"id": 1, "prompt": "p", "network": True}],
            },
        )
        self.assertTrue(output_eval.load_evals(self.path)[1][0].network)

    def test_invalid_evals(self) -> None:
        bad_cases = [
            {"id": 1, "prompt": ""},
            {"id": True, "prompt": "p"},
            {"id": 1, "prompt": "p", "files": "x"},
            {"id": 1, "prompt": "p", "assertions": [{"text": "t"}]},
            {
                "id": 1,
                "prompt": "p",
                "assertions": [{"text": "t", "check": "true", "grader": "x"}],
            },
            {"id": 1, "prompt": "p", "assertions": [7]},
            {"id": 1, "prompt": "p", "network": "yes"},
        ]
        for case in bad_cases:
            write(self.path, {"skill_name": "demo", "evals": [case]})
            with self.subTest(case=case), self.assertRaises(harness.UsageError):
                output_eval.load_evals(self.path)
        write(
            self.path,
            {
                "skill_name": "demo",
                "evals": [{"id": 1, "prompt": "p"}, {"id": "1", "prompt": "q"}],
            },
        )
        with self.assertRaises(harness.UsageError):
            output_eval.load_evals(self.path)

    def test_workspace_paths(self) -> None:
        self.assertEqual(
            output_eval.workspace_path("evals/files/data/in.csv"), Path("data/in.csv")
        )
        self.assertEqual(output_eval.workspace_path("assets/x.json"), Path("x.json"))
        for bad in ("/etc/passwd", "../x"):
            with self.assertRaises(harness.UsageError):
                output_eval.workspace_path(bad)


class GradingTests(unittest.TestCase):
    def test_check_runs_in_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "out.txt").write_text("ok")
            env = {**os.environ, "EVAL_RESPONSE_FILE": str(workspace / "out.txt")}
            passed = output_eval.run_check(
                Assertion("exists", "test -f out.txt"), workspace, env
            )
            failed = output_eval.run_check(
                Assertion("missing", 'grep -q nope "$EVAL_RESPONSE_FILE"'),
                workspace,
                env,
            )
        self.assertTrue(passed["passed"])
        self.assertFalse(failed["passed"])
        self.assertIn("exited 1", failed["evidence"])

    def test_grader_structured_output_and_empty_evidence(self) -> None:
        assertions = [Assertion("a"), Assertion("b")]
        result = {
            "type": "result",
            "structured_output": {
                "assertion_results": [
                    {
                        "text": "a",
                        "passed": True,
                        "evidence": "ran `just --fmt --check`",
                    },
                    {"text": "b", "passed": True, "evidence": " "},
                ]
            },
        }
        graded = output_eval.parse_grader([result], assertions)
        self.assertEqual([g["passed"] for g in graded], [True, False])
        self.assertEqual(graded[1]["evidence"], "no evidence given")

    def test_grader_json_in_text_and_count_mismatch(self) -> None:
        text = 'Here: {"assertion_results": [{"text": "a", "passed": false, "evidence": "not run"}]}'
        graded = output_eval.parse_grader(
            [{"type": "result", "result": text}], [Assertion("a")]
        )
        self.assertFalse(graded[0]["passed"])
        with self.assertRaises(ValueError):
            output_eval.parse_grader(
                [{"type": "result", "result": text}], [Assertion("a"), Assertion("b")]
            )

    def test_grading_document_summary(self) -> None:
        doc = output_eval.grading_document(
            [
                {"text": "a", "passed": True, "evidence": "x"},
                {"text": "b", "passed": False, "evidence": "y"},
            ]
        )
        self.assertEqual(
            doc["summary"], {"passed": 1, "failed": 1, "total": 2, "pass_rate": 0.5}
        )
        self.assertIsNone(output_eval.grading_document([])["summary"]["pass_rate"])

    def test_condensed_log(self) -> None:
        call = {
            "type": "assistant",
            "message": {
                "content": [
                    {
                        "type": "tool_use",
                        "name": "Bash",
                        "input": {"command": "just --fmt --check"},
                    }
                ]
            },
        }
        result = {
            "type": "user",
            "message": {
                "content": [
                    {
                        "type": "tool_result",
                        "content": [{"type": "text", "text": "ok"}],
                        "is_error": True,
                    }
                ]
            },
        }
        log = output_eval.condensed_log([call, result])
        self.assertIn('[tool Bash] {"command": "just --fmt --check"}', log)
        self.assertIn("[result (error)] ok", log)

    def test_changed_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "keep.txt").write_text("a")
            (root / "edit.txt").write_text("a")
            (root / ".claude" / "skills").mkdir(parents=True)
            before = output_eval.manifest(root)
            (root / "edit.txt").write_text("b")
            (root / "new" / "f.txt").parent.mkdir()
            (root / "new" / "f.txt").write_text("c")
            (root / ".claude" / "x").write_text("ignored")
            self.assertEqual(
                output_eval.changed_files(before, output_eval.manifest(root)),
                ["edit.txt", "new/f.txt"],
            )


class BenchmarkTests(unittest.TestCase):
    def test_aggregation_and_delta(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            iteration = Path(tmp)
            runs = {
                ("1", "with_skill"): (1.0, 40_000, 4000),
                ("2", "with_skill"): (0.5, 50_000, 3600),
                ("1", "without_skill"): (0.5, 30_000, 2000),
                ("2", "without_skill"): (0.0, 34_000, 2200),
            }
            for (case, config), (rate, ms, tokens) in runs.items():
                base = iteration / f"eval-{case}" / config
                write(base / "grading.json", {"summary": {"pass_rate": rate}})
                write(base / "timing.json", {"duration_ms": ms, "total_tokens": tokens})
            multi = iteration / "eval-3" / "with_skill" / "run-1"
            write(multi / "grading.json", {"summary": {"pass_rate": None}})
            write(multi / "timing.json", {"duration_ms": 60_000, "total_tokens": 5000})
            summary = output_eval.benchmark(iteration)["run_summary"]
        self.assertEqual(
            summary["with_skill"]["pass_rate"], {"mean": 0.75, "stddev": 0.3536}
        )
        self.assertEqual(summary["with_skill"]["runs"], 3)
        self.assertEqual(summary["with_skill"]["time_seconds"]["mean"], 50.0)
        self.assertEqual(
            summary["without_skill"]["pass_rate"], {"mean": 0.25, "stddev": 0.3536}
        )
        self.assertEqual(
            summary["delta"], {"pass_rate": 0.5, "time_seconds": 18.0, "tokens": 2100.0}
        )

    def test_single_run_stddev_is_zero(self) -> None:
        self.assertEqual(output_eval.stats([0.8]), {"mean": 0.8, "stddev": 0.0})
        self.assertIsNone(output_eval.stats([]))


if __name__ == "__main__":
    unittest.main()


class TextPreviewTests(unittest.TestCase):
    def test_binary_file_is_summarised(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pyc = Path(tmp) / "shipping.cpython-314.pyc"
            pyc.write_bytes(b"\xa7\r\r\n\x00\x00\x00\x00code")
            self.assertEqual(output_eval.text_preview(pyc), "<binary file, 12 bytes>")

    def test_text_file_is_truncated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            text = Path(tmp) / "a.py"
            text.write_text("x" * 5000, encoding="utf-8")
            self.assertEqual(len(output_eval.text_preview(text)), 4000)
