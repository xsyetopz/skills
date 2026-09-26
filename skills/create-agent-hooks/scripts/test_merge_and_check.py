"""Tests for merge_hooks.py and check_hook_config.py (stdlib only)."""

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

import check_hook_config as chc
import merge_hooks

HANDLER = {"type": "command", "command": "python3 guard.py", "timeout": 10}
EXISTING = {
    "permissions": {"deny": ["Bash(curl:*)"]},
    "hooks": {
        "PreToolUse": [
            {"matcher": "Edit", "hooks": [{"type": "command", "command": "fmt"}]}
        ]
    },
}


def merge(path: Path, *extra: str) -> int:
    with (
        contextlib.redirect_stdout(io.StringIO()),
        contextlib.redirect_stderr(io.StringIO()),
    ):
        return merge_hooks.main(
            [
                str(path),
                "--event",
                "PreToolUse",
                "--handler",
                json.dumps(HANDLER),
                *extra,
            ]
        )


class MergeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "settings.json"
        self.original = json.dumps(EXISTING, indent=2) + "\n"
        self.path.write_text(self.original)

    def test_add_keeps_other_settings_and_groups(self) -> None:
        self.assertEqual(merge(self.path, "--host", "claude", "--matcher", "Bash"), 0)
        config = json.loads(self.path.read_text())
        self.assertEqual(config["permissions"], EXISTING["permissions"])
        groups = config["hooks"]["PreToolUse"]
        self.assertEqual([g["matcher"] for g in groups], ["Edit", "Bash"])

    def test_add_twice_is_a_no_op(self) -> None:
        merge(self.path, "--host", "claude", "--matcher", "Bash")
        once = self.path.read_text()
        merge(self.path, "--host", "claude", "--matcher", "Bash")
        self.assertEqual(self.path.read_text(), once)

    def test_remove_restores_the_original_content(self) -> None:
        merge(self.path, "--host", "claude", "--matcher", "Bash")
        self.assertEqual(
            merge(self.path, "--host", "claude", "--matcher", "Bash", "--remove"), 0
        )
        self.assertEqual(json.loads(self.path.read_text()), EXISTING)

    def test_remove_from_file_without_hooks_restores_it(self) -> None:
        path = self.dir / "plain.json"
        path.write_text('{"model": "x"}\n')
        merge(path, "--host", "claude", "--matcher", "Bash")
        merge(path, "--host", "claude", "--matcher", "Bash", "--remove")
        self.assertEqual(json.loads(path.read_text()), {"model": "x"})

    def test_remove_of_absent_entry_fails(self) -> None:
        status = merge(self.path, "--host", "claude", "--matcher", "Bash", "--remove")
        self.assertEqual(status, 1)
        self.assertEqual(self.path.read_text(), self.original)

    def test_dry_run_leaves_file_unchanged(self) -> None:
        merge(self.path, "--host", "claude", "--matcher", "Bash", "--dry-run")
        self.assertEqual(self.path.read_text(), self.original)

    def test_flat_host_puts_matcher_in_entry_and_adds_version(self) -> None:
        path = self.dir / "hooks.json"
        merge(path, "--host", "cursor", "--matcher", "Shell")
        config = json.loads(path.read_text())
        self.assertEqual(config["version"], 1)
        self.assertEqual(config["hooks"]["PreToolUse"][0]["matcher"], "Shell")


