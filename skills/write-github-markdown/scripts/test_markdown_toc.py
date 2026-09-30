"""Tests for markdown_toc.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import markdown_toc as toc

DOCUMENT = textwrap.dedent(
    """\
    # Guide

    Intro.

    ## Contents

    - Install
    - Usage

    ## Install

    ```sh
    ## not a heading
    ```

    ### From source

    ## Usage: the `run` command

    ## Usage: the `run` command
    """
)


class BuildTests(unittest.TestCase):
    def test_links_every_level_two_heading_with_github_anchors(self) -> None:
        result = toc.build(DOCUMENT, max_level=2)
        self.assertIn(
            "## Contents\n\n"
            "- [Install](#install)\n"
            "- [Usage: the `run` command](#usage-the-run-command)\n"
            "- [Usage: the `run` command](#usage-the-run-command-1)\n"
            "\n## Install\n",
            result,
        )
        self.assertNotIn("not-a-heading", result)

    def test_max_level_nests_deeper_headings(self) -> None:
        result = toc.build(DOCUMENT, max_level=3)
        self.assertIn(
            "- [Install](#install)\n  - [From source](#from-source)\n", result
        )

    def test_rebuilding_is_stable(self) -> None:
        once = toc.build(DOCUMENT, max_level=2)
        self.assertEqual(toc.build(once, max_level=2), once)

    def test_long_entries_use_reference_links_within_width(self) -> None:
        heading = "A heading long enough that the inline link passes the width"
        text = f"# T\n\n## Contents\n\n- x\n\n## Short\n\n## {heading}\n\nEnd.\n"
        result = toc.build(text, max_level=2)
        slug = toc.github_slug(heading)
        self.assertIn(
            f"- [Short](#short)\n- [{heading}][toc-1]\n\n[toc-1]: #{slug}\n\n## Short",
            result,
        )
        for line in result.splitlines():
            if not line.startswith("[toc-"):
                self.assertLessEqual(len(line), 80, line)
        self.assertEqual(toc.build(result, max_level=2), result)

    def test_stale_toc_definitions_elsewhere_are_removed(self) -> None:
        text = (
            "## Contents\n\n- [Old][toc-old]\n\n## New\n\nBody.\n\n"
            "[toc-old]: #old\n[docs]: https://example.com\n"
        )
        result = toc.build(text, max_level=2)
        self.assertNotIn("toc-old", result)
        self.assertIn("[docs]: https://example.com", result)

    def test_slug_rules(self) -> None:
        cases = {
            "Tables & lists": "tables--lists",
            "Use `--json` output": "use---json-output",
            "See [docs](https://example.com)": "see-docs",
            "  Trailing  ": "trailing",
            "Café 2.0!": "café-20",
        }
        for heading, slug in cases.items():
            self.assertEqual(toc.github_slug(heading), slug, heading)

    def test_missing_contents_heading_is_an_error(self) -> None:
        with self.assertRaises(toc.InputError):
            toc.build("# Title\n\n## Install\n", max_level=2)

    def test_prose_in_contents_section_is_an_error(self) -> None:
        with self.assertRaises(toc.InputError):
            toc.build("## Contents\n\nRead this first.\n\n## Install\n", max_level=2)


class MainTests(unittest.TestCase):
    def run_main(self, *args: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            code = toc.main(list(args))
        return code, out.getvalue()

    def test_check_reports_stale_then_write_fixes_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "guide.md"
            path.write_text(DOCUMENT, encoding="utf-8")
            code, output = self.run_main("--check", str(path))
            self.assertEqual(code, 1)
            self.assertIn("stale", output)
            self.assertEqual(path.read_text(encoding="utf-8"), DOCUMENT)
            self.assertEqual(self.run_main(str(path))[0], 0)
            self.assertEqual(self.run_main("--check", str(path)), (0, ""))

    def test_bad_input_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plain.md"
            path.write_text("# Title\n", encoding="utf-8")
            self.assertEqual(self.run_main(str(path))[0], 2)
            self.assertEqual(self.run_main(str(Path(tmp) / "missing.md"))[0], 2)

    def test_bad_file_does_not_stop_the_rest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "plain.md"
            bad.write_text("# Title\n", encoding="utf-8")
            good = Path(tmp) / "guide.md"
            good.write_text(DOCUMENT, encoding="utf-8")
            code, output = self.run_main(str(bad), str(good))
            self.assertEqual(code, 2)
            self.assertIn("plain.md", output)
            self.assertIn("(#install)", good.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
