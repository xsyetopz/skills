"""Tests for term_report.py (stdlib only; run directly)."""

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

import term_report


def run(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        status = term_report.main(list(argv))
    return status, out.getvalue()


class TermReportTests(unittest.TestCase):
    def test_splits_identifier_styles(self) -> None:
        self.assertEqual(
            term_report.words("userRepo user_repo UserRepo HTTPServer"),
            ["user", "repo", "user", "repo", "user", "repo", "http", "server"],
        )

    def test_competing_term_sets_exit_one(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.py").write_text("repository = load_repository()\n")
            Path(tmp, "b.py").write_text("repo = open_repo()\n")
            status, output = run(tmp, "--group", "repository=repository,repo")
            self.assertEqual(status, 1)
            self.assertIn("b.py: 2", output)

    def test_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.py").write_text("repository = load_repository()\n")
            Path(tmp, "b.py").write_text("repo = open_repo()\n")
            status, output = run(tmp, "--group", "repository=repository,repo", "--json")
        report = json.loads(output)
        self.assertEqual(status, 1)
        self.assertTrue(report["mixed"])
        (group,) = report["groups"]
        self.assertEqual(
            (group["concept"], group["canonical"]), ("repository", "repository")
        )
        repo = group["terms"][1]
        self.assertEqual(
            (repo["term"], repo["total"], repo["competing"]), ("repo", 2, True)
        )
        self.assertEqual(list(repo["files"].values()), [2])

    def test_canonical_only_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.ts").write_text("const userRepository = 1;\n")
            status, _ = run(tmp, "--group", "repository=repository,repo")
            self.assertEqual(status, 0)

    def test_allow_mixed_reports_without_failing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "a.go").write_text("var dbStore Store\n")
            status, output = run(
                tmp, "--group", "storage=storage,store", "--allow-mixed"
            )
            self.assertEqual(status, 0)
            self.assertIn("store", output)

    def test_skips_vendor_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "node_modules").mkdir()
            Path(tmp, "node_modules", "x.js").write_text("repo\n")
            status, _ = run(tmp, "--group", "repository=repository,repo")
            self.assertEqual(status, 0)

    def test_bad_group_is_input_error(self) -> None:
        status, _ = run(".", "--group", "repository")
        self.assertEqual(status, 2)


if __name__ == "__main__":
    unittest.main()
