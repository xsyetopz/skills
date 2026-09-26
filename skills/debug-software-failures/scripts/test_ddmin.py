"""Tests for ddmin.py (stdlib only; run directly)."""

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

import ddmin


class AlgorithmTests(unittest.TestCase):
    def test_single_trigger_line(self) -> None:
        units = [f"line {i}\n" for i in range(64)]
        units[41] = "BAD\n"

        def fails(candidate: list[str]) -> bool:
            return "BAD\n" in candidate

        self.assertEqual(ddmin.ddmin(units, fails), ["BAD\n"])

    def test_two_lines_needed_together(self) -> None:
        units = [f"{i}\n" for i in range(30)]

        def fails(candidate: list[str]) -> bool:
            return "3\n" in candidate and "27\n" in candidate

        self.assertEqual(sorted(ddmin.ddmin(units, fails)), ["27\n", "3\n"])

    def test_result_is_one_minimal(self) -> None:
        units = list("xxaxxbxxcxx")

        def fails(candidate: list[str]) -> bool:
            text = "".join(candidate)
            return "a" in text and "c" in text

        result = ddmin.ddmin(units, fails)
        for index in range(len(result)):
            self.assertFalse(fails(result[:index] + result[index + 1 :]))


class CommandTests(unittest.TestCase):
    def test_command_oracle_with_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checker = Path(tmp) / "check.py"
            checker.write_text(
                "import sys\n"
                "data = open(sys.argv[1]).read()\n"
                "if 'boom' in data:\n"
                "    raise SystemExit('ValueError: boom')\n"
            )
            source = Path(tmp) / "input.txt"
            source.write_text("".join(f"ok {i}\n" for i in range(20)) + "boom\n")
            out = io.StringIO()
            err = io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = ddmin.main(
                    [
                        str(source),
                        "--oracle",
                        f"{sys.executable} {checker} {{}}",
                        "--fail-text",
                        "ValueError",
                    ]
                )
            self.assertEqual(status, 0)
            self.assertEqual(out.getvalue(), "boom\n")
            self.assertIn("units 21 -> 1", err.getvalue())

    def test_non_failing_input_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.txt"
            source.write_text("fine\n")
            with contextlib.redirect_stderr(io.StringIO()):
                status = ddmin.main([str(source), "--oracle", "true {}"])
            self.assertEqual(status, 1)


class InterfaceTests(unittest.TestCase):
    def run_main(self, *argv: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = ddmin.main(list(argv))
        return status, out.getvalue(), err.getvalue()

    def failing_input(self, tmp: str) -> tuple[Path, str]:
        checker = Path(tmp) / "check.py"
        checker.write_text(
            "import sys\n"
            "if 'boom' in open(sys.argv[1]).read():\n"
            "    raise SystemExit(1)\n"
        )
        source = Path(tmp) / "input.txt"
        source.write_text("a\nb\nboom\nc\n")
        return source, f"{sys.executable} {checker} {{}}"

    def test_json_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, oracle = self.failing_input(tmp)
            status, out, err = self.run_main(str(source), "--oracle", oracle, "--json")
        self.assertEqual(status, 0)
        report = json.loads(out)
        self.assertEqual(report["reduced"], "boom\n")
        self.assertEqual((report["units_before"], report["units_after"]), (4, 1))
        self.assertIsNone(report["output"])
        self.assertIn("units 4 -> 1", err)

    def test_json_with_output_writes_file_and_reports_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source, oracle = self.failing_input(tmp)
            target = str(Path(tmp) / "min.txt")
            status, out, _ = self.run_main(
                str(source), "--oracle", oracle, "--output", target, "--json"
            )
            self.assertEqual(Path(target).read_text(), "boom\n")
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(out)["output"], target)

    def test_missing_oracle_program_is_exit_2_not_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.txt"
            source.write_text("x\n")
            missing = str(Path(tmp) / "no-such-program")
            status, out, err = self.run_main(str(source), "--oracle", f"{missing} {{}}")
        self.assertEqual(status, 2)
        self.assertEqual(out, "")
        self.assertIn("cannot run the oracle", err)

    def test_unbalanced_quotes_in_oracle_is_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "input.txt"
            source.write_text("x\n")
            status, _, err = self.run_main(str(source), "--oracle", "python3 'x {}")
        self.assertEqual(status, 2)
        self.assertIn("not a valid command line", err)

    def test_help_documents_exit_status(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as caught:
            ddmin.main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn("Exit status:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
