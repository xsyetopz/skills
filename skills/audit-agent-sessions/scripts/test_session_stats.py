"""Tests for session_stats.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import session_stats as ss


def assistant(
    msg_id: str, model: str, tools: list[dict[str, Any]] | None = None, **usage: Any
) -> dict[str, Any]:
    return {
        "type": "assistant",
        "message": {
            "id": msg_id,
            "model": model,
            "usage": usage,
            "content": tools or [],
        },
    }


def tool(call_id: str, name: str, **args: Any) -> dict[str, Any]:
    return {"type": "tool_use", "id": call_id, "name": name, "input": args}


def bash_result(call_id: str, stdout: str) -> dict[str, Any]:
    return {
        "type": "user",
        "message": {
            "content": [
                {"type": "tool_result", "tool_use_id": call_id, "content": stdout}
            ]
        },
        "toolUseResult": {"stdout": stdout, "stderr": ""},
    }


class SessionStatsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, relative: str, rows: list[Any]) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        return path

    def run_json(self, *argv: str) -> dict[str, Any]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ss.main([*argv, "--json"]), 0)
        return json.loads(out.getvalue())

    def test_tokens_split_by_model_and_scope_and_counted_once_per_message(self) -> None:
        usage = {
            "input_tokens": 10,
            "cache_read_input_tokens": 1_000_000,
            "cache_creation_input_tokens": 300,
            "cache_creation": {
                "ephemeral_5m_input_tokens": 100,
                "ephemeral_1h_input_tokens": 200,
            },
            "output_tokens": 50,
        }
        # One API message is written as one row per content block.
        self.write("s1.jsonl", [assistant("m1", "claude-opus-5-5", **usage)] * 2)
        self.write(
            "s1/subagents/agent-a.jsonl",
            [assistant("m2", "claude-haiku-4-5-20251001", output_tokens=1_000_000)],
        )
        report = self.run_json(str(self.root))
        rows = {(r["model"], r["scope"]): r for r in report["tokens"]}
        main = rows[("claude-opus-5-5", "main")]
        self.assertEqual(
            [main[f] for f in ss.TOKEN_FIELDS], [10, 100, 200, 1_000_000, 50]
        )
        # 10*4 + 100*5 + 200*8 + 1e6*0.20 + 50*20, per million tokens.
        self.assertAlmostEqual(main["cost_usd"], 0.20314, places=4)
        sub = rows[("claude-haiku-4-5-20251001", "subagent")]
        self.assertEqual(sub["cost_usd"], 5.0)
        self.assertEqual(report["transcripts"], 2)

    def test_cache_write_without_split_is_priced_at_5m_rate(self) -> None:
        self.write(
            "s.jsonl",
            [
                assistant(
                    "m1", "claude-sonnet-5-5", cache_creation_input_tokens=1_000_000
                )
            ],
        )
        (row,) = self.run_json(str(self.root))["tokens"]
        self.assertEqual(row["cache_write_5m"], 1_000_000)
        self.assertEqual(row["cost_usd"], 2.5)

    def test_unknown_model_is_listed_not_priced(self) -> None:
        self.write("s.jsonl", [assistant("m1", "claude-future-9", output_tokens=5)])
        report = self.run_json(str(self.root))
        self.assertEqual(report["unpriced_models"], ["claude-future-9"])
        self.assertIsNone(report["tokens"][0]["cost_usd"])

    def test_repeated_command_counts_only_identical_output(self) -> None:
        rows = []
        for n, out in enumerate(["clean", "clean", "clean", "dirty"]):
            call = f"t{n}"
            rows += [
                assistant(
                    f"m{n}",
                    "claude-opus-5-5",
                    [tool(call, "Bash", command="git status")],
                ),
                bash_result(call, out),
            ]
        rows += [
            assistant("m9", "claude-opus-5-5", [tool("t9", "Bash", command="ls")]),
            bash_result("t9", "clean"),
        ]
        self.write("s.jsonl", rows)
        report = self.run_json(str(self.root))
        self.assertEqual(
            [(r["command_head"], r["runs"]) for r in report["repeated_commands"]],
            [("git status", 3)],
        )
        self.assertEqual(report["repeated_commands_total"], 2)

    def test_reread_resets_after_edit_and_ignores_other_ranges(self) -> None:
        def read(call: str, **args: Any) -> dict[str, Any]:
            return assistant(call, "claude-opus-5-5", [tool(call, "Read", **args)])

        self.write(
            "s.jsonl",
            [
                read("r1", file_path="/a.py"),
                read("r2", file_path="/a.py"),
                read("r3", file_path="/a.py", offset=10, limit=5),
                assistant(
                    "e1", "claude-opus-5-5", [tool("e1", "Edit", file_path="/a.py")]
                ),
                read("r4", file_path="/a.py"),
            ],
        )
        report = self.run_json(str(self.root))
        self.assertEqual(
            report["repeated_reads"],
            [{"transcript": str(self.root / "s.jsonl"), "path": "/a.py", "rereads": 1}],
        )

    def test_bad_lines_counted_and_orphaned_copies_skipped(self) -> None:
        path = self.write("s.jsonl", [assistant("m1", "claude-opus-5-5")])
        with path.open("a", encoding="utf-8") as handle:
            handle.write("{not json\n")
        self.write("s.orphaned-1-x.jsonl", [assistant("m2", "claude-opus-5-5")])
        report = self.run_json(str(self.root))
        self.assertEqual((report["transcripts"], report["bad_lines"]), (1, 1))

    def test_missing_path_exits_2_with_hint(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(ss.main([str(self.root / "nope")]), 2)
        self.assertIn("~/.claude/projects", err.getvalue())

    def test_text_output_has_no_command_output(self) -> None:
        self.write(
            "s.jsonl",
            [
                assistant("m1", "claude-opus-5-5", [tool("t1", "Bash", command="env")]),
                bash_result("t1", "SECRET=hunter2"),
                assistant("m2", "claude-opus-5-5", [tool("t2", "Bash", command="env")]),
                bash_result("t2", "SECRET=hunter2"),
            ],
        )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(ss.main([str(self.root)]), 0)
        self.assertIn("2x  env", out.getvalue())
        self.assertNotIn("hunter2", out.getvalue())


if __name__ == "__main__":
    unittest.main()
