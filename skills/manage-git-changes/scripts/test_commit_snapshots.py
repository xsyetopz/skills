"""Exercise Git snapshot mechanics, not model selection or semantic slicing."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class CommitSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.env = {
            key: value
            for key, value in os.environ.items()
            if not key.startswith("GIT_")
        }
        self.env.update(
            HOME=str(self.root),
            XDG_CONFIG_HOME=str(self.root / "config"),
            GIT_CONFIG_NOSYSTEM="1",
            GIT_CONFIG_GLOBAL=os.devnull,
            GIT_TERMINAL_PROMPT="0",
        )
        template = self.root / "empty-template"
        template.mkdir()
        self.git("init", "-q", f"--template={template}")
        self.git("config", "user.name", "Snapshot Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.git("config", "commit.gpgSign", "false")
        self.hooks = self.repo / ".git/hooks"
        self.hooks.mkdir()
        self.git("config", "core.hooksPath", str(self.hooks))
        self.feature("a", 1)
        self.feature("b", 2)
        self.write(".gitignore", "__pycache__/\n")
        self.git("add", ".")
        self.commit("chore: initialize fixture")
        self.base = self.git("rev-parse", "HEAD").strip()

    def git(self, *args: str, index: Path | None = None, status: int = 0) -> str:
        env = self.env.copy()
        if index is not None:
            env["GIT_INDEX_FILE"] = str(index)
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        self.assertEqual(result.returncode, status, result.stdout + result.stderr)
        return result.stdout

    def write(self, path: str, content: str) -> None:
        (self.repo / path).write_text(content)

    def feature(self, name: str, value: int) -> None:
        self.write(f"{name}.py", f"VALUE = {value}\n")
        self.write(
            f"check_{name}.py", f"from {name} import VALUE\nassert VALUE == {value}\n"
        )
        self.write(f"{name}.md", f"# {name}\n\nReturns {value}.\n")

    def stage_feature(self, name: str) -> None:
        self.git("add", "--", f"{name}.py", f"check_{name}.py", f"{name}.md")

    def check_snapshot(self, *, index: Path | None = None, status: int = 0) -> None:
        with tempfile.TemporaryDirectory(dir=self.root) as temporary:
            self.git("checkout-index", "--all", f"--prefix={temporary}/", index=index)
            result = subprocess.run(
                [sys.executable, "-c", "import check_a, check_b"],
                cwd=temporary,
                env=self.env,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            self.assertEqual(result.returncode, status, result.stdout + result.stderr)
            if status:
                self.assertIn("AssertionError", result.stderr)

    def commit(self, message: str, *, index: Path | None = None) -> str:
        tree = self.git("write-tree", index=index)
        self.git("commit", "-q", "-m", message, index=index)
        self.assertEqual(self.git("rev-parse", "HEAD^{tree}"), tree)
        self.assertEqual(self.git("log", "-1", "--format=%s").strip(), message)
        return self.git("rev-parse", "HEAD").strip()

    def test_independent_slices_validate_and_revert_independently(self) -> None:
        self.feature("a", 10)
        self.feature("b", 20)
        self.stage_feature("a")
        self.check_snapshot()
        first = self.commit("feat(a): return ten")
        self.assertEqual(self.git("show", "HEAD:b.py"), "VALUE = 2\n")
        self.stage_feature("b")
        self.check_snapshot()
        second = self.commit("feat(b): return twenty")
        for removed, retained, expected in ((first, "b", 20), (second, "a", 10)):
            with self.subTest(removed=removed):
                self.git("switch", "--detach", second)
                self.git("revert", "--no-edit", removed)
                self.check_snapshot()
                self.assertEqual(
                    self.git("show", f"HEAD:{retained}.py"), f"VALUE = {expected}\n"
                )
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_inseparable_source_and_test_change_need_one_snapshot(self) -> None:
        self.feature("a", 10)
        self.git("add", "--", "a.py")
        self.check_snapshot(status=1)
        self.stage_feature("a")
        self.check_snapshot()
        self.commit("feat(a): return ten")
        self.assertEqual(
            set(
                self.git(
                    "diff-tree", "--no-commit-id", "--name-only", "-r", "HEAD"
                ).splitlines()
            ),
            {"a.py", "a.md", "check_a.py"},
        )

    def test_dependency_order_keeps_each_snapshot_valid(self) -> None:
        self.feature("a", 10)
        self.stage_feature("a")
        self.check_snapshot()
        prerequisite = self.commit("feat(a): return ten")
        self.feature("b", 20)
        self.write("b.py", "from a import VALUE as BASE\nVALUE = BASE * 2\n")
        self.stage_feature("b")
        self.check_snapshot()
        dependent = self.commit("feat(b): derive value from a")
        self.git("revert", "--no-edit", dependent)
        self.check_snapshot()
        self.git("revert", "--no-edit", prerequisite)
        self.assertEqual(
            self.git("rev-parse", "HEAD^{tree}"),
            self.git("rev-parse", f"{self.base}^{{tree}}"),
        )

    def test_explicit_single_commit_can_include_both_behaviors(self) -> None:
        self.feature("a", 10)
        self.feature("b", 20)
        self.stage_feature("a")
        self.stage_feature("b")
        self.check_snapshot()
        self.commit("feat: update both values")
        self.assertEqual(
            self.git("rev-list", "--count", f"{self.base}..HEAD").strip(), "1"
        )

    def test_partial_staging_preserves_unrelated_index_and_worktree(self) -> None:
        self.feature("a", 10)
        self.stage_feature("a")
        self.write("a.py", "VALUE = 10\nLATER = 'unstaged'\n")
        self.feature("b", 20)
        self.stage_feature("b")
        self.write("b.py", "VALUE = 20\nLATER = 'unrelated'\n")
        self.write("untracked.txt", "preserve me\n")
        staged_b = self.git("ls-files", "--stage", "--", "b.py", "b.md", "check_b.py")
        worktree = {p.name: p.read_bytes() for p in self.repo.iterdir() if p.is_file()}
        hook = self.hooks / "pre-commit"
        hook.write_text("#!/bin/sh\ngit write-tree > .git/observed-hook-tree\n")
        hook.chmod(0o755)
        isolated = self.root / "isolated-index"
        self.git("read-tree", "HEAD", index=isolated)
        for path in ("a.py", "a.md", "check_a.py"):
            mode, blob, _ = self.git("ls-files", "--stage", "--", path).split()[:3]
            self.git(
                "update-index", "--add", "--cacheinfo", mode, blob, path, index=isolated
            )
        self.check_snapshot(index=isolated)
        self.commit("feat(a): return ten", index=isolated)
        self.assertEqual(
            (self.repo / ".git/observed-hook-tree").read_text(),
            self.git("rev-parse", "HEAD^{tree}"),
        )
        self.assertEqual(self.git("show", "HEAD:a.py"), "VALUE = 10\n")
        self.assertEqual(self.git("show", "HEAD:b.py"), "VALUE = 2\n")
        self.assertEqual(
            self.git("ls-files", "--stage", "--", "b.py", "b.md", "check_b.py"),
            staged_b,
        )
        self.assertEqual(
            {p.name: p.read_bytes() for p in self.repo.iterdir() if p.is_file()},
            worktree,
        )
        self.assertIn("LATER = 'unstaged'", self.git("diff", "--", "a.py"))

    def test_commit_only_is_a_negative_control_for_partial_staging(self) -> None:
        self.feature("a", 10)
        self.stage_feature("a")
        self.write("a.py", "VALUE = 10\nLATER = 'not authorized'\n")
        intended = self.git("write-tree")
        self.git("commit", "-q", "--only", "-m", "feat: wrong snapshot", "--", "a.py")
        self.assertNotEqual(self.git("rev-parse", "HEAD^{tree}"), intended)
        self.assertIn("not authorized", self.git("show", "HEAD:a.py"))

    def test_failed_hook_can_change_index_without_advancing_head(self) -> None:
        self.feature("a", 10)
        self.stage_feature("a")
        intended = self.git("write-tree")
        hook = self.hooks / "pre-commit"
        hook.write_text(
            "#!/bin/sh\nprintf 'VALUE = 99\\n' > a.py\ngit add -- a.py\nexit 1\n"
        )
        hook.chmod(0o755)
        self.git("commit", "-q", "-m", "feat(a): return ten", status=1)
        self.assertEqual(self.git("rev-parse", "HEAD").strip(), self.base)
        self.assertNotEqual(self.git("write-tree"), intended)
        self.assertEqual(self.git("show", ":a.py"), "VALUE = 99\n")
        self.check_snapshot(status=1)

    def test_successful_hook_is_not_snapshot_identity_proof(self) -> None:
        self.feature("a", 10)
        self.stage_feature("a")
        intended = self.git("write-tree")
        hook = self.hooks / "pre-commit"
        hook.write_text("#!/bin/sh\nprintf 'VALUE = 99\\n' > a.py\ngit add -- a.py\n")
        hook.chmod(0o755)
        self.git("commit", "-q", "-m", "feat(a): return ten")
        self.assertNotEqual(self.git("rev-parse", "HEAD^{tree}"), intended)
        self.assertEqual(self.git("status", "--porcelain"), "")
        self.check_snapshot(status=1)

    def test_explicit_message_policy_and_no_policy_fallback_are_recordable(
        self,
    ) -> None:
        # The scenario chooses policy; Git itself does not select conventions.
        self.feature("a", 10)
        self.stage_feature("a")
        self.commit("feat(a): return ten")
        self.write("CONTRIBUTING.md", "Commit subjects must start with TASK-42.\n")
        self.git("add", "--", "CONTRIBUTING.md")
        self.commit("TASK-42 document project message policy")
        hook = self.hooks / "commit-msg"
        hook.write_text(
            '#!/bin/sh\nIFS= read -r subject < "$1"\n'
            'case "$subject" in TASK-42*) exit 0 ;; *) exit 1 ;; esac\n'
        )
        hook.chmod(0o755)
        self.feature("b", 20)
        self.stage_feature("b")
        self.git("commit", "-q", "-m", "feat(b): wrong policy", status=1)
        self.check_snapshot()
        self.commit("TASK-42 return twenty from b")


if __name__ == "__main__":
    unittest.main()
