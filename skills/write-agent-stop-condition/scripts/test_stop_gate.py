"""Tests for stop_gate.py (stdlib only; run directly)."""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPT = Path(__file__).resolve().parent / "stop_gate.py"


def run(stdin: str, *args: str) -> subprocess.CompletedProcess:
    """Run the gate with its retry counters in the event's cwd, not the real temp dir."""
    cwd = json.loads(stdin).get("cwd", ".") if stdin.startswith("{") else "."
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env={**os.environ, "TMPDIR": cwd, "TEMP": cwd, "TMP": cwd},
    )


def stop_event(cwd: str, active: bool = False) -> str:
    return json.dumps(
        {
            "hook_event_name": "Stop",
            "session_id": "s1",
            "cwd": cwd,
            "stop_hook_active": active,
        }
    )


def decision(result: subprocess.CompletedProcess) -> str:
    return json.loads(result.stdout).get("decision", "stop")


def import_gate():
    sys.path.insert(0, str(SCRIPT.parent))
    import stop_gate

    return stop_gate


def main_in_process(gate, event: str, *args: str) -> dict:
    out = io.StringIO()
    stdin = io.TextIOWrapper(io.BytesIO(event.encode()))
    with mock.patch.object(sys, "stdin", stdin), mock.patch.object(sys, "stdout", out):
        gate.main(list(args))
    return json.loads(out.getvalue())


def py(code: str) -> str:
    return f"{sys.executable} -c '{code}'"


class StopGateTests(unittest.TestCase):
    def test_blocks_when_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            check = py('import sys; print("2 failed"); sys.exit(1)')
            result = run(stop_event(tmp), "--check", check)
        output = json.loads(result.stdout)
        self.assertEqual(output["decision"], "block")
        self.assertIn("2 failed", output["reason"])

    def test_allows_stop_when_check_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run(stop_event(tmp), "--check", py("pass"))
        self.assertEqual(json.loads(result.stdout), {})

    def test_blocks_up_to_max_retries_then_lets_the_agent_stop(self) -> None:
        fail = py("import sys; sys.exit(1)")
        with tempfile.TemporaryDirectory() as tmp:
            first = run(stop_event(tmp), "--check", fail, "--max-retries", "2")
            second = run(stop_event(tmp, True), "--check", fail, "--max-retries", "2")
            third = run(stop_event(tmp, True), "--check", fail, "--max-retries", "2")
        self.assertIn("Retry 1 of 2", json.loads(first.stdout)["reason"])
        self.assertIn("Retry 2 of 2", json.loads(second.stdout)["reason"])
        self.assertEqual(json.loads(third.stdout), {})

    def test_new_stop_starts_the_count_over(self) -> None:
        fail = py("import sys; sys.exit(1)")
        with tempfile.TemporaryDirectory() as tmp:
            run(stop_event(tmp), "--check", fail, "--max-retries", "1")
            used_up = run(stop_event(tmp, True), "--check", fail, "--max-retries", "1")
            fresh = run(stop_event(tmp), "--check", fail, "--max-retries", "1")
        self.assertEqual(decision(used_up), "stop")
        self.assertEqual(decision(fresh), "block")

    def test_passing_check_clears_the_counter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            run(stop_event(tmp), "--check", py("import sys; sys.exit(1)"))
            run(stop_event(tmp, True), "--check", py("pass"))
            self.assertEqual(list(Path(tmp).glob("stop_gate-*")), [])

    def test_unwritable_counter_lets_the_agent_stop(self) -> None:
        gate = import_gate()
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing" / "counter"
            with mock.patch.object(gate, "state_file", return_value=missing):
                output = main_in_process(
                    gate, stop_event(tmp), "--check", py("import sys; sys.exit(1)")
                )
        self.assertEqual(output, {})

    def test_unreadable_counter_lets_the_agent_stop(self) -> None:
        gate = import_gate()
        with tempfile.TemporaryDirectory() as tmp:
            counter = Path(tmp) / "counter"
            counter.write_text("junk")
            with mock.patch.object(gate, "state_file", return_value=counter):
                output = main_in_process(
                    gate,
                    stop_event(tmp, True),
                    "--check",
                    py("import sys; sys.exit(1)"),
                )
        self.assertEqual(output, {})

    def test_max_retries_below_one_is_usage_error(self) -> None:
        result = run(stop_event("."), "--check", "true", "--max-retries", "0")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--max-retries", result.stderr)

    def test_timeout_blocks_with_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run(
                stop_event(tmp),
                "--check",
                py("import time; time.sleep(5)"),
                "--timeout",
                "0.5",
            )
        self.assertIn("did not finish", json.loads(result.stdout)["reason"])

    def test_non_utf8_check_output_still_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            check = py(
                "import sys; sys.stdout.buffer.write(bytes([255, 254])); sys.exit(1)"
            )
            result = run(stop_event(tmp), "--check", check)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["decision"], "block")

    def test_check_command_is_resolved_with_which(self) -> None:
        stop_gate = import_gate()
        seen: list[list[str]] = []

        def fake_run(argv, **kwargs):
            seen.append(argv)
            return subprocess.CompletedProcess(argv, 0, "", "")

        with (
            mock.patch.object(stop_gate.shutil, "which", return_value="C:/x/npm.cmd"),
            mock.patch.object(stop_gate.subprocess, "run", fake_run),
            mock.patch.object(
                sys, "stdin", io.TextIOWrapper(io.BytesIO(stop_event(".").encode()))
            ),
        ):
            stop_gate.main(["--check", "npm test"])
        self.assertEqual(seen, [["C:/x/npm.cmd", "test"]])

    def test_windows_split_keeps_backslashes_and_drops_quotes(self) -> None:
        stop_gate = import_gate()
        cases = {
            r"C:\Python\python.exe -m unittest": [
                r"C:\Python\python.exe",
                "-m",
                "unittest",
            ],
            r'"C:\Program Files\Py\py.exe" -3 -c "print(1)"': [
                r"C:\Program Files\Py\py.exe",
                "-3",
                "-c",
                "print(1)",
            ],
        }
        for command, words in cases.items():
            with self.subTest(command=command):
                self.assertEqual(stop_gate.split_command(command, windows=True), words)
        self.assertEqual(
            stop_gate.split_command("sh -c 'echo a b'", windows=False),
            ["sh", "-c", "echo a b"],
        )

    def test_empty_or_unbalanced_check_is_usage_error(self) -> None:
        for check in ("", "   ", "echo 'unterminated"):
            with self.subTest(check=check):
                result = run(stop_event("."), "--check", check)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("stop_gate: --check", result.stderr)
                self.assertNotIn("Traceback", result.stderr)

    def test_wrong_event_is_rejected(self) -> None:
        stdin = json.dumps({"hook_event_name": "SessionStart"})
        self.assertEqual(run(stdin, "--check", "true").returncode, 2)


if __name__ == "__main__":
    unittest.main()
