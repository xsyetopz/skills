"""CLI errors must fail regardless of presentation format."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parent
VALID_CHANGELOG = """# Changelog
All notable changes follow Keep a Changelog and Semantic Versioning.
## [Unreleased]
### Fixed
- Correct an issue.
## [1.0.0] - 2026-01-01
### Added
- Initial release.
"""


class ValidatorTests(unittest.TestCase):
    def run_cli(self, script, args, mode, cwd):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / script), *args, *mode],
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_semver_valid_invalid_and_missing_arguments(self):
        with tempfile.TemporaryDirectory() as tmp:
            for args, status in [
                (["1.2.3", "v2.0.0-rc.1+build.9"], 0),
                (["1.2.3", "01.2.3"], 1),
                ([], 1),
                (["--unknown"], 2),
            ]:
                for mode in ([], ["--json"]):
                    with self.subTest(args=args, mode=mode):
                        result = self.run_cli("audit_semver.py", args, mode, tmp)
                        self.assertEqual(result.returncode, status, result.stderr)
                        if mode and args and args[0] != "--unknown":
                            records = json.loads(result.stdout)
                            self.assertIsInstance(records, list)
                            self.assertEqual(
                                any(not r["valid"] for r in records), status == 1
                            )

    def test_changelog_valid_invalid_empty_and_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            for text, status in [
                (VALID_CHANGELOG, 0),
                ("# Changes\n", 1),
                ("", 1),
                (None, 1),
            ]:
                path = Path(tmp) / "CHANGELOG.md"
                if path.exists():
                    path.unlink()
                if text is not None:
                    path.write_text(text)
                for mode in ([], ["--json"]):
                    with self.subTest(text=text, mode=mode):
                        result = self.run_cli(
                            "audit_changelog.py", [str(path)], mode, tmp
                        )
                        self.assertEqual(result.returncode, status, result.stderr)
                        if mode:
                            record = json.loads(result.stdout)
                            self.assertEqual(
                                set(record), {"path", "findings", "versions"}
                            )
                            self.assertEqual(
                                any(
                                    f["severity"] == "error" for f in record["findings"]
                                ),
                                status == 1,
                            )

    def test_source_errors_and_invalid_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ([], ["--json"]):
                for args in (["--from-changelog", "missing.md"], ["--from-tags"]):
                    result = self.run_cli("audit_semver.py", args, mode, tmp)
                    self.assertEqual(result.returncode, 1, result.stderr)
                result = self.run_cli("audit_changelog.py", ["--unknown"], mode, tmp)
                self.assertEqual(result.returncode, 2)

    def test_changelog_extraction_and_warning_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CHANGELOG.md"
            path.write_text(VALID_CHANGELOG)
            for mode in ([], ["--json"]):
                result = self.run_cli(
                    "audit_semver.py", ["--from-changelog", str(path)], mode, tmp
                )
                self.assertEqual(result.returncode, 0, result.stderr)

            path.write_text(VALID_CHANGELOG.replace(" and Semantic Versioning", ""))
            for mode in ([], ["--json"]):
                result = self.run_cli("audit_changelog.py", [str(path)], mode, tmp)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_unreadable_source_types_fail_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "invalid.md"
            bad.write_bytes(b"\xff\xfe")
            for path in (Path(tmp), bad):
                for mode in ([], ["--json"]):
                    for script, args in (
                        ("audit_semver.py", ["--from-changelog", str(path)]),
                        ("audit_changelog.py", [str(path)]),
                    ):
                        with self.subTest(path=path, mode=mode, script=script):
                            result = self.run_cli(script, args, mode, tmp)
                            self.assertEqual(result.returncode, 1)
                            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
