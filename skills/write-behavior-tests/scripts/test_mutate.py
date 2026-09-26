"""Tests for mutate.py (stdlib only; run directly)."""

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

import mutate

CLAMP = """
def clamp(x, lo, hi):
    if x < lo:
        return lo
    if x > hi:
        return hi
    return x
"""

PERCENT = """
def accept(value):
    return 1 <= value <= 100
"""


def project(source: str, tests: str) -> Path:
    root = Path(tempfile.mkdtemp())
    (root / "calc.py").write_text(textwrap.dedent(source))
    (root / "test_calc.py").write_text(textwrap.dedent(tests))
    return root


def run(root: Path, *extra: str) -> tuple[int, list[dict]]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        status = mutate.main(
            [
                str(root / "calc.py"),
                "--root",
                str(root),
                "--test",
                f"{sys.executable} -m unittest -q",
                "--json",
                *extra,
            ]
        )
    text = out.getvalue()
    return status, json.loads(text) if text.strip() else []


class MutateTests(unittest.TestCase):
    def test_equivalent_boundary_mutants_survive_clamp(self) -> None:
        tests = """
            import unittest
            from calc import clamp
            class T(unittest.TestCase):
                def test_cases(self):
                    for x, want in [(5, 5), (-3, 0), (30, 10), (0, 0), (10, 10)]:
                        self.assertEqual(clamp(x, 0, 10), want)
        """
        status, mutants = run(project(CLAMP, tests))
        self.assertEqual(status, 1)
        survived = [m["change"] for m in mutants if m["status"] == "survived"]
        self.assertEqual(survived, ["Lt -> LtE", "Gt -> GtE"])

    def test_boundary_tests_kill_every_chained_compare_mutant(self) -> None:
        tests = """
            import unittest
            from calc import accept
            class T(unittest.TestCase):
                def test_bounds(self):
                    for v, ok in [(0, False), (1, True), (100, True), (101, False)]:
                        self.assertIs(accept(v), ok)
        """
        status, mutants = run(project(PERCENT, tests))
        self.assertEqual(status, 0)
        self.assertEqual(len(mutants), 5)
        self.assertTrue(all(m["status"] == "killed" for m in mutants))

    def test_middle_only_tests_leave_boundary_mutants(self) -> None:
        tests = """
            import unittest
            from calc import accept
            class T(unittest.TestCase):
                def test_middle(self):
                    self.assertTrue(accept(50))
                    self.assertFalse(accept(500))
        """
        status, mutants = run(project(PERCENT, tests))
        self.assertEqual(status, 1)
        survived = {m["change"] for m in mutants if m["status"] == "survived"}
        self.assertIn("LtE -> Lt", survived)
        self.assertIn("1 -> 2", survived)

    def test_function_filter_limits_sites(self) -> None:
        source = CLAMP + "\n\ndef other():\n    return 1 + 2\n"
        tests = """
            import unittest
            class T(unittest.TestCase):
                def test_nothing(self):
                    pass
        """
        status, mutants = run(project(source, tests), "--function", "other")
        self.assertEqual({m["line"] for m in mutants}, {11})
        self.assertEqual(status, 1)

    def test_list_is_a_dry_run(self) -> None:
        root = project(CLAMP, "raise SystemExit('tests must not run')\n")
        before = (root / "calc.py").read_text()
        status, mutants = run(root, "--list")
        self.assertEqual(status, 0)
        self.assertGreater(len(mutants), 0)
        self.assertEqual({m["status"] for m in mutants}, {"pending"})
        self.assertEqual((root / "calc.py").read_text(), before)

    def test_missing_test_command_is_input_error(self) -> None:
        root = project(CLAMP, "")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            status = mutate.main(
                [str(root / "calc.py"), "--root", str(root), "--test", "no-such-cmd-x"]
            )
        self.assertEqual(status, 2)
        self.assertIn("cannot run --test", err.getvalue())

    def test_failing_baseline_is_refused(self) -> None:
        tests = """
            import unittest
            class T(unittest.TestCase):
                def test_broken(self):
                    self.fail("baseline")
        """
        status, _ = run(project(CLAMP, tests))
        self.assertEqual(status, 2)


if __name__ == "__main__":
    unittest.main()
