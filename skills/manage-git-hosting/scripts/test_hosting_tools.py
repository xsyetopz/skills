"""Offline tests for sync_labels.py and upsert_comment.py.

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
    if args[:2] == ["label", "list"]:
        print(json.dumps(state["labels"]))
    elif args[:1] == ["label"]:
        pass
    elif args[:3] == ["api", "--paginate", "--slurp"]:
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
        reads = (["label", "list"], ["api", "--paginate"])
        return [c for c in self.calls() if c[:2] not in reads]


LABELS = [
    {"name": "bug", "color": "d73a4a", "description": "Something is broken"},
    {"name": "stale", "color": "cccccc", "description": ""},
]


class SyncLabelsTests(unittest.TestCase):
    def desired(self, fake: FakeGh, labels: list[dict]) -> str:
        path = fake.dir / "desired.json"
        path.write_text(json.dumps(labels))
        return str(path)

    def test_plan_without_apply_writes_nothing(self) -> None:
        fake = FakeGh({"labels": LABELS})
        wanted = [
            {"name": "Bug", "color": "#D73A4A", "description": "Something is broken"},
            {"name": "docs", "color": "0075ca", "description": "Docs"},
        ]
        result = fake.run("sync_labels.py", "o/r", self.desired(fake, wanted))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.splitlines(),
            ["plan gh label create docs --color 0075ca --description Docs"],
        )
        self.assertEqual(fake.writes(), [])

    def test_apply_edits_changed_label_and_prunes_only_with_flag(self) -> None:
        fake = FakeGh({"labels": LABELS})
        wanted = [
            {"name": "bug", "color": "ff0000", "description": "Something is broken"}
        ]
        fake.run("sync_labels.py", "o/r", self.desired(fake, wanted), "--apply")
        self.assertEqual(
            fake.writes(),
            [
                [
                    "label",
                    "edit",
                    "bug",
                    "--color",
                    "ff0000",
                    "--description",
                    "Something is broken",
                    "-R",
                    "o/r",
                ]
            ],
        )
        fake.run(
            "sync_labels.py", "o/r", self.desired(fake, wanted), "--apply", "--prune"
        )
        self.assertIn(["label", "delete", "stale", "--yes", "-R", "o/r"], fake.writes())

    def test_json_plan_and_apply(self) -> None:
        fake = FakeGh({"labels": LABELS})
        wanted = self.desired(fake, [{"name": "docs", "color": "0075ca"}])
        planned = fake.run("sync_labels.py", "o/r", wanted, "--json")
        report = json.loads(planned.stdout)
        self.assertEqual((report["repo"], report["applied"]), ("o/r", False))
        self.assertEqual(
            report["changes"],
            [
                {
                    "action": "create",
                    "label": "docs",
                    "command": ["gh", "label", "create", "docs", "--color",
                                "0075ca", "--description", "", "-R", "o/r"],
                    "status": "planned",
                }
            ],
        )  # fmt: skip
        self.assertEqual(fake.writes(), [])
        applied = fake.run("sync_labels.py", "o/r", wanted, "--json", "--apply")
        self.assertEqual(json.loads(applied.stdout)["changes"][0]["status"], "applied")
        self.assertEqual(len(fake.writes()), 1)

    def test_missing_gh_is_explained(self) -> None:
        fake = FakeGh({"labels": LABELS})
        fake.env["PATH"] = str(fake.dir / "empty")
        result = fake.run("sync_labels.py", "o/r", self.desired(fake, LABELS))
        self.assertEqual(result.returncode, 2)
        self.assertIn("gh not found", result.stderr)

    def test_matching_labels_do_nothing(self) -> None:
        fake = FakeGh({"labels": LABELS})
        result = fake.run(
            "sync_labels.py", "o/r", self.desired(fake, LABELS), "--apply"
        )
        self.assertIn("nothing to do", result.stdout)
        self.assertEqual(fake.writes(), [])


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

    def test_dry_run_makes_no_write(self) -> None:
        fake = FakeGh({"comments": []})
        result = fake.run("upsert_comment.py", "o/r", "7", "k", self.body(fake, "x"))
        self.assertIn("plan create comment on #7", result.stdout)
        self.assertEqual(fake.writes(), [])


if __name__ == "__main__":
    unittest.main()
