"""Tests for the 'Use when' sentence that the skill index prints."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from skill_index import USE


def use(description: str) -> str | None:
    match = USE.search(description)
    return match.group(1) if match else None


class UseSentenceTest(unittest.TestCase):
    def test_file_name_period_does_not_end_the_sentence(self) -> None:
        self.assertEqual(
            use("Writes skills. Use when a SKILL.md grew too long. Not for hooks."),
            "when a SKILL.md grew too long.",
        )

    def test_sentence_at_end_of_description(self) -> None:
        self.assertEqual(
            use("Audits repos. Use before open-sourcing."), "before open-sourcing."
        )

    def test_description_without_use_sentence(self) -> None:
        self.assertIsNone(use("Writes skills. Not for hooks."))


if __name__ == "__main__":
    unittest.main()
