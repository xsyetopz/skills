"""Tests for reflow_markdown.py (stdlib only; run directly)."""

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

import reflow_markdown as reflow


def dedent(text: str) -> str:
    return textwrap.dedent(text).lstrip("\n")


class ReflowTests(unittest.TestCase):
    def test_paragraph_fills_each_line_up_to_width(self) -> None:
        text = "one two\nthree four five\nsix seven eight nine ten\n"
        result = reflow.reflow(text, 20)
        self.assertEqual(result, "one two three four\nfive six seven eight\nnine ten\n")
        self.assertTrue(all(len(line) <= 20 for line in result.splitlines()))

    def test_list_item_keeps_marker_and_continuation_indent(self) -> None:
        text = (
            "- alpha beta\n  gamma delta epsilon\n1. one two\n   three four five six\n"
        )
        self.assertEqual(
            reflow.reflow(text, 22),
            "- alpha beta gamma\n  delta epsilon\n1. one two three four\n   five six\n",
        )

    def test_block_quote_keeps_its_marker_on_every_line(self) -> None:
        text = "> alpha beta gamma\n> delta epsilon zeta eta\n"
        self.assertEqual(
            reflow.reflow(text, 22), "> alpha beta gamma\n> delta epsilon zeta\n> eta\n"
        )

    def test_non_paragraph_blocks_are_unchanged(self) -> None:
        text = dedent(
            """
            ---
            description: a b
              c d
            ---

            # A heading that is long enough to wrap

            ```sh
            echo one
            echo two
            ```

            | a | b |
            |---|---|
            | c | d |

            <details>
            <summary>x</summary>
            </details>

            [label]: https://example.com/a/very/long/path/that/is/longer/than/the/width

                indented code
                stays put

            ---
            """
        )
        self.assertEqual(reflow.reflow(text, 20), text)

    def test_hard_breaks_and_setext_headings_are_kept(self) -> None:
        for text in (
            "first line\\\nsecond line\n",
            "first line  \nsecond line\n",
            "first<br>\nsecond line\n",
            "Title words\nmore title\n===\n",
        ):
            with self.subTest(text=text):
                self.assertEqual(reflow.reflow(text, 80), text)

    def test_lines_are_not_joined_across_blocks(self) -> None:
        text = "para text\n- item one\n- item two\n\npara\n# heading\n"
        self.assertEqual(
            reflow.reflow(text, 80),
            "para text\n- item one\n- item two\n\npara\n# heading\n",
        )

    def test_no_line_starts_with_a_block_marker(self) -> None:
        text = "aaaa bbbb cccc - dddd\n"
        result = reflow.reflow(text, 15)
        self.assertEqual(result, "aaaa bbbb\ncccc - dddd\n")
        for line in result.splitlines()[1:]:
            self.assertFalse(line.startswith(("- ", "#", ">", "<")), line)

    def test_autolink_does_not_end_the_paragraph(self) -> None:
        text = "- source:\n  <https://example.com/x>\n"
        self.assertEqual(reflow.reflow(text, 80), "- source: <https://example.com/x>\n")

    def test_code_span_stays_whole_unless_longer_than_a_line(self) -> None:
        self.assertEqual(reflow.reflow("aa `b c d` e\n", 9), "aa\n`b c d` e\n")
        long_span = "run `" + " ".join(["word"] * 8) + "` now\n"
        result = reflow.reflow(long_span, 20)
        self.assertTrue(all(len(line) <= 20 for line in result.splitlines()), result)
        self.assertEqual(" ".join(result.split()), " ".join(long_span.split()))

    def test_reflow_is_idempotent(self) -> None:
        text = "- " + " ".join(f"w{i}" for i in range(60)) + "\n"
        once = reflow.reflow(text, 30)
        self.assertEqual(reflow.reflow(once, 30), once)


class MainTests(unittest.TestCase):
    def run_main(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = reflow.main(list(args))
        return status, out.getvalue(), err.getvalue()

    def test_check_reports_without_writing_and_rewrite_fixes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "doc.md")
            path.write_text("one\ntwo\n", encoding="utf-8")
            status, out, _ = self.run_main("--check", str(path))
            self.assertEqual(
                (status, path.read_text(encoding="utf-8")), (1, "one\ntwo\n")
            )
            self.assertIn("needs reflow", out)
            self.assertEqual(self.run_main(str(path))[0], 0)
            self.assertEqual(path.read_text(encoding="utf-8"), "one two\n")
            self.assertEqual(self.run_main("--check", str(path))[0], 0)

    def test_width_comes_from_nearest_markdownlint_config(self) -> None:
        long_text = " ".join(["word"] * 30) + "\n"
        cli2 = '{\n  // comment\n  "$schema": "https://x/y.json",\n  "config": {"extends": "./base.jsonc"},\n}\n'
        cases = (
            (
                {
                    ".markdownlint-cli2.jsonc": cli2,
                    "base.jsonc": '{"MD013": {"line_length": 40,},}',
                },
                40,
                "",
            ),
            ({".markdownlint.json": '{"MD013": true}'}, 80, ""),
            ({".markdownlint.json": '{"default": true}'}, 80, ""),
            ({".markdownlint.json": '{"line-length": false}'}, 100, ""),
            (
                {".markdownlint.yaml": "MD013:\n  line_length: 40\n"},
                100,
                "pass --width",
            ),
            ({}, 100, ""),
        )
        for files, width, note in cases:
            with self.subTest(files=files), tempfile.TemporaryDirectory() as directory:
                for name, content in files.items():
                    Path(directory, name).write_text(content, encoding="utf-8")
                path = Path(directory, "docs", "doc.md")
                path.parent.mkdir()
                path.write_text(long_text, encoding="utf-8")
                status, _, err = self.run_main(str(path))
                self.assertEqual(status, 0)
                lines = path.read_text(encoding="utf-8").splitlines()
                self.assertTrue(all(len(line) <= width for line in lines), lines)
                self.assertGreater(len(lines[0]), width - 5)
                self.assertIn(note, err)

    def test_explicit_width_overrides_config(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, ".markdownlint.json").write_text(
                '{"MD013": true}', encoding="utf-8"
            )
            path = Path(directory, "doc.md")
            path.write_text(" ".join(["word"] * 30) + "\n", encoding="utf-8")
            self.assertEqual(self.run_main("--width", "30", str(path))[0], 0)
            self.assertTrue(
                all(len(line) <= 30 for line in path.read_text().splitlines())
            )

    def test_unparsable_config_is_bad_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            Path(directory, ".markdownlint.json").write_text("{nope", encoding="utf-8")
            path = Path(directory, "doc.md")
            path.write_text("one\ntwo\n", encoding="utf-8")
            status, _, err = self.run_main(str(path))
            self.assertEqual(
                (status, path.read_text(encoding="utf-8")), (2, "one\ntwo\n")
            )
            self.assertIn(".markdownlint.json:", err)

    def test_missing_file_is_bad_input_and_others_still_run(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "doc.md")
            path.write_text("one\ntwo\n", encoding="utf-8")
            status, _, err = self.run_main(str(Path(directory, "absent.md")), str(path))
            self.assertEqual(status, 2)
            self.assertIn("absent.md", err)
            self.assertEqual(path.read_text(encoding="utf-8"), "one two\n")


if __name__ == "__main__":
    unittest.main()
