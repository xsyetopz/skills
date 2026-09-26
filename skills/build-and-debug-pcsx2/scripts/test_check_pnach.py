"""Tests for check_pnach.py against the bundled good, bad, and warn fixtures."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "check_pnach.py"
FIXTURES = HERE.parent / "assets" / "examples" / "pnach"
sys.path.insert(0, str(HERE))

import check_pnach  # noqa: E402

# One bad fixture per loader rule, mapped to the loader's own error text.
BAD = {
    "10000001_fields": "Expected 5 data parameters; only found 4",
    "10000002_place": "Invalid 'place' value '4'",
    "10000003_cpu": "Unrecognized CPU Target: 'ee'",
    "10000004_address": "Malformed address '0x00100000'",
    "10000005_type": "Unrecognized Operand Size: 'dword'",
    "10000006_data": "Malformed data '1234567Z'",
    "10000007_bytes": "Malformed data ''",
    "10000008_dpatch": "Expected 2 fields for each 2 patterns",
    "10000009_aspect": "Stretch is an unknown aspect ratio",
    "1000000A_interlace": "10 is an unknown interlace mode",
    "1000000B_header": "Malformed patch line: [unterminated",
}


def run(*paths: Path | str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *map(str, paths)],
        check=False,
        capture_output=True,
        text=True,
    )


class GoodFixtures(unittest.TestCase):
    def test_good_fixture_has_no_findings(self) -> None:
        result = run(*sorted((FIXTURES / "good").glob("*.pnach")))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(result.stdout.strip(), "0 errors, 0 warnings")

    def test_spaces_around_fields_are_accepted(self) -> None:
        # Patch.cpp splits with StringUtil::SplitString, which strips fields.
        self.assertEqual(check_pnach.check_patch("1, EE, 0010, byte, 01", 1), [])


class BadFixtures(unittest.TestCase):
    def test_each_bad_fixture_reports_its_loader_error(self) -> None:
        for name, expected in BAD.items():
            with self.subTest(name=name):
                result = run(FIXTURES / "bad" / f"{name}.pnach")
                self.assertEqual(result.returncode, 1, result.stdout)
                self.assertIn(expected, result.stdout)

    def test_every_bad_fixture_is_covered(self) -> None:
        names = {p.stem for p in (FIXTURES / "bad").glob("*.pnach")}
        self.assertEqual(names, set(BAD))

    def test_enum_matching_is_case_sensitive(self) -> None:
        levels = [f.level for f in check_pnach.check_patch("1,EE,0,Word,1", 1)]
        self.assertEqual(levels, ["error"])


class Warnings(unittest.TestCase):
    def test_warn_fixture_exits_zero_with_each_warning(self) -> None:
        result = run(FIXTURES / "warn" / "10000000_legacy.pnach")
        self.assertEqual(result.returncode, 0, result.stdout)
        for text in (
            "cut at '//'",
            "before the first [group]",
            "disables patches.zip",
            "wider than byte",
            "unknown key 'patchs'",
            "drops the last nibble",
            "not a multiple of 4",
            "duplicate group [g]",
        ):
            self.assertIn(text, result.stdout)

    def test_name_without_crc_is_flagged(self) -> None:
        result = run(FIXTURES / "warn" / "SLUS-20062_notes.pnach")
        self.assertIn("file name does not match", result.stdout)

    def test_serial_crc_and_crc_only_names_pass(self) -> None:
        # The loader's wildcard match ignores case, so lower-case CRCs load.
        names = (
            "SLUS-20062_ABCDEF01.pnach",
            "slus-20062_abcdef01.pnach",
            "ABCDEF01_extra.pnach",
        )
        with tempfile.TemporaryDirectory() as tmp:
            for name in names:
                path = Path(tmp) / name
                path.write_text("[g]\npatch=0,EE,00100000,word,0\n")
                self.assertEqual(check_pnach.check_file(path), [], name)


class Usage(unittest.TestCase):
    def test_missing_file_is_usage_error(self) -> None:
        result = run(FIXTURES / "does-not-exist.pnach")
        self.assertEqual(result.returncode, 2)

    @unittest.skipIf(os.name == "nt" or os.geteuid() == 0, "needs POSIX non-root")
    def test_unreadable_file_is_usage_error_not_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ABCDEF01.pnach"
            path.write_text("[g]\n")
            path.chmod(0)
            try:
                result = run(path)
            finally:
                path.chmod(0o600)
        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_help_documents_exit_status(self) -> None:
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Exit status:", result.stdout)

    def test_negative_limit_is_usage_error(self) -> None:
        result = run(FIXTURES / "good", "--limit", "-1")
        self.assertEqual(result.returncode, 2)
        self.assertIn("--limit", result.stderr)


class NonAsciiDigits(unittest.TestCase):
    # std::from_chars reads ASCII digits only; str.isdigit() also accepts
    # superscripts that int() rejects, which used to crash the checker.
    def test_superscript_dpatch_version_is_an_error(self) -> None:
        findings = check_pnach.check_dpatch("\u00b2,1,1,0,0,0,0", 1)
        self.assertEqual([f.level for f in findings], ["error"])
        self.assertIn("Malformed version/type", findings[0].message)

    def test_superscript_interlace_mode_is_an_error(self) -> None:
        findings = check_pnach.check_interlace("\u00b2", 1)
        self.assertEqual([f.level for f in findings], ["error"])


class JsonAndLimit(unittest.TestCase):
    def test_json_report_counts_bad_fixtures(self) -> None:
        paths = sorted((FIXTURES / "bad").glob("*.pnach"))
        result = run(*paths, "--json")
        self.assertEqual(result.returncode, 1)
        report = json.loads(result.stdout)
        self.assertEqual(report["errors"], len(BAD))
        summary = run(*paths).stdout.splitlines()[-1]
        self.assertEqual(
            summary, f"{report['errors']} errors, {report['warnings']} warnings"
        )
        self.assertEqual(len(report["findings"]), report["errors"] + report["warnings"])
        first = report["findings"][0]
        self.assertEqual(set(first), {"file", "line", "level", "message"})
        self.assertEqual(first["level"], "error")

    def test_json_good_fixture_is_empty(self) -> None:
        result = run(*sorted((FIXTURES / "good").glob("*.pnach")), "--json")
        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            json.loads(result.stdout), {"findings": [], "errors": 0, "warnings": 0}
        )

    def test_limit_caps_lines_but_summary_counts_all(self) -> None:
        paths = sorted((FIXTURES / "bad").glob("*.pnach"))
        result = run(*paths, "--limit", "3")
        self.assertEqual(result.returncode, 1)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 4)
        self.assertEqual(lines[-1], run(*paths).stdout.splitlines()[-1])
        self.assertIn("showing 3 of", result.stderr)

    def test_limit_applies_to_json_findings(self) -> None:
        paths = sorted((FIXTURES / "bad").glob("*.pnach"))
        report = json.loads(run(*paths, "--json", "--limit", "2").stdout)
        self.assertEqual(len(report["findings"]), 2)
        self.assertEqual(report["errors"], len(BAD))


if __name__ == "__main__":
    unittest.main()
