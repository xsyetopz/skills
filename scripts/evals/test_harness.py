"""Tests for stream-json parsing, settings generation, and the model guard."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

import harness

# Trimmed from a real Claude Code 2.1.283 `-p --output-format stream-json --verbose`
# trigger run (see scripts/evals/trigger_eval.py); field values shortened.
INIT = {
    "type": "system",
    "subtype": "init",
    "cwd": "/tmp/skill-trigger-optimize-go-code-x",
    "session_id": "s",
    "tools": ["Task", "Bash", "Read", "Skill", "Write"],
    "mcp_servers": [],
    "model": "claude-opus-5-5",
    "permissionMode": "dontAsk",
    "skills": ["optimize-go-code", "write-justfiles"],
    "plugins": [],
    "claude_code_version": "2.1.283",
}
USAGE = {
    "input_tokens": 2,
    "cache_creation_input_tokens": 25615,
    "cache_read_input_tokens": 0,
    "output_tokens": 4,
    "service_tier": "standard",
}
THINKING = {
    "type": "assistant",
    "message": {
        "id": "msg_1",
        "model": "claude-opus-5-5",
        "role": "assistant",
        "content": [{"type": "thinking", "thinking": "", "signature": "x"}],
        "usage": USAGE,
    },
    "parent_tool_use_id": None,
    "session_id": "s",
}
SKILL_CALL = {
    "type": "assistant",
    "message": {
        "id": "msg_1",
        "model": "claude-opus-5-5",
        "role": "assistant",
        "content": [
            {
                "type": "tool_use",
                "id": "toolu_1",
                "name": "Skill",
                "input": {"skill": "optimize-go-code", "args": "p99 latency doubled"},
            }
        ],
        "usage": USAGE,
    },
    "parent_tool_use_id": None,
    "session_id": "s",
}
RESULT = {
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "duration_ms": 23332,
    "num_turns": 3,
    "result": "Done.",
    "total_cost_usd": 0.5,
    "usage": {**USAGE, "cache_read_input_tokens": 1000, "output_tokens": 800},
    "modelUsage": {"claude-opus-5-5": {"inputTokens": 2}},
}


def call(name: str, message_id: str) -> dict:
    """A top-level assistant event holding one tool_use block."""
    event = json.loads(json.dumps(SKILL_CALL))
    event["message"]["id"] = message_id
    event["message"]["content"] = [
        {"type": "tool_use", "id": f"toolu_{name}", "name": name, "input": {}}
    ]
    return event


def lines(*events: dict) -> list[str]:
    return [json.dumps(e) + "\n" for e in events]


class StreamTests(unittest.TestCase):
    def test_first_tool_is_skill_call(self) -> None:
        events = harness.parse_stream(
            ["noise\n", *lines(INIT, THINKING, SKILL_CALL), "{bad json\n"]
        )
        self.assertEqual(len(events), 3)
        prefix, tool = harness.tool_prefix(events)
        self.assertEqual(prefix, ["Skill"])
        self.assertEqual(harness.skill_of(tool), "optimize-go-code")
        self.assertEqual(harness.init_event(events), INIT)

    def test_meta_tools_are_read_past(self) -> None:
        events = [
            INIT,
            call("ToolSearch", "msg_1"),
            call("TaskCreate", "msg_2"),
            SKILL_CALL,
            call("Bash", "msg_3"),
        ]
        prefix, tool = harness.tool_prefix(events)
        self.assertEqual(prefix, ["ToolSearch", "TaskCreate", "Skill"])
        self.assertEqual(harness.skill_of(tool), "optimize-go-code")

    def test_meta_then_other_tool_is_decisive(self) -> None:
        prefix, tool = harness.tool_prefix(
            [call("TodoWrite", "msg_1"), call("Bash", "msg_2"), SKILL_CALL]
        )
        self.assertEqual(prefix, ["TodoWrite", "Bash"])
        self.assertEqual(tool and tool["name"], "Bash")
        self.assertIsNone(harness.skill_of(tool))

    def test_subagent_task_tool_is_not_meta(self) -> None:
        prefix, tool = harness.tool_prefix([call("Task", "msg_1"), SKILL_CALL])
        self.assertEqual(prefix, ["Task"])
        self.assertEqual(tool and tool["name"], "Task")

    def test_blocks_within_one_message(self) -> None:
        both = call("TaskList", "msg_1")
        both["message"]["content"].append(SKILL_CALL["message"]["content"][0])
        prefix, tool = harness.tool_prefix([both])
        self.assertEqual(prefix, ["TaskList", "Skill"])
        self.assertEqual(harness.skill_of(tool), "optimize-go-code")

    def test_no_decisive_tool(self) -> None:
        self.assertEqual(
            harness.tool_prefix(harness.parse_stream(lines(INIT, THINKING, RESULT))),
            ([], None),
        )
        self.assertEqual(
            harness.tool_prefix([call("ToolSearch", "msg_1")]), (["ToolSearch"], None)
        )

    def test_subagent_tool_calls_are_ignored(self) -> None:
        nested = {**SKILL_CALL, "parent_tool_use_id": "toolu_parent"}
        self.assertEqual(harness.tool_prefix([nested]), ([], None))

    def test_namespaced_skill_name_is_stripped(self) -> None:
        self.assertEqual(
            harness.skill_of({"name": "Skill", "input": {"skill": "plug:deploy"}}),
            "deploy",
        )

    def test_usage_from_result_event(self) -> None:
        usage = harness.stream_usage(
            harness.parse_stream(lines(INIT, SKILL_CALL, RESULT))
        )
        self.assertFalse(usage["partial"])
        self.assertEqual(usage["total_tokens"], 2 + 25615 + 1000 + 800)
        self.assertEqual(usage["total_cost_usd"], 0.5)

    def test_partial_usage_counts_each_message_once(self) -> None:
        usage = harness.stream_usage([INIT, THINKING, SKILL_CALL])
        self.assertTrue(usage["partial"])
        self.assertEqual(usage["total_tokens"], 2 + 25615 + 4)

    def test_first_request_usage_ignores_later_requests(self) -> None:
        later = call("Bash", "msg_2")
        later["message"]["usage"] = {**USAGE, "cache_read_input_tokens": 25615}
        subagent = {**later, "parent_tool_use_id": "toolu_parent"}
        first = harness.first_request_usage(
            [INIT, subagent, THINKING, SKILL_CALL, later]
        )
        self.assertEqual(first and first["cache_creation_input_tokens"], 25615)
        self.assertEqual(first and first["cache_read_input_tokens"], 0)
        self.assertIsNone(harness.first_request_usage([INIT]))

    def test_final_text_prefers_result(self) -> None:
        self.assertEqual(harness.final_text([SKILL_CALL, RESULT]), "Done.")
        reply = {
            "type": "assistant",
            "message": {"content": [{"type": "text", "text": "partial"}]},
        }
        self.assertEqual(harness.final_text([reply]), "partial")

    def test_models_and_violations(self) -> None:
        haiku = {
            "type": "assistant",
            "message": {"model": "claude-haiku-4-5", "content": []},
        }
        models = harness.models_used([SKILL_CALL, haiku, RESULT])
        self.assertEqual(models, ["claude-haiku-4-5", "claude-opus-5-5"])
        self.assertEqual(
            harness.model_violations(models, "claude-opus-5-5"), ["claude-haiku-4-5"]
        )
        self.assertEqual(
            harness.model_violations(["claude-opus-5-5[1m]"], "claude-opus-5-5"), []
        )


class SettingsTests(unittest.TestCase):
    def test_model_and_effort_guard(self) -> None:
        harness.check_model_effort("claude-fable-5-1", "medium")
        for model, effort in (
            ("claude-sonnet-5", "high"),
            ("claude-haiku-4-5", "high"),
            ("claude-opus-5-5", "max"),
        ):
            with self.assertRaises(harness.UsageError):
                harness.check_model_effort(model, effort)

    def test_personal_and_synced_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            for rel in ("skills/mine", "skills/synced/bucket/pdf", "skills/.trash/old"):
                (home / rel).mkdir(parents=True)
                (home / rel / "SKILL.md").write_text("---\nname: x\n---\n")
            (home / "skills/not-a-skill").mkdir()
            self.assertEqual(harness.personal_skill_names(home), ["mine", "pdf"])
            self.assertEqual(harness.personal_skill_names(home / "missing"), [])

    def test_plugin_ids_from_settings_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            user = root / "settings.json"
            user.write_text(
                json.dumps({"enabledPlugins": {"a@m": True, "off@m": False}})
            )
            manifest = root / "installed_plugins.json"
            manifest.write_text(json.dumps({"version": 2, "plugins": {"b@m": []}}))
            self.assertEqual(
                harness.plugin_ids([user, root / "absent.json"], manifest),
                ["a@m", "b@m"],
            )

    def test_build_settings(self) -> None:
        settings = harness.build_settings(
            "claude-opus-5-5", ["pdf", "mine", "pdf"], ["a@m"]
        )
        self.assertIs(settings["disableBundledSkills"], True)
        self.assertIs(settings["disableAllHooks"], True)
        self.assertEqual(settings["skillOverrides"], {"mine": "off", "pdf": "off"})
        self.assertEqual(settings["enabledPlugins"], {"a@m": False})
        self.assertEqual(
            settings["env"]["ANTHROPIC_DEFAULT_HAIKU_MODEL"], "claude-opus-5-5"
        )
        self.assertEqual(settings["env"]["ENABLE_CLAUDEAI_MCP_SERVERS"], "false")

    def test_sandbox_denies_network_unless_opted_in(self) -> None:
        closed = harness.sandbox_settings(network=False)
        sandbox = closed["sandbox"]
        self.assertIs(sandbox["enabled"], True)
        self.assertIs(sandbox["failIfUnavailable"], True)
        self.assertIs(sandbox["allowUnsandboxedCommands"], False)
        self.assertEqual(
            sandbox["network"], {"strictAllowlist": True, "allowedDomains": []}
        )
        for rule in (
            "Bash(git push *)",
            "Bash(gh *)",
            "Bash(dropdb *)",
            "Bash(curl *)",
        ):
            self.assertIn(rule, closed["permissions"]["deny"])
        self.assertIn("Bash", closed["permissions"]["allow"])
        opened = harness.sandbox_settings(network=True)
        self.assertEqual(opened["sandbox"], sandbox)
        self.assertIn("WebFetch(domain:*)", opened["permissions"]["allow"])
        self.assertNotIn("Bash(curl *)", opened["permissions"]["deny"])
        self.assertIn("Bash(git push *)", opened["permissions"]["deny"])

    def test_command_carries_isolation_flags(self) -> None:
        command = harness.claude_command(
            "hi",
            model="claude-opus-5-5",
            effort="high",
            settings=Path("s.json"),
            permission_mode="dontAsk",
        )
        for flag in ("--strict-mcp-config", "--no-session-persistence", "--verbose"):
            self.assertIn(flag, command)
        self.assertEqual(command[command.index("--output-format") + 1], "stream-json")
        self.assertEqual(command[command.index("--permission-prompts") + 1], "none")

    def test_snapshot_excludes_evals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "src" / "demo"
            (source / "evals").mkdir(parents=True)
            (source / "SKILL.md").write_text("x")
            (source / "evals" / "evals.json").write_text("{}")
            copies = harness.snapshot_skills({"demo": source}, Path(tmp) / "snap")
            self.assertTrue((copies["demo"] / "SKILL.md").is_file())
            self.assertFalse((copies["demo"] / "evals").exists())
            project = harness.make_project(copies, prefix="harness-test-")
            try:
                self.assertTrue(
                    (project / ".claude" / "skills" / "demo" / "SKILL.md").is_file()
                )
            finally:
                harness.remove_project(project)


class RunTests(unittest.TestCase):
    def test_stops_at_decisive_tool_after_meta_tools(self) -> None:
        script = (
            "import json, sys, time\n"
            f"for event in json.loads({json.dumps([INIT, call('ToolSearch', 'm1'), SKILL_CALL])!r}):\n"
            "    print(json.dumps(event), flush=True)\n"
            "time.sleep(30)\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            run = harness.run_claude(
                [sys.executable, "-c", script],
                Path(tmp),
                dict(os.environ),
                timeout=20,
                stop_at_decisive_tool=True,
            )
        self.assertTrue(run.stopped_early)
        self.assertFalse(run.timed_out)
        prefix, tool = harness.tool_prefix(run.events)
        self.assertEqual(prefix, ["ToolSearch", "Skill"])
        self.assertEqual(harness.skill_of(tool), "optimize-go-code")


class SlotTests(unittest.TestCase):
    def test_slot_is_recreated_at_a_fixed_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill = root / "src" / "demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text("x")
            with harness.slot_project(root / "slots", 1, {"demo": skill}) as first:
                (first / "leftover.txt").write_text("from an earlier run")
            self.assertFalse(first.exists())
            with harness.slot_project(root / "slots", 1, {"demo": skill}) as second:
                self.assertEqual(second, root / "slots" / "slot-1")
                self.assertFalse((second / "leftover.txt").exists())
                self.assertTrue(
                    (second / ".claude" / "skills" / "demo" / "SKILL.md").is_file()
                )


class SessionStateTests(unittest.TestCase):
    def test_state_dir_matches_claude_code_naming(self) -> None:
        # Observed name for a real run directory under macOS's temp dir.
        project = Path("/private/var/folders/rv/abc/T/skill-output-with_skill-pu3zwh3n")
        self.assertEqual(
            harness.session_state_dir(project, Path("/h/.claude")),
            Path(
                "/h/.claude/projects/-private-var-folders-rv-abc-T-skill-output-with-skill-pu3zwh3n"
            ),
        )


class InstallSkillsTests(unittest.TestCase):
    def test_copy_excludes_top_level_evals_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = Path(tmp) / "src" / "demo"
            (skill / "evals").mkdir(parents=True)
            (skill / "evals" / "evals.json").write_text("{}", encoding="utf-8")
            (skill / "references" / "evals").mkdir(parents=True)
            (skill / "references" / "evals" / "card.md").write_text("x")
            (skill / "scripts" / "__pycache__").mkdir(parents=True)
            (skill / "SKILL.md").write_text("---\nname: demo\n---\n")
            project = Path(tmp) / "project"
            project.mkdir()
            harness.install_skills(project, {"demo": skill})
            installed = project / ".claude" / "skills" / "demo"
            self.assertFalse(installed.is_symlink())
            self.assertTrue((installed / "SKILL.md").is_file())
            self.assertFalse((installed / "evals").exists())
            self.assertTrue((installed / "references" / "evals" / "card.md").is_file())
            self.assertFalse((installed / "scripts" / "__pycache__").exists())


if __name__ == "__main__":
    unittest.main()
