"""Tests for line_count.py and file_length.py (stdlib only; run directly)."""

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

import file_length
import line_count


def count(name: str, source: str) -> int | None:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / name
        path.write_text(textwrap.dedent(source))
        return line_count.count_code_lines(path)


def run(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        status = file_length.main(argv)
    return status, out.getvalue()


class LineCountTests(unittest.TestCase):
    def test_c_comments_and_blank_lines_do_not_count(self) -> None:
        source = """\
            int a; // trailing comment keeps the line

            /* block
               comment */
            int b; /* inline */
            // whole-line comment
            """
        self.assertEqual(count("a.c", source), 2)

    def test_comment_markers_inside_strings_are_code(self) -> None:
        source = 'const u = "http://x/*";\nconst v = 1;\n'
        self.assertEqual(count("a.ts", source), 2)

    def test_multiline_template_literal_lines_count(self) -> None:
        source = "const s = `\n// not a comment\n`;\n"
        self.assertEqual(count("a.js", source), 3)

    def test_rust_nested_comments_lifetimes_and_char_literals(self) -> None:
        source = """\
            /* outer /* inner */ still comment */
            fn f<'a>(x: &'a str) -> char { '"' } // quote char
            // done
            """
        self.assertEqual(count("a.rs", source), 1)

    def test_python_comments_and_docstrings_do_not_count(self) -> None:
        source = '''\
            """Module docstring.

            More text.
            """
            # comment
            def f():
                """Function docstring."""
                text = """
                data
                """
                return text
            '''
        self.assertEqual(count("a.py", source), 5)

    def test_python_one_line_def_with_docstring_counts(self) -> None:
        self.assertEqual(count("a.py", 'def f(): "doc"\n'), 1)

    def test_python_that_does_not_parse_falls_back_to_lexer(self) -> None:
        self.assertEqual(count("a.py", "print 'x'  # py2\n# c\n"), 1)

    def test_lua_block_comment_and_long_string(self) -> None:
        source = "--[[ block\ncomment ]]\nlocal s = [[\n-- kept\n]]\n"
        self.assertEqual(count("a.lua", source), 3)

    def test_hash_languages(self) -> None:
        self.assertEqual(count("a.sh", 'echo "#x" # c\n# only\n'), 1)

    def test_unknown_suffix_returns_none(self) -> None:
        self.assertIsNone(count("notes.txt", "hello\n"))


class ClassificationTests(unittest.TestCase):
    def test_test_paths(self) -> None:
        for name in [
            "tests/helpers.py",
            "pkg/__tests__/a.js",
            "test_parser.py",
            "parser_test.go",
            "parser.test.ts",
            "parser.spec.js",
            "parser_spec.rb",
            "ParserTest.java",
            "ParserTests.cs",
            "ParserSpec.scala",
            "conftest.py",
        ]:
            self.assertTrue(file_length.is_test(Path(name), []), name)

    def test_code_paths(self) -> None:
        for name in ["src/parser.py", "latest.go", "Contest.java", "testing.py"]:
            self.assertFalse(file_length.is_test(Path(name), []), name)

    def test_extra_glob(self) -> None:
        self.assertTrue(file_length.is_test(Path("qa/check.py"), ["qa/*"]))


class CommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "big.py").write_text("x = 1\n" * 4)
        (self.root / "test_big.py").write_text("x = 1\n" * 4)
        (self.root / "notes.txt").write_text("text\n")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_code_limit_and_test_limit_differ(self) -> None:
        status, out = run([str(self.root), "--max-code", "3", "--max-test", "4"])
        self.assertEqual(status, 1)
        self.assertIn("big.py: 4 lines (code, limit 3, over)", out)
        self.assertNotIn("test_big.py", out)
        self.assertIn("skipped: 1 files", out)

    def test_within_limits_exits_zero(self) -> None:
        status, _ = run([str(self.root)])
        self.assertEqual(status, 0)

    def test_exclude_glob(self) -> None:
        status, _ = run([str(self.root), "--max-code", "3", "--exclude", "*/big.py"])
        self.assertEqual(status, 0)

    def test_json_report(self) -> None:
        _, out = run([str(self.root), "--json"])
        report = json.loads(out)
        self.assertEqual(report["summary"]["code"]["lines"], 4)
        self.assertEqual(report["summary"]["test"]["files"], 1)
        self.assertEqual(len(report["skipped"]), 1)

    def test_missing_path_exits_two(self) -> None:
        status, _ = run([str(self.root / "missing")])
        self.assertEqual(status, 2)


if __name__ == "__main__":
    unittest.main()
