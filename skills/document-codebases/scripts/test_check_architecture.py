"""Tests for check_architecture.py (stdlib only; run directly)."""

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

import check_architecture as ca


def document(**bodies: str) -> str:
    """A clean document; keyword arguments replace a section's body."""
    sections = {
        "map": "```text\n├── app/\n│   └── main.py\n└── README.md\n```",
        "core": "`app/main.py` holds the entry point.",
        "invariants": "Nothing under `app/` imports `README.md`.",
    }
    sections.update(bodies)
    parts = ["# Architecture", "", "A tool."]
    titles = {"map": "Code map", "core": "Modules", "invariants": "Invariants"}
    for key, body in sections.items():
        parts += ["", f"## {titles[key]}", "", body]
    return "\n".join(parts) + "\n"


class Repo:
    def __init__(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        (self.root / "app").mkdir()
        (self.root / "app/main.py").write_text("")
        (self.root / "README.md").write_text("")

    def check(self, text: str) -> list[ca.Finding]:
        return ca.check(text, self.root)

    def close(self) -> None:
        self._tmp.cleanup()


def messages(findings: list[ca.Finding], level: str = "error") -> list[str]:
    return [f.message for f in findings if f.level == level]


class CheckTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = Repo()
        self.addCleanup(self.repo.close)

    def test_complete_document_is_clean(self) -> None:
        self.assertEqual(self.repo.check(document()), [])

    def test_empty_section(self) -> None:
        text = document(core="")
        errors = messages(self.repo.check(text))
        self.assertTrue(any("'Modules' is empty" in e for e in errors), errors)

    def test_heading_with_subsections_is_not_empty(self) -> None:
        text = document(core="### App\n\nServes requests from `app/main.py`.")
        self.assertEqual(self.repo.check(text), [])

    def test_nested_tree_path_that_does_not_exist(self) -> None:
        tree = "```text\n├── app/\n│   ├── main.py\n│   └── gone.py\n└── README.md\n```"
        errors = messages(self.repo.check(document(map=tree)))
        self.assertEqual(errors, ["tree names 'app/gone.py', which does not exist"])

    def test_tree_comments_and_ellipsis_are_ignored(self) -> None:
        tree = "```text\nroot/\n├── app/   # code\n│   └── ...\n└── README.md\n```"
        self.assertEqual(self.repo.check(document(map=tree)), [])

    def test_backticked_paths_and_bare_names(self) -> None:
        body = "`app/main.py`, `main.py`, `app/nope.py:3`, `missing.toml`."
        errors = messages(self.repo.check(document(core=body)))
        self.assertIn("names `app/nope.py`, which does not exist", errors)
        self.assertIn("names `missing.toml`, which does not exist", errors)
        self.assertEqual(len(errors), 2, errors)

    def test_commands_urls_and_modules_are_not_paths(self) -> None:
        body = "`python3 -m app`, `github.com/a/b`, `app.main:run`, `/etc/hosts`."
        self.assertEqual(self.repo.check(document(core=body)), [])

    def test_placeholders(self) -> None:
        body = "Name: [Insert Project Name]\n\nOwner: {team name}\n\n[Terminal] ok."
        errors = messages(self.repo.check(document(core=body)))
        self.assertEqual(len(errors), 2, errors)

    def test_uncovered_top_level_directory(self) -> None:
        (self.repo.root / "worker").mkdir()
        (self.repo.root / "worker/run.py").write_text("")
        errors = messages(self.repo.check(document(core="The worker runs jobs.")))
        self.assertIn("top-level directory 'worker/' is not described", errors)
        text = document(core="`worker/` runs jobs.")
        self.assertEqual(self.repo.check(text), [])

    def test_warnings_do_not_count_as_errors(self) -> None:
        body = "See [main](app/main.py), `app/main.py:10`, see CONTRIBUTING.md."
        findings = self.repo.check(document(core=body))
        self.assertEqual(messages(findings), [])
        self.assertEqual(len(messages(findings, "warning")), 3)


class MainTests(unittest.TestCase):
    def run_main(self, *argv: str) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            status = ca.main(list(argv))
        return status, out.getvalue()

    def test_exit_codes_and_json(self) -> None:
        repo = Repo()
        self.addCleanup(repo.close)
        doc = repo.root / "ARCHITECTURE.md"
        doc.write_text(document())
        self.assertEqual(self.run_main(str(doc))[0], 0)
        doc.write_text(document(core="`app/gone.py`"))
        status, out = self.run_main(str(doc), "--json")
        self.assertEqual(status, 1)
        self.assertEqual(json.loads(out)["errors"], 1)
        self.assertEqual(self.run_main(str(repo.root / "absent.md"))[0], 2)

    def test_placement(self) -> None:
        repo = Repo()
        self.addCleanup(repo.close)
        (repo.root / "docs").mkdir()
        cases = {
            "docs/ARCHITECTURE.md": "move the file to the repository root",
            "architecture.md": "name the file ARCHITECTURE.md",
        }
        for name, message in cases.items():
            doc = repo.root / name
            doc.write_text(document())
            status, out = self.run_main(str(doc))
            self.assertEqual(status, 1, out)
            self.assertIn(message, out)

    def test_commands(self) -> None:
        text = "```sh\n# setup\n$ make test\nmake test\n```\n```text\nls\n```\n"
        self.assertEqual(ca.commands(text), ["make test"])


if __name__ == "__main__":
    unittest.main()
