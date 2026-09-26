"""Exercise the shipped oracle in disposable, real Git histories.

Requires Git and Python only. No user's repository, configuration, hooks, or
credentials are used. The oracle resides outside the history under test.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ORACLE = Path(__file__).with_name("bisect_oracle.py").resolve()


@unittest.skipUnless(shutil.which("git"), "Git is not installed")
class BisectIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="skill-bisect-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        # Prevent ambient repo/index/config settings from touching an unrelated tree.
        self.env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        self.env.update(
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_TERMINAL_PROMPT="0",
            LC_ALL="C",
        )
        self.git("init", "-q")
        self.git("config", "user.name", "Isolated fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgSign", "false")
        self.git("config", "core.hooksPath", str(self.root / "no-hooks"))
        self.git("config", "core.autocrlf", "false")

    def git(self, *args, check=True):
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            env=self.env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        if check and result.returncode:
            self.fail(f"git {args!r}: {result.stdout}\n{result.stderr}")
        return result

    def history(self, statuses):
        revisions = []
        for index, status in enumerate(statuses):
            (self.repo / "state.txt").write_text(str(status), encoding="utf-8")
            (self.repo / "revision.txt").write_text(str(index), encoding="utf-8")
            self.git("add", "state.txt", "revision.txt")
            self.git("commit", "-qm", f"fixture revision {index}")
            revisions.append(self.git("rev-parse", "HEAD").stdout.strip())
        return revisions

    def bisect(self, revisions):
        self.git("bisect", "start", revisions[-1], revisions[0])
        self.addCleanup(lambda: self.git("bisect", "reset", check=False))
        return self.git(
            "bisect",
            "run",
            sys.executable,
            str(ORACLE),
            "--skip-exit",
            "77",
            "--timeout",
            "10",
            "--",
            sys.executable,
            "-c",
            "from pathlib import Path; raise SystemExit(int(Path('state.txt').read_text()))",
            check=False,
        )

    def test_identifies_exact_first_bad_revision(self):
        revisions = self.history([0, 0, 0, 1, 1, 1, 1])
        result = self.bisect(revisions)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = result.stdout.replace("'bad'", "bad")
        self.assertIn(revisions[3] + " is the first bad commit", output)
        self.assertEqual(
            self.git("rev-parse", "refs/bisect/bad").stdout.strip(), revisions[3]
        )

    def test_skipped_boundary_reports_ambiguity_not_a_unique_culprit(self):
        revisions = self.history([0, 77, 1])
        result = self.bisect(revisions)
        output = (result.stdout + result.stderr).replace("'bad'", "bad")
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn("The first bad commit could be any of:", output)
        self.assertIn(revisions[1], output)
        self.assertIn(revisions[2], output)
        self.assertNotIn("is the first bad commit", output)

    def test_unclassified_failure_aborts_without_marking_midpoint_bad(self):
        revisions = self.history([0, 2, 1])
        result = self.bisect(revisions)
        output = (result.stdout + result.stderr).replace("'bad'", "bad")
        self.assertNotEqual(result.returncode, 0, output)
        self.assertIn("bisect oracle abort: unclassified command exit 2", output)
        self.assertEqual(
            self.git("rev-parse", "refs/bisect/bad").stdout.strip(), revisions[-1]
        )
        self.assertNotIn("is the first bad commit", output)


if __name__ == "__main__":
    unittest.main()
