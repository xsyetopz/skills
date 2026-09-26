"""Tests for zen_scan.py (stdlib only; run directly)."""

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

import zen_scan


def kinds(source: str) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "sample.py"
        path.write_text(textwrap.dedent(source))
        return [f.kind for f in zen_scan.scan(path)]


class ScanTests(unittest.TestCase):
    def test_silenced_except(self) -> None:
        source = "try:\n    f()\nexcept OSError:\n    pass\n"
        self.assertEqual(kinds(source), ["silenced-except"])

    def test_broad_except_without_reraise(self) -> None:
        source = "try:\n    f()\nexcept Exception:\n    log()\n"
        self.assertEqual(kinds(source), ["broad-except"])

    def test_broad_except_that_reraises_is_fine(self) -> None:
        source = "try:\n    f()\nexcept Exception:\n    log()\n    raise\n"
        self.assertEqual(kinds(source), [])

    def test_narrow_handled_except_is_fine(self) -> None:
        source = "try:\n    f()\nexcept KeyError as e:\n    raise ValueError from e\n"
        self.assertEqual(kinds(source), [])

    def test_wide_suppress(self) -> None:
        wide = "with suppress(OSError):\n    a()\n    b()\n"
        narrow = "with contextlib.suppress(OSError):\n    a()\n"
        self.assertEqual(kinds(wide), ["wide-suppress"])
        self.assertEqual(kinds(narrow), [])

    def test_or_default_on_parameter_only(self) -> None:
        source = """
            def f(value, default=3):
                local = compute()
                return (value or default), (local or 4)
        """
        self.assertEqual(kinds(source), ["or-default"])

    def test_star_import(self) -> None:
        self.assertEqual(kinds("from os.path import *\n"), ["star-import"])

    def test_fixture_counts_and_exit_status(self) -> None:
        skill = Path(__file__).resolve().parents[1]
        examples = skill / "assets/examples/zen-of-python/python"
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            before = zen_scan.main([str(examples / "zen_before.py")])
        self.assertEqual(before, 1)
        self.assertIn("5 finding(s)", out.getvalue())
        clean = [
            str(examples / name)
            for name in ("explicit_errors.py", "structure.py", "surface.py")
        ]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(zen_scan.main(clean), 0)

    def test_json_and_limit(self) -> None:
        skill = Path(__file__).resolve().parents[1]
        before = skill / "assets/examples/zen-of-python/python/zen_before.py"
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = zen_scan.main([str(before), "--json", "--limit", "2"])
        self.assertEqual(status, 1)
        rows = json.loads(out.getvalue())
        self.assertEqual(len(rows), 2)
        self.assertEqual(set(rows[0]), {"path", "line", "kind", "detail"})
        self.assertIn("showing 2 of 5 findings", err.getvalue())

    def test_unparsable_input(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.py"
            path.write_text("def (:\n")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(zen_scan.main([str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
