"""Tests for check_instructions.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_instructions as ci


def run(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        status = ci.main(list(argv))
    return status, out.getvalue()


class ScanTests(unittest.TestCase):
    def test_extracts_fenced_and_inline_commands(self) -> None:
        text = (
            "Run `just test` before committing.\n"
            "```sh\n# comment\n$ bun install --frozen-lockfile\nuv run pytest\n```\n"
            "```python\nprint('not a command')\n```\n"
        )
        _, commands = ci.scan(text)
        self.assertEqual(
            commands, ["just test", "bun install --frozen-lockfile", "uv run pytest"]
        )


class FileTests(unittest.TestCase):
    def test_imports_resolve_and_code_spans_are_literal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text("# Rules\n\nUse Bun.\n")
            (root / "CLAUDE.md").write_text(
                "@AGENTS.md\n\nMention `@missing.md` literally.\n"
            )
            status, output = run(str(root / "CLAUDE.md"))
            self.assertEqual(status, 0, output)

    def test_missing_import_and_link_are_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CLAUDE.md"
            path.write_text("@docs/missing.md\n\nSee [guide](docs/guide.md).\n")
            status, output = run(str(path))
            self.assertEqual(status, 1)
            self.assertIn("missing @import docs/missing.md", output)
            self.assertIn("missing link target docs/guide.md", output)

    def test_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text("Run `just test`.\n\nSee [guide](docs/guide.md).\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = ci.main([str(path), "--json"])
        report = json.loads(out.getvalue())
        self.assertEqual((status, report["errors"]), (1, 1))
        (entry,) = report["files"]
        self.assertEqual(entry["file"], str(path))
        self.assertEqual(entry["commands"], ["just test"])
        self.assertEqual(len(entry["errors"]), 1)
        self.assertIn("docs/guide.md", entry["errors"][0])

    def test_non_utf8_file_is_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_bytes(b"\xff\xfe bad")
            status, output = run(str(path))
        self.assertEqual(status, 2)
        self.assertIn("cannot read", output)

    def test_generic_phrases_and_size_are_warnings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text("Follow best practices.\n" + "x\n" * 250)
            status, output = run(str(path))
            self.assertEqual(status, 0)
            self.assertIn("generic phrase 'best practices'", output)
            self.assertIn("200-line target", output)

    def test_import_hop_limit(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for n in range(6):
                (root / f"f{n}.md").write_text(f"@f{n + 1}.md\n")
            (root / "f6.md").write_text("end\n")
            status, output = run(str(root / "f0.md"))
            self.assertEqual(status, 1)
            self.assertIn("exceeds four hops", output)

    def test_commands_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "AGENTS.md"
            path.write_text("```sh\njust test\njust test\n```\n")
            status, output = run(str(path), "--commands")
            self.assertEqual((status, output.strip()), (0, "just test"))

    def test_missing_file_is_input_error(self) -> None:
        self.assertEqual(run("/nonexistent/AGENTS.md")[0], 2)


if __name__ == "__main__":
    unittest.main()
