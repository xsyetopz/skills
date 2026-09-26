"""Tests for python_function_metrics.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import python_function_metrics as pfm


def analyze(source: str) -> dict[str, pfm.FunctionMetrics]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text(textwrap.dedent(source), encoding="utf-8")
        return {m.name: m for m in pfm.analyze_file(path)}


class MetricsTests(unittest.TestCase):
    def test_elif_chain_is_one_level(self) -> None:
        metrics = analyze(
            """
            def band(x):
                if x < 1:
                    return "a"
                elif x < 2:
                    return "b"
                elif x < 3:
                    return "c"
                return "d"
            """
        )["band"]
        self.assertEqual(metrics.nesting, 1)
        self.assertEqual(metrics.ccn, 4)

    def test_nested_blocks_count_depth(self) -> None:
        metrics = analyze(
            """
            def deep(items):
                for item in items:
                    if item:
                        while item:
                            item -= 1
            """
        )["deep"]
        self.assertEqual(metrics.nesting, 3)
        self.assertEqual(metrics.ccn, 4)

    def test_nested_function_is_reported_separately(self) -> None:
        result = analyze(
            """
            def outer(a):
                def inner(b):
                    if b:
                        if b > 1:
                            return 2
                    return 0
                return inner(a)
            """
        )
        self.assertEqual(result["outer"].nesting, 0)
        self.assertEqual(result["inner"].nesting, 2)

    def test_self_is_not_a_parameter(self) -> None:
        result = analyze(
            """
            class C:
                def method(self, a, *rest, key=None, **extra):
                    return a
            """
        )
        self.assertEqual(result["method"].params, 4)

    def test_boolean_operands_and_comprehensions_add_decisions(self) -> None:
        metrics = analyze(
            """
            def f(a, b, c, rows):
                ok = a and b or c
                return [r for r in rows if r if ok]
            """
        )["f"]
        # 1 + (and: 1) + (or: 1) + (for: 1) + (two ifs: 2)
        self.assertEqual(metrics.ccn, 6)

    def test_limits_set_exit_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.py"
            path.write_text("def f(a, b, c, d, e):\n    return a\n")
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(pfm.main([str(path), "--max-params", "5"]), 0)
                self.assertEqual(pfm.main([str(path), "--max-params", "4"]), 1)

    def test_json_marks_exceeded_limits_and_limit_bounds_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.py"
            path.write_text("def f(a, b):\n    return a\n\n\ndef g(a):\n    return a\n")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = pfm.main(
                    [str(path), "--json", "--max-params", "1", "--limit", "1"]
                )
        self.assertEqual(status, 1)
        (row,) = json.loads(out.getvalue())
        self.assertEqual((row["name"], row["exceeded"]), ("f", ["params 2 > 1"]))
        self.assertIn("showing 1 of 2 functions", err.getvalue())

    def test_missing_path_is_input_error(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(pfm.main(["/nonexistent/path.py"]), 2)


if __name__ == "__main__":
    unittest.main()
