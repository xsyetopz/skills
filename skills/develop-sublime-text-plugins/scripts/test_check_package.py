"""Tests for check_package.py. Run: python test_check_package.py"""

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_package  # noqa: E402

EXAMPLE = HERE.parent / "assets" / "examples" / "TodoLens"

PLUGIN = """\
import sublime
import sublime_plugin

sublime.load_settings("X.sublime-settings")
VERSION = sublime.version()


class ShowHTMLCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        pass


class PickCommand(sublime_plugin.WindowCommand):
    def input(self, args):
        return None

    def run(self, item):
        sublime.status_message(item)
"""


class CheckPackageTest(unittest.TestCase):
    def make(self, files, name="Pkg"):
        temp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp)
        root = Path(temp) / name
        root.mkdir()
        for rel, text in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        return root

    def test_bundled_example_is_clean(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = check_package.main([str(EXAMPLE), "--external", "edit_settings"])
        self.assertEqual(out.getvalue(), "0 issue(s) in TodoLens\n")
        self.assertEqual(status, 0)

    def test_json_report(self):
        root = self.make({".python-version": "3.8\n", "x.py": PLUGIN}, name="Pkg")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = check_package.main([str(root), "--json"])
        report = json.loads(out.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(report["package"], "Pkg")
        self.assertEqual(report["count"], len(report["issues"]))
        self.assertIn(
            {
                "file": "x.py",
                "line": 4,
                "message": "sublime.load_settings() at import time; "
                "move it into plugin_loaded()",
            },
            report["issues"],
        )
        capitals = [
            i for i in report["issues"] if "consecutive capitals" in i["message"]
        ]
        self.assertEqual((capitals[0]["file"], capitals[0]["line"]), ("x.py", None))

    def test_input_errors_exit_2(self):
        broken = self.make({".python-version": "3.8\n", "x.py": "def (:\n"})
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(check_package.main([str(broken)]), 2)
            self.assertEqual(check_package.main([str(broken / "missing")]), 2)
        self.assertIn("cannot parse", err.getvalue())
        self.assertIn("is not a directory", err.getvalue())

    def test_every_rule_reports(self):
        root = self.make(
            {
                "plugin.py": PLUGIN,
                "__init__.py": "",
                "package-metadata.json": "{}",
                "Default.sublime-keymap": (
                    '[ // bindings\n  {"keys": ["f1"], "command": "show_html"},'
                    '\n  {"keys": ["f2"], "command": "missing_cmd"},\n]'
                ),
                "Main.sublime-menu": '[{"children": [{"command": "pick"}]}]',
                "Bad.sublime-settings": "{ nope }",
            },
            name="My.Pkg",
        )
        issues = check_package.check(root, external=set())
        text = "\n".join(issues)
        for fragment in (
            "package name contains '.'",
            ".python-version: missing",
            "package-metadata.json: generated",
            "__init__.py: packages must not",
            "ShowHTMLCommand has consecutive capitals",
            "plugin.py:4: sublime.load_settings() at import time",
            "Bad.sublime-settings: does not parse",
            "command 'missing_cmd' is not defined",
            # documented rule maps ShowHTMLCommand to show_h_t_m_l
            "command 'show_html' is not defined",
            "PickCommand: input() needs a .sublime-commands entry",
        ):
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)
        self.assertNotIn("sublime.version()", text)  # import-time safe
        self.assertNotIn("status_message", text)  # inside a method
        self.assertEqual(len(issues), 10)

    def test_external_and_comment_tolerance(self):
        root = self.make(
            {
                ".python-version": "3.8\n",
                "Default.sublime-commands": (
                    '[\n  /* palette */\n  {"caption": "a // not comment",'
                    ' "command": "edit_settings",},\n]'
                ),
            }
        )
        self.assertEqual(check_package.check(root, external={"edit_settings"}), [])
        self.assertEqual(len(check_package.check(root, external=set())), 1)

    def test_command_name_rule(self):
        self.assertEqual(
            check_package.command_name("TodoLensMarkDoneCommand"),
            "todo_lens_mark_done",
        )
        self.assertEqual(check_package.command_name("Example"), "example")


if __name__ == "__main__":
    unittest.main()
