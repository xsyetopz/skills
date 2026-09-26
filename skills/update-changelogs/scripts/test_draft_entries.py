"""Tests for draft_entries.py (stdlib + git; run directly)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import draft_entries as de


def commit(sha: str, subject: str, body: str = "") -> de.Commit:
    return de.Commit(sha, subject, body)


class BuildDraftTests(unittest.TestCase):
    def test_categories_and_minor_bump(self) -> None:
        draft = de.build_draft(
            [
                commit("a1", "feat(api): add export cancel"),
                commit("b2", "fix: keep destination on cancel"),
                commit("c3", "docs: explain cancel"),
                commit("d4", "Update stuff"),
            ]
        )
        self.assertEqual(draft.categories["Added"], ["api: add export cancel (a1)"])
        self.assertEqual(draft.categories["Fixed"], ["keep destination on cancel (b2)"])
        self.assertEqual(draft.unclassified, ["Update stuff (d4)"])
        self.assertEqual(draft.bump, "minor")

    def test_breaking_bang_and_footer(self) -> None:
        draft = de.build_draft(
            [
                commit("e5", "feat!: drop v1 endpoint"),
                commit("f6", "fix: rename flag", "BREAKING CHANGE: --x is now --y"),
            ]
        )
        self.assertEqual(len(draft.categories["Changed"]), 2)
        self.assertTrue(all("**Breaking:**" in e for e in draft.categories["Changed"]))
        self.assertEqual(draft.bump, "major")

    def test_patch_and_none(self) -> None:
        self.assertEqual(de.build_draft([commit("a", "perf: faster")]).bump, "patch")
        self.assertEqual(de.build_draft([commit("a", "chore: bump")]).bump, "none")


@unittest.skipUnless(shutil.which("git"), "git not installed")
class GitIntegrationTests(unittest.TestCase):
    def test_reads_range_from_repository(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
            env.update(
                GIT_CONFIG_NOSYSTEM="1",
                GIT_CONFIG_GLOBAL=os.devnull,
                GIT_AUTHOR_NAME="t",
                GIT_AUTHOR_EMAIL="t@example.invalid",
                GIT_COMMITTER_NAME="t",
                GIT_COMMITTER_EMAIL="t@example.invalid",
            )

            def git(*args: str) -> None:
                subprocess.run(
                    ["git", *args], cwd=tmp, env=env, check=True, capture_output=True
                )

            git("init", "-q")
            git("commit", "-q", "--allow-empty", "-m", "chore: init")
            git("tag", "v1.0.0")
            git("commit", "-q", "--allow-empty", "-m", "feat: add thing")
            old = os.getcwd()
            os.chdir(tmp)
            old_env = dict(os.environ)
            os.environ.clear()
            os.environ.update(env)
            try:
                out = io.StringIO()
                with contextlib.redirect_stdout(out):
                    status = de.main(
                        ["v1.0.0..HEAD", "--version", "1.1.0", "--date", "2026-09-25"]
                    )
            finally:
                os.chdir(old)
                os.environ.clear()
                os.environ.update(old_env)
            self.assertEqual(status, 0)
            self.assertIn("## [1.1.0] - 2026-09-25", out.getvalue())
            self.assertIn("### Added", out.getvalue())
            self.assertIn("suggested SemVer increment: minor", out.getvalue())

    def test_json_draft(self) -> None:
        commits = [
            de.Commit("a1", "feat(cli): add --limit", ""),
            de.Commit("b2", "fix: handle empty input", ""),
            de.Commit("c3", "docs: typo", ""),
            de.Commit("d4", "rework everything", ""),
        ]
        out = io.StringIO()
        with (
            mock.patch.object(de, "read_commits", return_value=commits),
            contextlib.redirect_stdout(out),
        ):
            status = de.main(["v1.0.0..HEAD", "--json"])
        self.assertEqual(status, 0)
        self.assertEqual(
            json.loads(out.getvalue()),
            {
                "heading": "[Unreleased]",
                "bump": "minor",
                "categories": {
                    "Added": ["cli: add --limit (a1)"],
                    "Fixed": ["handle empty input (b2)"],
                },
                "unclassified": ["rework everything (d4)"],
            },
        )


if __name__ == "__main__":
    unittest.main()