class CheckTests(unittest.TestCase):
    def messages(self, config: dict, host: str) -> list[str]:
        return [m for _, m in chc.check(config, host, None)]

    def test_wrong_case_event_gets_a_hint(self) -> None:
        config = {"version": 1, "hooks": {"PreToolUse": [{"command": "x"}]}}
        self.assertIn(
            "PreToolUse: unknown cursor event (did you mean preToolUse?)",
            self.messages(config, "cursor"),
        )

    def test_event_from_another_host_is_unknown(self) -> None:
        config = {"hooks": {"BeforeTool": [{"hooks": [HANDLER]}]}}
        self.assertIn("BeforeTool: unknown codex event", self.messages(config, "codex"))

    def test_codex_ignores_stop_matcher_and_skips_prompt(self) -> None:
        handler = {"type": "prompt", "prompt": "check"}
        config = {"hooks": {"Stop": [{"matcher": "x", "hooks": [handler]}]}}
        found = self.messages(config, "codex")
        self.assertIn("Stop: codex ignores matcher on this event", found)
        self.assertIn("Stop: codex parses prompt handlers but skips them", found)

    def test_codex_session_end_timeout_limit(self) -> None:
        handler = dict(HANDLER, timeout=10)
        config = {"hooks": {"SessionEnd": [{"hooks": [handler]}]}}
        self.assertIn(
            "SessionEnd: codex allows at most 3 s for SessionEnd",
            self.messages(config, "codex"),
        )

    def test_gemini_lifecycle_matcher_and_millisecond_timeout(self) -> None:
        handler = {"type": "command", "command": "a", "timeout": 5}
        config = {
            "hooks": {
                "SessionStart": [{"matcher": "startup|resume", "hooks": [handler]}]
            }
        }
        found = self.messages(config, "gemini")
        self.assertIn(
            "SessionStart: exact-string matcher 'startup|resume' never matches",
            found,
        )
        self.assertIn("SessionStart: gemini timeout is milliseconds; 5 ms", found)

    def test_invalid_regex(self) -> None:
        config = {"hooks": {"PreToolUse": [{"matcher": "(", "hooks": [HANDLER]}]}}
        self.assertTrue(
            any("is not a regex" in m for m in self.messages(config, "claude"))
        )

    def test_missing_script_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            handler = {
                "type": "command",
                "command": "python3",
                "args": ["${CLAUDE_PROJECT_DIR}/.agent-hooks/missing.py"],
            }
            config = {"hooks": {"PreToolUse": [{"hooks": [handler]}]}}
            found = [m for _, m in chc.check(config, "claude", Path(tmp))]
        self.assertTrue(any("script not found" in m for m in found), found)


