"""Tests for check_links (stdlib only)."""

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

import check_links as cl


def quiet(function, *args):
    with contextlib.redirect_stdout(io.StringIO()) as out:
        status = function(list(args))
    return status, out.getvalue()


def write(directory: Path, name: str, text: str) -> Path:
    path = directory / name
    path.write_text(textwrap.dedent(text))
    return path


class LinkTests(unittest.TestCase):
    def test_anchor_to_renamed_heading_and_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            doc = write(
                Path(tmp),
                "a.md",
                """\
                # Title
                ## Options & flags
                See [ok](#options--flags), [old](#flags), [gone](docs/x.md).
                """,
            )
            status, out = quiet(cl.main, str(doc))
        self.assertEqual(status, 1)
        self.assertIn("no heading for #flags", out)
        self.assertIn("missing target docs/x.md", out)
        self.assertNotIn("#options--flags", out)

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


if __name__ == "__main__":
    unittest.main()
