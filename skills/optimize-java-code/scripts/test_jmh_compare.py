#!/usr/bin/env python3
"""Standalone tests for jmh_compare.py (stdlib only): python test_jmh_compare.py"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import jmh_compare


def row(
    name: str,
    score: float,
    error: object = 1.0,
    alloc: float | None = None,
    mode: str = "avgt",
    unit: str = "ns/op",
    params: dict | None = None,
) -> dict:
    item: dict = {
        "benchmark": f"example.Bench.{name}",
        "mode": mode,
        "threads": 1,
        "params": params,
        "primaryMetric": {"score": score, "scoreError": error, "scoreUnit": unit},
        "secondaryMetrics": {},
    }
    if alloc is not None:
        item["secondaryMetrics"]["gc.alloc.rate.norm"] = {
            "score": alloc,
            "scoreError": 0.0,
            "scoreUnit": "B/op",
        }
    return item


class JmhCompareTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name: str, rows: object) -> str:
        path = Path(self.tmp.name) / name
        path.write_text(json.dumps(rows), encoding="utf-8")
        return str(path)

    def run_main(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = jmh_compare.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def test_alloc_lower_pass_and_fail(self) -> None:
        f = self.write(
            "a.json", [row("base", 10, alloc=100.0), row("cand", 9, alloc=10.0)]
        )
        code, out, _ = self.run_main(f, "--alloc-lower", "base:cand")
        self.assertEqual(code, 0)
        self.assertIn("PASS alloc", out)
        code, out, _ = self.run_main(f, "--alloc-lower", "cand:base")
        self.assertEqual(code, 1)
        self.assertIn("FAIL alloc", out)

    def test_alloc_same_tolerates_harness_noise(self) -> None:
        f = self.write("a.json", [row("x", 1, alloc=0.015), row("y", 1, alloc=0.0001)])
        self.assertEqual(self.run_main(f, "--alloc-same", "x:y")[0], 0)

    def test_prefixed_secondary_key_is_accepted(self) -> None:
        item = row("x", 1)
        item["secondaryMetrics"]["·gc.alloc.rate.norm"] = {"score": 5.0}
        f = self.write("a.json", [item, row("y", 1, alloc=50.0)])
        self.assertEqual(self.run_main(f, "--alloc-lower", "y:x")[0], 0)

    def test_missing_alloc_is_invalid(self) -> None:
        f = self.write("a.json", [row("x", 1), row("y", 1)])
        code, _, err = self.run_main(f, "--alloc-lower", "x:y")
        self.assertEqual(code, 2)
        self.assertIn("-prof gc", err)

    def test_ambiguous_name_is_invalid(self) -> None:
        rows = [row("x", 1, params={"n": 1}), row("x", 2, params={"n": 2})]
        f = self.write("a.json", rows)
        self.assertEqual(self.run_main(f, "--alloc-lower", "x:x")[0], 2)

    def test_duplicate_rows_are_invalid(self) -> None:
        f = self.write("a.json", [row("x", 1), row("x", 2)])
        self.assertEqual(self.run_main(f)[0], 2)

    def test_two_file_regression_detection(self) -> None:
        base = self.write("b.json", [row("x", 100, error=1.0)])
        worse = self.write("c.json", [row("x", 120, error=1.0)])
        code, out, _ = self.run_main(base, worse, "--fail-regression", "5")
        self.assertEqual(code, 1)
        self.assertIn("worse", out)

    def test_two_file_nan_error_is_within_error(self) -> None:
        base = self.write("b.json", [row("x", 100, error="NaN")])
        cand = self.write("c.json", [row("x", 150, error="NaN")])
        code, out, _ = self.run_main(base, cand, "--fail-regression", "5")
        self.assertEqual(code, 0)
        self.assertIn("within error", out)

    def test_throughput_higher_is_better(self) -> None:
        base = self.write("b.json", [row("x", 100, 1.0, mode="thrpt", unit="ops/us")])
        cand = self.write("c.json", [row("x", 50, 1.0, mode="thrpt", unit="ops/us")])
        self.assertEqual(self.run_main(base, cand, "--fail-regression", "5")[0], 1)
        faster = self.write("d.json", [row("x", 200, 1.0, mode="thrpt", unit="ops/us")])
        self.assertEqual(self.run_main(base, faster, "--fail-regression", "5")[0], 0)

    def test_row_set_mismatch_is_invalid(self) -> None:
        base = self.write("b.json", [row("x", 1)])
        cand = self.write("c.json", [row("y", 1)])
        self.assertEqual(self.run_main(base, cand)[0], 2)

    def test_malformed_input_is_invalid(self) -> None:
        self.assertEqual(self.run_main(self.write("a.json", {"not": "a list"}))[0], 2)
        self.assertEqual(
            self.run_main(self.write("b.json", [{"benchmark": "x"}]))[0], 2
        )
        bad = Path(self.tmp.name) / "c.json"
        bad.write_text("{", encoding="utf-8")
        self.assertEqual(self.run_main(str(bad))[0], 2)

    def test_json_one_file_rows_and_checks(self) -> None:
        f = self.write(
            "a.json",
            [row("base", 10, error="NaN", alloc=100.0), row("cand", 9, alloc=10.0)],
        )
        code, out, _ = self.run_main(f, "--alloc-lower", "base:cand", "--json")
        report = json.loads(out)
        self.assertEqual(code, 0)
        self.assertEqual(len(report["rows"]), 2)
        self.assertIsNone(report["rows"][0]["error"])
        (check,) = report["checks"]
        self.assertEqual((check["check"], check["ok"]), ("alloc-lower", True))

    def test_json_two_files_marks_regressions(self) -> None:
        base = self.write("b.json", [row("x", 100, error=1.0)])
        worse = self.write("c.json", [row("x", 120, error=1.0)])
        code, out, _ = self.run_main(base, worse, "--fail-regression", "5", "--json")
        self.assertEqual(code, 1)
        (entry,) = json.loads(out)["comparisons"]
        self.assertEqual((entry["verdict"], entry["regression"]), ("worse", True))
        self.assertAlmostEqual(entry["ratio"], 1.2)

    def test_bad_pair_spec_and_margin(self) -> None:
        f = self.write("a.json", [row("x", 1, alloc=1.0)])
        self.assertEqual(self.run_main(f, "--alloc-lower", "x")[0], 2)
        self.assertEqual(self.run_main(f, "--margin", "1.5")[0], 2)


if __name__ == "__main__":
    unittest.main()
