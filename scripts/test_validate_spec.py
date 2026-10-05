"""Tests for the spec check that allows Claude Code frontmatter fields."""

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_spec import validate


def skill(root: Path, extra: str) -> Path:
    path = root / "demo-skill"
    path.mkdir()
    (path / "SKILL.md").write_text(
        f"---\nname: demo-skill\ndescription: Does a thing.\n{extra}---\n\nBody.\n"
    )
    return path


class ValidateSpecTest(unittest.TestCase):
    def test_claude_code_fields_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            extra = "when_to_use: Say this.\ndisable-model-invocation: true\n"
            self.assertEqual(validate(skill(Path(tmp), extra)), [])

    def test_other_unknown_fields_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            errors = validate(skill(Path(tmp), "triggers: x\n"))
        self.assertTrue(any("triggers" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