class InterfaceTests(unittest.TestCase):
    """--json, --dry-run, malformed layouts, and --help for both scripts."""

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.dir = Path(temp.name)
        self.path = self.dir / "settings.json"
        self.path.write_text(json.dumps(EXISTING, indent=2) + "\n")

    def call(self, module, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = module.main(list(argv))
        return status, out.getvalue(), err.getvalue()

    def merge_json(self, path: Path, *extra: str) -> tuple[int, dict]:
        status, out, _ = self.call(
            merge_hooks,
            str(path),
            "--host",
            "claude",
            "--event",
            "PreToolUse",
            "--matcher",
            "Bash",
            "--handler",
            json.dumps(HANDLER),
            "--json",
            *extra,
        )
        return status, json.loads(out) if out else {}

    def test_json_dry_run_reports_change_without_writing(self) -> None:
        before = self.path.read_text()
        status, report = self.merge_json(self.path, "--dry-run")
        self.assertEqual(status, 0)
        self.assertEqual((report["changed"], report["written"]), (True, False))
        self.assertIn('"Bash"', report["diff"])
        self.assertEqual(self.path.read_text(), before)

    def test_dry_run_on_missing_file_creates_nothing(self) -> None:
        target = self.dir / "new" / ".claude" / "settings.json"
        status, report = self.merge_json(target, "--dry-run")
        self.assertEqual((status, report["written"]), (0, False))
        self.assertFalse(target.parent.exists())

    def test_json_add_then_repeat_then_remove(self) -> None:
        status, first = self.merge_json(self.path)
        self.assertEqual((status, first["changed"], first["written"]), (0, True, True))
        status, again = self.merge_json(self.path)
        self.assertEqual((status, again["changed"], again["diff"]), (0, False, ""))
        status, removed = self.merge_json(self.path, "--remove")
        self.assertEqual(
            (status, removed["action"], removed["changed"]), (0, "remove", True)
        )
        self.assertEqual(json.loads(self.path.read_text()), EXISTING)
        status, missing = self.merge_json(self.path, "--remove")
        self.assertEqual((status, missing["changed"]), (1, False))

    def test_malformed_layouts_are_exit_2_and_untouched(self) -> None:
        layouts = {
            '"hooks" must be an object': {"hooks": []},
            "hooks.PreToolUse must be a list": {"hooks": {"PreToolUse": {}}},
            "hooks.PreToolUse[0] must be an object": {"hooks": {"PreToolUse": ["x"]}},
            "hooks.PreToolUse[0].hooks must be a list": {
                "hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": {}}]}
            },
        }
        for expected, config in layouts.items():
            with self.subTest(expected=expected):
                text = json.dumps(config)
                self.path.write_text(text)
                status, out, err = self.call(
                    merge_hooks,
                    str(self.path),
                    "--host",
                    "claude",
                    "--event",
                    "PreToolUse",
                    "--matcher",
                    "Bash",
                    "--handler",
                    json.dumps(HANDLER),
                )
                self.assertEqual((status, out), (2, ""))
                self.assertIn(expected, err)
                self.assertEqual(self.path.read_text(), text)

    def test_other_matcher_groups_are_not_validated(self) -> None:
        config = {
            "hooks": {"PreToolUse": [{"matcher": "Edit", "hooks": {}}]},
        }
        self.path.write_text(json.dumps(config))
        status, report = self.merge_json(self.path)
        self.assertEqual((status, report["changed"]), (0, True))
        groups = json.loads(self.path.read_text())["hooks"]["PreToolUse"]
        self.assertEqual(groups[0], {"matcher": "Edit", "hooks": {}})
        self.assertEqual(groups[1], {"matcher": "Bash", "hooks": [HANDLER]})

    def test_flat_host_rejects_non_list_event(self) -> None:
        self.path.write_text('{"version": 1, "hooks": {"stop": {}}}')
        status, _, err = self.call(
            merge_hooks,
            str(self.path),
            "--host",
            "cursor",
            "--event",
            "stop",
            "--handler",
            '{"command": "x"}',
            "--remove",
        )
        self.assertEqual(status, 2)
        self.assertIn("hooks.stop must be a list", err)

    def test_bad_handler_json_names_the_flag(self) -> None:
        status, _, err = self.call(
            merge_hooks,
            str(self.path),
            "--host",
            "claude",
            "--event",
            "Stop",
            "--handler",
            "not json",
        )
        self.assertEqual(status, 2)
        self.assertIn("--handler", err)

    def test_check_non_string_matcher_is_an_error_not_a_crash(self) -> None:
        config = {"hooks": {"PreToolUse": [{"matcher": 5, "hooks": [HANDLER]}]}}
        self.assertIn(
            ("error", "PreToolUse: matcher must be a string, got 5"),
            chc.check(config, "claude", None),
        )

    def test_check_unhashable_handler_type_is_an_error(self) -> None:
        handler = {"type": ["command"], "command": "x"}
        config = {"hooks": {"PreToolUse": [{"hooks": [handler]}]}}
        severities = [s for s, _ in chc.check(config, "claude", None)]
        self.assertEqual(severities, ["error"])

    def test_check_non_object_entry_names_its_position(self) -> None:
        self.path.write_text('{"hooks": {"PreToolUse": [{"hooks": ["x"]}]}}')
        status, out, err = self.call(chc, str(self.path), "--host", "claude")
        self.assertEqual((status, out), (2, ""))
        self.assertIn("hooks.PreToolUse[0].hooks[0] must be an object", err)

    def test_help_documents_exit_status(self) -> None:
        for module in (merge_hooks, chc):
            with self.subTest(module=module.__name__):
                out = io.StringIO()
                with (
                    contextlib.redirect_stdout(out),
                    self.assertRaises(SystemExit) as caught,
                ):
                    module.main(["--help"])
                self.assertEqual(caught.exception.code, 0)
                self.assertIn("Exit status:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
