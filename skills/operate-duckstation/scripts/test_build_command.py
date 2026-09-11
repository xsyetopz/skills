"""Tests for the DuckStation command builder."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("build_command.py")


class BuildCommandTests(unittest.TestCase):
    def run_builder(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *args],
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


if __name__ == "__main__":
    unittest.main()
