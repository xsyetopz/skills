"""Tests for find_compat_python.py (stdlib only; run directly)."""

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

import find_compat_python as fcp

SOURCE = textwrap.dedent(
    """
    import sys
    import warnings

    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib

    if sys.version_info < (3, 11):
        OLD = True
    if sys.version_info >= (3, 12):
        NEW = True
    if sys.platform == "win32":
        SEP = "\\\\"

    def load_legacy(path):
        warnings.warn("use load", DeprecationWarning, stacklevel=2)
        return path

    HAS_FORK = hasattr(os, "fork")
    """
)


class ScanTests(unittest.TestCase):
    def scan(self, minimum: tuple[int, ...] | None) -> list[fcp.Candidate]:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mod.py"
            path.write_text(SOURCE)
            return fcp.scan_file(path, minimum)

    def test_finds_every_kind(self) -> None:
        kinds = [c.kind for c in self.scan(None)]
        self.assertEqual(
            kinds,
            [
                "import-fallback",
                "version-branch",
                "version-branch",
                "version-branch",
                "deprecated-alias",
                "feature-probe",
            ],
        )

    def test_dead_branch_status_for_minimum_version(self) -> None:
        details = [c.detail for c in self.scan((3, 11)) if c.kind == "version-branch"]
        self.assertIn("false for every supported version", details[0])
        self.assertIn("live for some supported versions", details[1])

    def test_missing_path_is_input_error(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(fcp.main(["/nonexistent/x.py"]), 2)
        self.assertIn("/nonexistent/x.py does not exist", err.getvalue())

    def test_limit_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mod.py"
            path.write_text(SOURCE)
            total = len(fcp.scan_file(path, None))
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = fcp.main([str(path), "--json", "--limit", "1"])
        self.assertGreater(total, 1)
        self.assertEqual(status, 0)
        (only,) = json.loads(out.getvalue())
        self.assertEqual(only["path"], str(path))
        self.assertIn(f"showing 1 of {total}", err.getvalue())

    def test_bad_min_python_is_a_usage_error(self) -> None:
        with (
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            fcp.main([".", "--min-python", "3.x"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
