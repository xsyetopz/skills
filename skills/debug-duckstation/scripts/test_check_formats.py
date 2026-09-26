"""Tests for check_formats.py against the bundled good and bad fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_formats.py")
EXAMPLES = Path(__file__).resolve().parent.parent / "assets" / "examples"


def run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").split()


class SettingsTests(unittest.TestCase):
    def test_debug_overlay_passes(self) -> None:
        result = run("settings", str(EXAMPLES / "settings" / "debug-overlay.ini"))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.strip(), "OK")

    def test_bad_overlay_reports_typo_type_and_duplicate(self) -> None:
        result = run("settings", str(EXAMPLES / "settings" / "bad-overlay.ini"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Logging.LogToFiles is not written", result.stdout)
        self.assertIn("expects true or false, got 'yes'", result.stdout)
        self.assertIn("duplicate key Debug.EnableGDBServer", result.stdout)
        self.assertEqual(len(result.stdout.splitlines()), 3)

    def test_key_before_section_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "s.ini"
            path.write_text("LogToFile = true\n", encoding="utf-8")
            result = run("settings", str(path))
        self.assertEqual(result.returncode, 1)
        self.assertIn("key before any [Section]", result.stdout)


class CheatTests(unittest.TestCase):
    def test_example_passes(self) -> None:
        result = run("cht", str(EXAMPLES / "cheats" / "HASH-EXAMPLE.cht"))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_bad_example_reports_each_code(self) -> None:
        result = run("cht", str(EXAMPLES / "cheats" / "bad-example.cht"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("Activation must be Manual or EndFrame", result.stdout)
        self.assertIn("[Wildcard Without Option] uses '?'", result.stdout)
        self.assertIn(":15: not a code line", result.stdout)

    def test_hex_option_range_and_trailing_option_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.cht"
            path.write_text(
                "[Pick]\nType = Gameshark\nActivation = EndFrame\n"
                "801EEAE4 00??\nOptionRange = 0x00:0xFF\n",
                encoding="utf-8",
            )
            result = run("cht", str(path))
        self.assertEqual(result.returncode, 0, result.stdout)


class TextureNameTests(unittest.TestCase):
    def test_wiki_names_pass(self) -> None:
        names = lines(EXAMPLES / "textures" / "names.txt")
        result = run("texture-name", *names)
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_bad_names_fail(self) -> None:
        names = lines(EXAMPLES / "textures" / "bad-names.txt")
        result = run("texture-name", *names)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(len(result.stdout.splitlines()), len(names))


class CommandLineTests(unittest.TestCase):
    def test_json_report(self) -> None:
        result = run("cht", str(EXAMPLES / "cheats" / "bad-example.cht"), "--json")
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["count"], len(report["findings"]))
        first = report["findings"][0]
        self.assertEqual(first["subject"], str(EXAMPLES / "cheats" / "bad-example.cht"))
        self.assertIsInstance(first["line"], int)
        self.assertTrue(any(f["line"] is None for f in report["findings"]))

    def test_missing_file_is_input_error(self) -> None:
        result = run("cht", "/nonexistent/x.cht")
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read /nonexistent/x.cht", result.stderr)


if __name__ == "__main__":
    unittest.main()
