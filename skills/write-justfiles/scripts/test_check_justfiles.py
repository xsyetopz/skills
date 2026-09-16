"""Wrapper tests and separately labelled native-tool integration tests."""

import contextlib
import io
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import check_justfiles as check


class DiscoveryTests(unittest.TestCase):
    def test_names(self):
        for name in ("justfile", "Justfile", ".justfile", "tasks.just"):
            self.assertTrue(check.is_justfile(Path(name)))
        self.assertFalse(check.is_justfile(Path("notes.md")))

    def test_missing_explicit_path_is_error(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            self.assertRaisesRegex(ValueError, "does not exist"),
        ):
            check.discover([Path(tmp) / "missing.just"])

    def test_explicit_wrong_extension_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "note.txt"
            path.write_text("")
            with self.assertRaisesRegex(ValueError, "not a Just"):
                check.discover([path])

    def test_deduplicate_and_prune(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            p = root / "justfile"
            p.touch()
            (root / "node_modules").mkdir()
            (root / "node_modules/justfile").touch()
            (root / "sub").mkdir()
            q = root / "sub/.justfile"
            q.touch()
            self.assertEqual(check.discover([root, p]), sorted([p, q]))

    def test_native_argv_and_no_shell(self):
        with patch.object(
            subprocess, "run", return_value=subprocess.CompletedProcess([], 0, "", "")
        ) as run:
            check.validate(Path("/tmp/space ' ;.just"), "/tools/just", 10)
        self.assertEqual(
            run.call_args.args[0],
            ["/tools/just", "--fmt", "--check", "--justfile", "/tmp/space ' ;.just"],
        )
        self.assertNotIn("shell", run.call_args.kwargs)

    def test_native_failure_is_not_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "justfile"
            p.touch()
            with (
                patch.object(
                    check,
                    "validate",
                    return_value=subprocess.CompletedProcess([], 1, "diff", ""),
                ),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(check.main([str(p)]), 1)

    def test_no_files_is_invalid_not_pass(self):
        with (
            tempfile.TemporaryDirectory() as tmp,
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(check.main([tmp]), 2)

    def test_missing_native_tool_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "justfile"
            p.touch()
            with (
                patch.object(check, "validate", side_effect=FileNotFoundError("just")),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                self.assertEqual(check.main([str(p)]), 2)


@unittest.skipUnless(shutil.which("just"), "native Just executable not installed")
class NativeJustTests(unittest.TestCase):
    def test_comments_and_strings_are_not_policy_violations(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "justfile"
            p.write_text("""# env_var("OLD") is text, not a function call
value := 'env_var("OLD")'

default:
    @echo done
""")
            self.assertEqual(check.validate(p).returncode, 0)

    def test_invalid_syntax_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "justfile"
            p.write_text("default\n")
            self.assertNotEqual(check.validate(p).returncode, 0)


if __name__ == "__main__":
    unittest.main()
