"""Tests for check_action_pins.py (stdlib only; run directly, offline)."""

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
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_action_pins as pins

SHA = "3d3c42e5aac5ba805825da76410c181273ba90b1"
WORKFLOW = f"""
jobs:
  a:
    steps:
      - uses: actions/checkout@{SHA} # v7.0.1
      - uses: actions/setup-python@v6
      - uses: "actions/cache@main"
      - uses: ./.github/actions/local
      - uses: docker://alpine:3.22
      - uses: docker://alpine@sha256:{"a" * 64}
      - name: not a uses line
        run: echo uses: nothing@v1
"""


def findings(text: str, resolve: bool = False) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "ci.yml"
        path.write_text(textwrap.dedent(text))
        return [f.split(": ", 1)[1] for f in pins.check_file(path, resolve)]


class PinTests(unittest.TestCase):
    def test_reports_tags_branches_and_undigested_images(self) -> None:
        self.assertEqual(
            findings(WORKFLOW),
            [
                "actions/setup-python pinned to 'v6', not a commit SHA",
                "actions/cache pinned to 'main', not a commit SHA",
                "docker image not pinned by digest: docker://alpine:3.22",
            ],
        )

    def test_resolve_accepts_matching_comment(self) -> None:
        with mock.patch.object(pins, "resolve", return_value=SHA):
            self.assertEqual(findings(f"- uses: a/b@{SHA} # v7.0.1\n", True), [])

    def test_resolve_reports_drifted_comment(self) -> None:
        other = "f" * 40
        with mock.patch.object(pins, "resolve", return_value=other):
            found = findings(f"- uses: a/b@{SHA} # v7.0.1\n", True)
        self.assertEqual(found, ["comment v7.0.1 is ffffffffffff, pin is 3d3c42e5aac5"])

    def test_resolve_reports_unknown_tag(self) -> None:
        with mock.patch.object(pins, "resolve", return_value=None):
            found = findings(f"- uses: a/b@{SHA} # v9\n", True)
        self.assertEqual(found, ["could not resolve a/b@v9"])

    def test_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ci.yml"
            path.write_text(WORKFLOW)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = pins.main([str(path), "--json"])
        report = json.loads(out.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(report["count"], 3)
        first = report["findings"][0]
        self.assertEqual(first["file"], str(path))
        self.assertIsInstance(first["line"], int)
        self.assertEqual(
            first["message"], "actions/setup-python pinned to 'v6', not a commit SHA"
        )

    def test_missing_path_is_input_error(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(pins.main(["/nonexistent/ci.yml"]), 2)
        self.assertIn("does not exist", err.getvalue())


if __name__ == "__main__":
    unittest.main()
