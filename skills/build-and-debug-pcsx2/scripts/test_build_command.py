"""Tests for the PCSX2 command builder."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("build_command.py")


class BuildCommandTests(unittest.TestCase):
    def run_builder(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--format", "posix", *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def test_isolated_no_gui_boot(self) -> None:
        result = self.run_builder(
            "--exe",
            "/opt/PCSX2 Nightly/pcsx2-qt",
            "--batch",
            "--no-gui",
            "--data-path",
            "/tmp/case data",
            "--log-file",
            "/tmp/case data/emulog.txt",
            "--boot",
            "/games/-sample.iso",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "'/opt/PCSX2 Nightly/pcsx2-qt' -batch -nogui -datapath '/tmp/case data' "
            "-logfile '/tmp/case data/emulog.txt' -- /games/-sample.iso",
        )

    def test_elf_disc_and_game_args(self) -> None:
        result = self.run_builder(
            "--exe",
            "pcsx2-qt",
            "--elf",
            "test.elf",
            "--disc",
            "/dev/sr0",
            "--game-args",
            "level=2 mode=test",
            "--debugger",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "pcsx2-qt -elf test.elf -gameargs 'level=2 mode=test' -disc /dev/sr0 -debugger",
        )

    def test_test_config(self) -> None:
        result = self.run_builder(
            "--exe", "pcsx2-qt", "--data-path", "/tmp/case", "--test-config"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(), "pcsx2-qt -datapath /tmp/case -testconfig"
        )

    def test_no_gui_requires_target(self) -> None:
        result = self.run_builder("--exe", "pcsx2-qt", "--no-gui")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("require a bootable target", result.stderr)

    def test_state_file_requires_matching_boot_target(self) -> None:
        result = self.run_builder("--exe", "pcsx2-qt", "--state-file", "checkpoint.p2s")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("require a boot target", result.stderr)
        result = self.run_builder(
            "--exe",
            "pcsx2-qt",
            "--state-file",
            "checkpoint.p2s",
            "--boot",
            "game.iso",
            "--batch",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            result.stdout.strip(),
            "pcsx2-qt -batch -statefile checkpoint.p2s -- game.iso",
        )

    def test_batch_without_target_is_rejected(self) -> None:
        result = self.run_builder("--exe", "pcsx2-qt", "--batch")
        self.assertNotEqual(result.returncode, 0)

    def test_game_args_require_elf(self) -> None:
        result = self.run_builder(
            "--exe", "pcsx2-qt", "--boot", "game.iso", "--game-args", "x"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires --elf", result.stderr)

    def test_conflicting_modes_are_rejected(self) -> None:
        result = self.run_builder(
            "--exe", "pcsx2-qt", "--portable", "--data-path", "/tmp/case"
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed with argument", result.stderr)

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


if __name__ == "__main__":
    unittest.main()
