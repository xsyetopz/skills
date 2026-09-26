"""Tests for check_queries.py (stdlib only; run directly)."""

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

import check_queries

NODE_TYPES = [
    {
        "type": "rule",
        "named": True,
        "fields": {"target": {"types": []}},
    },
    {"type": "targets", "named": True},
    {"type": "word", "named": True},
    {"type": "comment", "named": True},
    {"type": "shell_text", "named": True},
    {"type": "(", "named": False},
    {"type": ")", "named": False},
]


def run(files: dict[str, str], node_types: bool = True) -> tuple[int, str]:
    root = Path(tempfile.mkdtemp())
    for name, text in files.items():
        (root / name).write_text(text, encoding="utf-8")
    argv = [str(root)]
    if node_types:
        types = root / "node-types.json"
        types.write_text(json.dumps(NODE_TYPES), encoding="utf-8")
        argv += ["--node-types", str(types)]
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        status = check_queries.main(argv)
    return status, out.getvalue()


class QueryTests(unittest.TestCase):
    def test_valid_files_pass(self) -> None:
        status, output = run(
            {
                "highlights.scm": "(comment) @comment\n(word) @property.key\n",
                "brackets.scm": '("(" @open ")" @close)\n',
                "outline.scm": "((rule (targets) @name) @item\n"
                '  (#not-match? @name "^\\\\."))\n',
                "injections.scm": "((shell_text) @injection.content\n"
                '  (#set! injection.language "bash"))\n',
            }
        )
        self.assertEqual(status, 0, output)
        self.assertIn("0 errors, 0 warnings", output)

    def test_unbalanced_parenthesis_is_an_error(self) -> None:
        status, output = run({"highlights.scm": "(comment @comment\n"})
        self.assertEqual(status, 1)
        self.assertIn("unclosed '('", output)

    def test_parenthesis_inside_string_is_ignored(self) -> None:
        status, output = run({"brackets.scm": '("(" @open ")" @close)\n'})
        self.assertEqual(status, 0, output)

    def test_unknown_node_and_field_are_errors(self) -> None:
        status, output = run(
            {"highlights.scm": "(rule name: (identifier) @function)\n"}
        )
        self.assertEqual(status, 1)
        self.assertIn("no field `name`", output)
        self.assertIn("no named node `identifier`", output)

    def test_missing_required_outline_capture(self) -> None:
        status, output = run({"outline.scm": "(rule (targets) @title) @item\n"})
        self.assertEqual(status, 1)
        self.assertIn("missing required @name", output)
        self.assertIn("@title is not read", output)

    def test_injection_needs_content(self) -> None:
        status, output = run(
            {"injections.scm": '((word) @x (#set! injection.language "c"))\n'},
            node_types=False,
        )
        self.assertEqual(status, 1)
        self.assertIn("needs @injection.content", output)

    def test_indent_start_suffix_is_allowed(self) -> None:
        status, output = run({"indents.scm": "(rule) @indent\n(rule) @start.rule\n"})
        self.assertEqual(status, 0, output)

    def test_unknown_highlight_is_a_warning(self) -> None:
        status, output = run({"highlights.scm": "(word) @storageclass\n"})
        self.assertEqual(status, 0)
        self.assertIn("WARN", output)

    def test_unreadable_node_types_is_a_usage_error(self) -> None:
        root = Path(tempfile.mkdtemp())
        (root / "highlights.scm").write_text("(word) @string\n", encoding="utf-8")
        (root / "bad.json").write_text("{not json", encoding="utf-8")
        for types in (root / "missing.json", root / "bad.json"):
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                status = check_queries.main([str(root), "--node-types", str(types)])
            self.assertEqual(status, 2)
            self.assertIn("cannot read --node-types", err.getvalue())

    def test_underscore_captures_are_private(self) -> None:
        status, output = run({"brackets.scm": '("(" @open ")" @close) @_pair\n'})
        self.assertEqual(status, 0, output)
        self.assertNotIn("WARN", output)


if __name__ == "__main__":
    unittest.main()
