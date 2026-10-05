"""Tests for change_coupling.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import change_coupling
from change_coupling import couple, parse_log

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "test@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "test@example.com",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
}


def run(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        status = change_coupling.main(argv)
    return status, out.getvalue()


def usage_error(argv: list[str]) -> int:
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            change_coupling.main(argv)
        except SystemExit as exit_:
            return int(exit_.code or 0)
    return 0


def pairs_of(result: list[change_coupling.Pair]) -> dict[tuple[str, str], int]:
    return {(p.entity, p.coupled): p.degree for p in result}


class ParseLogTests(unittest.TestCase):
    def test_splits_commits_and_skips_blank_lines(self) -> None:
        text = "--abc1234\na.py\nsrc/b.py\n\n--def5678\nc.py\n"
        self.assertEqual(parse_log(text), [{"a.py", "src/b.py"}, {"c.py"}])

    def test_commit_without_files_is_an_empty_set(self) -> None:
        text = "--abc1234\n--def5678\na.py\n"
        self.assertEqual(parse_log(text), [set(), {"a.py"}])

    def test_empty_log(self) -> None:
        self.assertEqual(parse_log(""), [])


class CoupleTests(unittest.TestCase):
    def test_degree_is_shared_over_average_revisions(self) -> None:
        # a: 6 revs, b: 4 revs, 4 shared -> 4 / 5 = 80%, average-revs 5.
        commits = [{"a", "b"}] * 4 + [{"a"}] * 2
        result = couple(commits, min_revs=1, min_shared=1)
        self.assertEqual(len(result), 1)
        pair = result[0]
        self.assertEqual((pair.entity, pair.coupled), ("a", "b"))
        self.assertEqual((pair.degree, pair.shared_revs, pair.average_revs), (80, 4, 5))

    def test_degree_rounds_down_and_average_rounds_up(self) -> None:
        # a: 3 revs, b: 4 revs, 3 shared -> 3 / 3.5 = 85.7% -> 85; 3.5 -> 4.
        commits = [{"a", "b"}] * 3 + [{"b"}]
        pair = couple(commits, min_revs=1, min_shared=1)[0]
        self.assertEqual((pair.degree, pair.average_revs), (85, 4))

    def test_default_thresholds(self) -> None:
        five = [{"a", "b"}] * 5
        self.assertEqual(pairs_of(couple(five)), {("a", "b"): 100})
        four = [{"a", "b"}] * 4
        self.assertEqual(couple(four), [])

    def test_min_revs_applies_to_the_average_like_code_maat(self) -> None:
        # a has 10 revisions and b has 2, so the average is 6.
        commits = [{"a", "b"}] * 2 + [{"a"}] * 8
        self.assertEqual(couple(commits, min_revs=7, min_shared=1, min_coupling=1), [])
        self.assertEqual(
            len(couple(commits, min_revs=6, min_shared=1, min_coupling=1)), 1
        )

    def test_min_coupling_filters_weak_pairs(self) -> None:
        # 5 shared of a: 25 revs, b: 5 revs -> 5 / 15 = 33%.
        commits = [{"a", "b"}] * 5 + [{"a"}] * 20
        self.assertEqual(pairs_of(couple(commits)), {("a", "b"): 33})
        self.assertEqual(couple(commits, min_coupling=34), [])

    def test_large_changesets_are_skipped(self) -> None:
        big = {"a", "b", *(f"f{i}" for i in range(29))}
        stats = change_coupling.Stats()
        result = couple([big] * 5, stats=stats)
        self.assertEqual(result, [])
        self.assertEqual((stats.commits, stats.skipped_large), (5, 5))
        self.assertEqual(len(couple([big] * 5, max_changeset=31)), 465)

    def test_test_files_are_dropped_unless_included(self) -> None:
        commits = [{"src/a.py", "tests/test_a.py", "src/a.test.ts"}] * 5
        self.assertEqual(couple(commits), [])
        included = couple(commits, include_tests=True)
        self.assertEqual(len(included), 3)

    def test_cross_dir_and_sort_order(self) -> None:
        commits = [{"src/a.py", "src/b.py"}] * 5 + [{"src/a.py", "lib/c.py"}] * 6
        result = couple(commits)
        self.assertEqual(
            [(p.entity, p.coupled, p.cross_dir) for p in result],
            [("lib/c.py", "src/a.py", True), ("src/a.py", "src/b.py", False)],
        )
        self.assertEqual([p.degree for p in result], [70, 62])

    def test_is_test_matches_file_length_rules(self) -> None:
        for path in (
            "tests/x.py",
            "a/test_x.py",
            "x_test.go",
            "FooTest.java",
            "a.spec.ts",
        ):
            self.assertTrue(change_coupling.is_test(path), path)
        for path in ("src/latest.py", "contest.py", "attest/x.py"):
            self.assertFalse(change_coupling.is_test(path), path)


class GitRepoTests(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.git("init", "-q")
        for i in range(5):
            self.commit(i, "src/core.py", "lib/helper.py")
        self.commit(5, "src/core.py")
        # A mass change coupling everything; skipped with --max-changeset 3.
        for i in range(5):
            self.commit(10 + i, "src/core.py", "a.py", "b.py", "c.py")

    def git(self, *args: str) -> None:
        subprocess.run(
            ["git", "-c", "commit.gpgsign=false", *args],
            cwd=self.root,
            env={**os.environ, **GIT_ENV},
            check=True,
            capture_output=True,
        )

    def commit(self, n: int, *names: str) -> None:
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"{n}\n")
        self.git("add", *names)
        self.git("commit", "-q", "-m", f"change {n}")

    def test_reports_known_pair_and_skips_large_commits(self) -> None:
        status, out = run(["--repo", str(self.root), "--max-changeset", "3", "--json"])
        self.assertEqual(status, 1)
        report = json.loads(out)
        # core: 6 revs (large commits skipped), helper: 5 revs -> 5 / 5.5 = 90%.
        self.assertEqual(
            report["pairs"],
            [
                {
                    "entity": "lib/helper.py",
                    "coupled": "src/core.py",
                    "degree": 90,
                    "average_revs": 6,
                    "shared_revs": 5,
                    "cross_dir": True,
                }
            ],
        )
        self.assertEqual(report["summary"]["skipped_large_commits"], 5)
        self.assertEqual(report["summary"]["cross_dir_pairs"], 1)

    def test_large_commits_count_when_under_the_limit(self) -> None:
        status, out = run(["--repo", str(self.root), "--json"])
        self.assertEqual(status, 1)
        degrees = {
            (p["entity"], p["coupled"]): p["degree"] for p in json.loads(out)["pairs"]
        }
        self.assertEqual(degrees[("a.py", "b.py")], 100)
        # core: 11 revs, helper: 5 revs -> 5 / 8 = 62%.
        self.assertEqual(degrees[("lib/helper.py", "src/core.py")], 62)

    def test_text_output_and_limit(self) -> None:
        status, out = run(["--repo", str(self.root), "--limit", "1"])
        self.assertEqual(status, 1)
        lines = out.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("degree%", lines[0])
        self.assertIn("1 pairs reported (0 cross directories) of 7", lines[2])

    def test_no_pair_exits_zero(self) -> None:
        status, out = run(["--repo", str(self.root), "--min-shared", "20"])
        self.assertEqual(status, 0)
        self.assertIn("0 pairs reported", out)

    def test_since_in_the_future_finds_nothing(self) -> None:
        status, _ = run(["--repo", str(self.root), "--since", "2099-01-01"])
        self.assertEqual(status, 0)

    def test_not_a_repository_exits_two(self) -> None:
        with tempfile.TemporaryDirectory() as other:
            env = {**os.environ, "GIT_CEILING_DIRECTORIES": other}
            with mock.patch.dict(os.environ, env):
                status, _ = run(["--repo", other])
        self.assertEqual(status, 2)

    def test_git_missing_exits_two(self) -> None:
        with (
            tempfile.TemporaryDirectory() as empty,
            mock.patch.dict(os.environ, {"PATH": empty}),
        ):
            status, _ = run(["--repo", str(self.root)])
        self.assertEqual(status, 2)

    def test_bad_option_values_exit_two(self) -> None:
        for argv in (
            ["--min-revs", "0"],
            ["--limit", "-1"],
            ["--min-coupling", "0"],
            ["--min-coupling", "101"],
            ["--max-changeset", "x"],
        ):
            self.assertEqual(usage_error(["--repo", str(self.root), *argv]), 2, argv)


if __name__ == "__main__":
    unittest.main()
