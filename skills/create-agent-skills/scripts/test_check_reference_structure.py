"""Tests for check_reference_structure.py (stdlib only; run directly)."""

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

import check_reference_structure as crs

SKILL = """\
---
name: demo-skill
description: >-
  Demonstrates the checker. Use in tests only.
---

# Demo

See [cards](references/cards.md#first-card) and [long](references/long.md).
"""


def make_skill(root: Path, skill_md: str = SKILL) -> Path:
    skill = root / "demo-skill"
    (skill / "references").mkdir(parents=True)
    (skill / "SKILL.md").write_text(skill_md, encoding="utf-8")
    (skill / "references" / "cards.md").write_text(
        textwrap.dedent(
            """\
            # Cards

            ## First card

            Text with `code` in a [link](../SKILL.md).
            """
        ),
        encoding="utf-8",
    )
    long_lines = ["# Long", "", "## Contents", ""] + ["line"] * 120
    (skill / "references" / "long.md").write_text(
        "\n".join(long_lines) + "\n", encoding="utf-8"
    )
    return skill


def run(skill: Path) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        status = crs.main([str(skill)])
    return status, out.getvalue()


class CheckerTests(unittest.TestCase):
    def test_valid_skill_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status, output = run(make_skill(Path(tmp)))
            self.assertEqual(status, 0, output)

    def test_unlinked_reference_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = make_skill(Path(tmp))
            (skill / "references" / "orphan.md").write_text("# Orphan\n")
            status, output = run(skill)
            self.assertEqual(status, 1)
            self.assertIn("orphan.md: not linked directly", output)

    def test_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = make_skill(Path(tmp))
            orphan = skill / "references" / "orphan.md"
            orphan.write_text("# Orphan\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = crs.main(["--json", str(skill)])
        self.assertEqual(status, 1)
        self.assertEqual(
            json.loads(out.getvalue()),
            {
                "problems": [
                    {
                        "file": str(orphan),
                        "message": "not linked directly from SKILL.md",
                    }
                ],
                "skills": 1,
            },
        )

    def test_help_and_usage_return_status(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(crs.main(["--help"]), 0)
        self.assertIn("Exit status:", out.getvalue())
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(crs.main([]), 2)

    def test_long_reference_without_contents_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = make_skill(Path(tmp))
            (skill / "references" / "long.md").write_text("x\n" * 150)
            status, output = run(skill)
            self.assertEqual(status, 1)
            self.assertIn("no '## Contents' section", output)

    def test_missing_anchor_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = make_skill(Path(tmp), SKILL.replace("#first-card", "#second-card"))
            status, output = run(skill)
            self.assertEqual(status, 1)
            self.assertIn("missing anchor", output)

    def test_name_must_match_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skill = make_skill(
                Path(tmp), SKILL.replace("name: demo-skill", "name: other")
            )
            status, output = run(skill)
            self.assertEqual(status, 1)
            self.assertIn("name must equal directory", output)

    def test_slug_rules(self) -> None:
        self.assertEqual(
            crs.github_slug("CollectionsMarshal.AsSpan"), "collectionsmarshalasspan"
        )
        self.assertEqual(
            crs.github_slug("Use `ValueTask` for X"), "use-valuetask-for-x"
        )
        self.assertEqual(
            crs.github_slug("Dispatch table instead of an if/elif chain"),
            "dispatch-table-instead-of-an-ifelif-chain",
        )

    def test_nested_fences_hide_headings_and_links(self) -> None:
        text = "\n".join(
            [
                "````markdown",
                "## Inside",
                "```python",
                "x = 1",
                "```",
                "[broken](missing.md)",
                "````",
                "## Outside",
            ]
        )
        self.assertEqual(crs.outside_fences(text), ["## Outside"])

    def test_not_a_directory_is_input_error(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(crs.main(["/nonexistent"]), 2)


if __name__ == "__main__":
    unittest.main()
