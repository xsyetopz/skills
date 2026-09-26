"""Tests for check_doc_commands, check_links, and same_words (stdlib only)."""

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

import check_doc_commands as cdc
import check_links as cl
import same_words as sw

EXAMPLE = Path(__file__).resolve().parents[1] / "assets/examples/wordfreq"


def quiet(function, *args):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        status = function(list(args))
    return status, out.getvalue()


def write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(textwrap.dedent(text))
    return path


class DocCommandTests(unittest.TestCase):
    def test_example_readme_passes_and_broken_flag_fails(self) -> None:
        self.assertEqual(quiet(cdc.main, str(EXAMPLE / "README.md"))[0], 0)
        status, out = quiet(cdc.main, str(EXAMPLE / "README.broken.txt"))
        self.assertEqual(status, 1)
        self.assertIn("unrecognized arguments: --limit", out)

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


class LinkTests(unittest.TestCase):
    def test_example_docs_are_clean_and_broken_ones_are_not(self) -> None:
        good = [str(EXAMPLE / "README.md"), str(EXAMPLE / "CONTRIBUTING.md")]
        self.assertEqual(quiet(cl.main, *good)[0], 0)
        status, out = quiet(cl.main, str(EXAMPLE / "README.broken.txt"))
        self.assertEqual(status, 1)
        self.assertIn("no heading for #flags", out)
        self.assertIn("missing target docs/CONTRIBUTING.md", out)

    def test_duplicate_headings_and_code_are_handled(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(
                Path(tmp),
                "a.md",
                """\
                # Setup
                ## Setup
                See [second](#setup-1) and [bad](#setup-2).
                `[x](missing.md)`
                ```md
                [y](also-missing.md)
                ```
                """,
            )
            status, out = quiet(cl.main, str(doc))
        self.assertEqual(status, 1)
        self.assertIn("#setup-2", out)
        self.assertNotIn("missing.md", out)

    def test_vague_text_empty_alt_and_undefined_reference(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "img.png").write_bytes(b"")
            doc = write(
                Path(tmp),
                "a.md",
                """\
                Read [here](a.md). ![](img.png) See [docs][nowhere].
                """,
            )
            status, out = quiet(cl.main, str(doc))
        self.assertEqual(status, 1)
        self.assertIn("vague link text 'here'", out)
        self.assertIn("image without alt text", out)
        self.assertIn("undefined reference [nowhere]", out)

    def test_json_report_has_structured_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(
                Path(tmp),
                "a.md",
                """\
                # Title
                Read [here](#title) and [gone](gone.md).
                See <https://x.test> and [site](https://example.com).
                """,
            )
            status, out = quiet(cl.main, str(doc), "--json", "--external")
        self.assertEqual(status, 1)
        report = json.loads(out)
        self.assertEqual(
            report["errors"],
            [{"file": str(doc), "line": 2, "message": "missing target gone.md"}],
        )
        self.assertEqual(
            report["warnings"],
            [{"file": str(doc), "line": 2, "message": "vague link text 'here'"}],
        )
        self.assertEqual(
            [x["message"] for x in report["external"]], ["https://example.com"]
        )

    def test_missing_path_is_input_error(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            status, _ = quiet(cl.main, "/nonexistent/docs")
        self.assertEqual(status, 2)
        self.assertIn("/nonexistent/docs does not exist", err.getvalue())

    def test_slug_rules(self) -> None:
        self.assertEqual(cl.slug("Options & flags"), "options--flags")
        self.assertEqual(cl.slug("`check_links.py` usage"), "check_linkspy-usage")


class SameWordsTests(unittest.TestCase):
    def compare(self, before: str, after: str):
        with tempfile.TemporaryDirectory() as tmp:
            a = write(Path(tmp), "a.md", before)
            b = write(Path(tmp), "b.md", after)
            return quiet(sw.main, str(a), str(b))

    def test_rewrap_and_list_markers_are_formatting(self) -> None:
        before = "Run the tests\nbefore pushing.\n\n* one\n* two\n"
        after = "Run the tests before pushing.\n\n- one\n- two\n"
        self.assertEqual(self.compare(before, after)[0], 0)

    def test_changed_word_url_or_code_is_reported(self) -> None:
        status, out = self.compare("Use [docs](a.md) now.\n", "Use [docs](b.md) now.\n")
        self.assertEqual(status, 1)
        self.assertIn("a.md", out)
        status, out = self.compare(
            "```sh\nmake  test\n```\n", "```sh\nmake test\n```\n"
        )
        self.assertEqual(status, 1)

    def test_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            a = write(Path(tmp), "a.md", "Run tests.\n\n```sh\nmake test\n```\n")
            b = write(Path(tmp), "b.md", "Run checks.\n\n```sh\nmake test\n```\n")
            status, out = quiet(sw.main, str(a), str(b), "--json")
            same_status, same_out = quiet(sw.main, str(a), str(a), "--json")
        self.assertEqual(status, 1)
        self.assertEqual(
            json.loads(out),
            {
                "same": False,
                "differences": 1,
                "words": [
                    {"change": "replace", "removed": "tests.", "added": "checks."}
                ],
                "code_diff": [],
            },
        )
        self.assertEqual(same_status, 0)
        self.assertTrue(json.loads(same_out)["same"])

    def test_wrong_argument_count_is_usage_error(self) -> None:
        with (
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as raised,
        ):
            sw.main(["only-one.md"])
        self.assertEqual(raised.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
