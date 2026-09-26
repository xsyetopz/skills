"""Tests for the DuckStation command builder."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("build_command.py")
HELP = (
    Path(__file__).resolve().parent.parent
    / "assets"
    / "examples"
    / "help-0.1-11826.txt"
)


class BuildCommandTests(unittest.TestCase):
    def run_builder(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--format", "posix", *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_no_gui_image_boot(self) -> None:
        result = self.run_builder(
            "--exe",
            "/tmp/Duck Station/duckstation-qt",
            "--batch",
            "--no-gui",
            "--fast-boot",
            "--boot",
            "/games/-sample.cue",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "'/tmp/Duck Station/duckstation-qt' -batch -fastboot -nogui -- /games/-sample.cue",
        )

    def test_direct_executable(self) -> None:
        result = self.run_builder(
            "--exe", "duckstation-qt", "--batch", "--psx-exe", "test.exe"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "duckstation-qt -batch -- test.exe")

    def test_resume_with_game(self) -> None:
        result = self.run_builder(
            "--exe",
            "duckstation-qt",
            "--resume",
            "--no-gui",
            "--boot",
            "game.cue",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(), "duckstation-qt -resume -nogui -- game.cue"
        )

    def test_no_gui_requires_target(self) -> None:
        result = self.run_builder("--exe", "duckstation-qt", "--no-gui")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires a bootable target", result.stderr)

    def test_conflicting_boot_modes_are_rejected(self) -> None:
        result = self.run_builder(
            "--exe",
            "duckstation-qt",
            "--boot",
            "game.cue",
            "--fast-boot",
            "--slow-boot",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed with argument", result.stderr)

    def test_state_file_conflicts_with_state_slot(self) -> None:
        result = self.run_builder(
            "--exe",
            "duckstation-qt",
            "--state-file",
            "checkpoint.sav",
            "--state",
            "1",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("mutually exclusive", result.stderr)

    def test_resume_conflicts_with_state_slot(self) -> None:
        result = self.run_builder("--exe", "duckstation-qt", "--resume", "--state", "1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("cannot be combined", result.stderr)

    def test_json_argv_preserves_exact_native_arguments(self) -> None:
        import json

        result = self.run_builder(
            "--format",
            "argv",
            "--exe",
            "emulator",
            "--native",
            "-new-native-switch",
            "space ' ; value",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            json.loads(result.stdout),
            ["emulator", "-new-native-switch", "space ' ; value"],
        )

    def test_native_mode_rejects_silently_dropped_convenience_options(self) -> None:
        result = self.run_builder(
            "--exe", "emulator", "--batch", "--native", "-new-native-switch"
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("do not mix", result.stderr)

    def test_unknown_wrapper_option_is_not_ignored(self) -> None:
        result = self.run_builder("--exe", "emulator", "--not-supported")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")

    def test_help_file_accepts_every_convenience_flag(self) -> None:
        result = self.run_builder(
            "--exe",
            "DuckStation",
            "--help-file",
            str(HELP),
            "--batch",
            "--no-gui",
            "--fast-boot",
            "--early-console",
            "--fullscreen",
            "--big-picture",
            "--boot=-dash.cue",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "DuckStation -batch -fastboot -fullscreen -nogui -bigpicture"
            " -earlyconsole -- -dash.cue",
        )

    def test_help_file_rejects_flag_the_release_does_not_list(self) -> None:
        result = self.run_builder(
            "--exe",
            "DuckStation",
            "--help-file",
            str(HELP),
            "--native",
            "-portable",
            "-batch",
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("flags not listed", result.stderr)
        self.assertIn("-portable", result.stderr)

    def test_unreadable_help_file_is_a_usage_error(self) -> None:
        result = self.run_builder(
            "--exe", "duckstation-qt", "--boot", "g.cue",
            "--help-file", "/nonexistent/help.txt",
        )  # fmt: skip
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read --help-file", result.stderr)


if __name__ == "__main__":
    unittest.main()
