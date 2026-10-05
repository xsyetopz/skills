"""Offline tests for upsert_comment.py.

A fake `gh` executable on PATH answers from a JSON state file and logs
every call, so the tests see exactly which writes would reach GitHub.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent

FAKE_GH = textwrap.dedent(
    """\
    #!/usr/bin/env python3
    import json, os, sys
    state_path = os.environ["FAKE_GH_STATE"]
    state = json.load(open(state_path))
    args = sys.argv[1:]
    with open(os.environ["FAKE_GH_LOG"], "a") as log:
        log.write(json.dumps(args) + "\\n")
    if args[:3] == ["api", "--paginate", "--slurp"]:
        print(json.dumps([state["comments"]]))
    elif args[:3] == ["api", "--method", "POST"]:
        body = json.loads(sys.stdin.read())["body"]
        state["comments"].append({"id": 99, "body": body})
        json.dump(state, open(state_path, "w"))
        print(json.dumps({"html_url": "https://example.invalid/c/99"}))
    elif args[:3] == ["api", "--method", "PATCH"]:
        body = json.loads(sys.stdin.read())["body"]
        cid = int(args[3].rsplit("/", 1)[1])
        for c in state["comments"]:
            if c["id"] == cid:
                c["body"] = body
        json.dump(state, open(state_path, "w"))
        print(json.dumps({"html_url": f"https://example.invalid/c/{cid}"}))
    else:
        sys.exit(f"unexpected gh call: {args}")
    """
)


class FakeGh:
    def __init__(self, state: dict) -> None:
        self.dir = Path(tempfile.mkdtemp())
        gh = self.dir / "gh"
        gh.write_text(FAKE_GH)
        gh.chmod(0o755)
        self.state = self.dir / "state.json"
        self.state.write_text(json.dumps(state))
        self.log = self.dir / "log.jsonl"
        self.env = {
            **os.environ,
            "PATH": f"{self.dir}{os.pathsep}{os.environ['PATH']}",
            "FAKE_GH_STATE": str(self.state),
            "FAKE_GH_LOG": str(self.log),
        }

    def run(self, script: str, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *args],
            capture_output=True,
            text=True,
            env=self.env,
            check=False,
        )

    def calls(self) -> list[list[str]]:
        if not self.log.exists():
            return []
        return [json.loads(line) for line in self.log.read_text().splitlines()]

    def writes(self) -> list[list[str]]:
        return [c for c in self.calls() if c[:2] != ["api", "--paginate"]]


class UpsertCommentTests(unittest.TestCase):
    def body(self, fake: FakeGh, text: str) -> str:
        path = fake.dir / "body.md"
        path.write_text(text)
        return str(path)

    def test_creates_once_then_updates_then_noop(self) -> None:
        fake = FakeGh({"comments": [{"id": 1, "body": "human comment"}]})
        first = fake.run(
            "upsert_comment.py",
            "o/r",
            "7",
            "coverage",
            self.body(fake, "92%"),
            "--apply",
        )
        self.assertIn("create comment on #7", first.stdout)
        second = fake.run(
            "upsert_comment.py",
            "o/r",
            "7",
            "coverage",
            self.body(fake, "93%"),
            "--apply",
        )
        self.assertIn("update comment 99", second.stdout)
        third = fake.run(
            "upsert_comment.py",
            "o/r",
            "7",
            "coverage",
            self.body(fake, "93%"),
            "--apply",
        )
        self.assertIn("already up to date", third.stdout)
        state = json.loads(fake.state.read_text())
        self.assertEqual(len(state["comments"]), 2)
        self.assertEqual(state["comments"][1]["body"], "<!-- upsert:coverage -->\n93%")

    def test_json_plan_then_apply(self) -> None:
        fake = FakeGh({"comments": [{"id": 5, "body": "<!-- upsert:k -->\nold"}]})
        body = self.body(fake, "new")
        planned = fake.run("upsert_comment.py", "o/r", "7", "k", body, "--json")
        self.assertEqual(
            json.loads(planned.stdout),
            {"action": "update", "comment_id": 5, "applied": False, "url": None},
        )
        self.assertEqual(fake.writes(), [])
        applied = fake.run(
            "upsert_comment.py", "o/r", "7", "k", body, "--apply", "--json"
        )
        report = json.loads(applied.stdout)
        self.assertEqual((report["action"], report["applied"]), ("update", True))
        self.assertEqual(report["url"], "https://example.invalid/c/5")
        again = fake.run("upsert_comment.py", "o/r", "7", "k", body, "--json")
        self.assertEqual(json.loads(again.stdout)["action"], "none")

    def test_missing_gh_is_explained(self) -> None:
        fake = FakeGh({"comments": []})
        fake.env["PATH"] = str(fake.dir / "empty")
        result = fake.run("upsert_comment.py", "o/r", "7", "k", self.body(fake, "x"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("gh not found", result.stderr)

    def test_gh_output_is_decoded_as_utf8(self) -> None:
        sys.path.insert(0, str(SCRIPTS))
        import upsert_comment

        with mock.patch.object(upsert_comment.subprocess, "run") as run:
            upsert_comment.gh("api", "x")
        self.assertEqual(run.call_args.kwargs.get("encoding"), "utf-8")

    def test_missing_body_file_names_expected_input(self) -> None:
        fake = FakeGh({"comments": []})
        result = fake.run("upsert_comment.py", "o/r", "7", "k", "/no/such/body.md")
        self.assertEqual(result.returncode, 2)
        self.assertIn("/no/such/body.md", result.stderr)
        self.assertIn("expected a Markdown comment body file", result.stderr)

    def test_dry_run_makes_no_write(self) -> None:
        fake = FakeGh({"comments": []})
        result = fake.run("upsert_comment.py", "o/r", "7", "k", self.body(fake, "x"))
        self.assertIn("plan create comment on #7", result.stdout)
        self.assertEqual(fake.writes(), [])


if __name__ == "__main__":
    unittest.main()
