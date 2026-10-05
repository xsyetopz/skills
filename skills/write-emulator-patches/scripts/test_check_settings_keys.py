"""Tests for check_settings_keys.py."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_settings_keys.py")

GOOD = """\
[Logging]
LogLevel = Debug
LogToFile = true

[Debug]
EnableGDBServer = true
"""
BAD = """\
[Logging]
LogToFiles = true
LogToFile = yes

[Debug]
EnableGDBServer = true
EnableGDBServer = false
"""


def run(text: str, *extra: str) -> subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "settings.ini"
        path.write_text(text, encoding="utf-8")
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path), *extra],
            check=False,
            capture_output=True,
            text=True,
        )


class SettingsTests(unittest.TestCase):
    def test_known_keys_pass(self) -> None:
        result = run(GOOD)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.strip(), "OK")

    def test_typo_bad_boolean_and_duplicate_are_reported(self) -> None:
        result = run(BAD)
        self.assertEqual(result.returncode, 1)
        self.assertIn("Logging.LogToFiles is not written", result.stdout)
        self.assertIn("expects true or false, got 'yes'", result.stdout)
        self.assertIn("duplicate key Debug.EnableGDBServer", result.stdout)
        self.assertEqual(len(result.stdout.splitlines()), 3)

    def test_key_before_section_is_reported(self) -> None:
        result = run("LogToFile = true\n")
        self.assertEqual(result.returncode, 1)
        self.assertIn("key before any [Section]", result.stdout)

    def test_missing_file_is_input_error(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "/nonexistent/settings.ini"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read /nonexistent/settings.ini", result.stderr)

    def test_help_exits_zero(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
