"""Tests for check_doc_commands (stdlib only)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_doc_commands as cdc


def quiet(function, *args):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        status = function(list(args))
    return status, out.getvalue()


def write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(textwrap.dedent(text))
    return path


class DocCommandTests(unittest.TestCase):
    def test_passing_command_and_failing_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = write(Path(tmp), "good.md", "```sh\necho hi\n```\n")
            bad = write(Path(tmp), "bad.md", "```sh\nls --no-such-flag-xyz\n```\n")
            self.assertEqual(quiet(cdc.main, str(good))[0], 0)
            self.assertEqual(quiet(cdc.main, str(bad))[0], 1)

    def test_console_transcript_and_output_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(
                Path(tmp),
                "doc.md",
                """\
                ```console
                $ echo hello
                hello
                $ echo two
                three
                ```
                """,
            )
            status, out = quiet(cdc.main, str(doc))
        self.assertEqual(status, 1)
        self.assertIn("ok   ", out)
        self.assertIn("output differs", out)

    def test_skip_marker_lists_without_running(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(
                Path(tmp),
                "doc.md",
                """\
                <!-- doc-check: skip -->
                ```sh
                exit 7
                ```
                """,
            )
            status, out = quiet(cdc.main, str(doc))
        self.assertEqual(status, 0)
        self.assertIn("skip", out)

    def test_json_report_lists_each_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(
                Path(tmp),
                "doc.md",
                """\
                ```console
                $ echo hello
                hello
                $ false
                ```
                """,
            )
            status, out = quiet(cdc.main, str(doc), "--json")
        self.assertEqual(status, 1)
        report = json.loads(out)
        self.assertEqual((report["passed"], report["total"]), (1, 2))
        first, second = report["checks"]
        self.assertEqual(
            (first["command"], first["status"], first["output_checked"]),
            ("echo hello", "ok", True),
        )
        self.assertEqual((second["status"], second["line"]), ("fail", 1))
        self.assertTrue(second["problem"].startswith("exit 1"))

    def test_missing_cwd_is_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(Path(tmp), "doc.md", "```sh\ntrue\n```\n")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                status, _ = quiet(cdc.main, str(doc), "--cwd", str(Path(tmp) / "no"))
        self.assertEqual(status, 2)
        self.assertIn("is not a directory", err.getvalue())

    def test_commands_run_in_a_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(Path(tmp), "doc.md", "```sh\ntouch created.txt\n```\n")
            quiet(cdc.main, str(doc))
            self.assertFalse((Path(tmp) / "created.txt").exists())

    def test_missing_sh_is_input_error_but_list_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(Path(tmp), "doc.md", "```sh\ntrue\n```\n")
            err = io.StringIO()
            with (
                mock.patch.object(cdc.shutil, "which", return_value=None),
                contextlib.redirect_stderr(err),
            ):
                status, _ = quiet(cdc.main, str(doc))
                listed, _ = quiet(cdc.main, str(doc), "--list")
        self.assertEqual(status, 2)
        self.assertIn("needs a POSIX sh (Git Bash or WSL) on PATH", err.getvalue())
        self.assertEqual(listed, 0)

    def test_listed_and_skipped_commands_do_not_count_as_passed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(Path(tmp), "doc.md", "```sh\ntrue\n```\n")
            status, out = quiet(cdc.main, str(doc), "--list", "--json")
            _, text = quiet(cdc.main, str(doc), "--list")
        report = json.loads(out)
        self.assertEqual(status, 0)
        self.assertEqual(
            (report["passed"], report["listed"], report["total"]), (0, 1, 1)
        )
        self.assertIn("0 passed, 0 failed, 0 skipped, 1 listed of 1", text)

    def test_output_is_decoded_as_utf_8_with_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(
                Path(tmp),
                "doc.md",
                "```sh\nprintf '\\303\\201\\377'\n```\n\nExpected:\n\n```text\n\u00c1\ufffd\n```\n",
            )
            # An ASCII locale, as a non-UTF-8 Windows code page would be:
            # without an explicit encoding the output would not decode.
            env = {
                **os.environ,
                "LC_ALL": "C",
                "PYTHONUTF8": "0",
                "PYTHONCOERCECLOCALE": "0",
            }
            result = subprocess.run(
                [sys.executable, cdc.__file__, str(doc)],
                env=env,
                capture_output=True,
                timeout=30,
                check=False,
            )
        self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))


if __name__ == "__main__":
    unittest.main()
