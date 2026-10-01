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

    def audit_text(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CHANGELOG.md"
            path.write_text(text)
            result = self.run_cli("audit_changelog.py", [str(path)], ["--json"], tmp)
            record = json.loads(result.stdout)
            self.assertEqual(
                result.returncode,
                int(any(f["severity"] == "error" for f in record["findings"])),
            )
            return record

    def test_empty_unreleased_is_valid_but_empty_categories_are_not(self):
        record = self.audit_text("# Changelog\n\n## [Unreleased]\n")
        self.assertFalse([f for f in record["findings"] if f["severity"] == "error"])
        for suffix in ("", "<!-- pending -->\n", "- \n"):
            with self.subTest(suffix=suffix):
                record = self.audit_text(
                    "# Changelog\n\n## [1.0.0] - 2026-01-01\n\n### Fixed\n\n" + suffix
                )
                self.assertIn("empty-category", [f["rule"] for f in record["findings"]])

    def test_malformed_release_headers_are_reported(self):
        for header, rule in (
            ("## [1.2] - 2026-01-01", "semver-format"),
            ("## [1.0.0]", "date-format"),
            ("## [1.0.0] - yesterday", "date-format"),
            ("## [1.0.0] - 2026-02-30", "date-format"),
            ("## [1.0.0] - 20260101", "date-format"),
        ):
            with self.subTest(header=header):
                record = self.audit_text(
                    "# Changelog\n\n" + header + "\n### Fixed\n- Bug fix.\n"
                )
                self.assertIn(rule, [f["rule"] for f in record["findings"]])

    def test_duplicate_releases_and_misplaced_unreleased(self):
        release = "## [1.0.0] - 2026-01-01\n### Fixed\n- Bug fix.\n"
        for text, rule in (
            (release + release, "duplicate-version"),
            (release + "## [Unreleased]\n", "unreleased-order"),
            ("## [Unreleased]\n## [Unreleased]\n", "duplicate-version"),
            ("### Fixed\n- Bug fix.\n" + release, "orphan-category"),
        ):
            with self.subTest(rule=rule):
                record = self.audit_text("# Changelog\n" + text)
                self.assertIn(rule, [f["rule"] for f in record["findings"]])

    def test_markdown_examples_are_not_release_sections(self):
        examples = (
            "```markdown\n## [9.0.0] - 2099-01-01\n### Invalid\n```\n",
            "~~~\n## [9.0.0] - 2099-01-01\n~~~\n",
            "    ## [9.0.0] - 2099-01-01\n",
            "> ## [9.0.0] - 2099-01-01\n",
            "<!--\n## [9.0.0] - 2099-01-01\n-->\n",
        )
        for example in examples:
            with self.subTest(example=example):
                text = VALID_CHANGELOG + "\n" + example
                record = self.audit_text(text)
                self.assertEqual(record["versions"], ["1.0.0"])
                self.assertFalse(
                    [f for f in record["findings"] if f["severity"] == "error"]
                )

    def test_rendered_release_headings_and_yanked_marker(self):
        for heading, definitions in (
            ("## [1.0.0](https://example.com/tag) - 2026-01-01 [YANKED]", ""),
            ("## [1.0.0] - 2026-01-01", "[1.0.0]: https://example.com/tag\n"),
            ("## 1.0.0 - 2026-01-01 ##", ""),
            ("[1.0.0] - 2026-01-01\n---", ""),
        ):
            with self.subTest(heading=heading):
                record = self.audit_text(
                    "# Changelog\n\n"
                    + heading
                    + "\n\n### Fixed\n\n- Bug fix.\n\n"
                    + definitions
                )
                self.assertEqual(record["versions"], ["1.0.0"])
                self.assertFalse(
                    [f for f in record["findings"] if f["severity"] == "error"]
                )

    def test_bounded_markdown_parser_regressions(self):
        sys.path.insert(0, str(SCRIPTS))
        from changelog_markdown import Section, sections

        text = """# Changelog
## [1.0.0](https://example.com/tag) - 2026-01-01 ##
### Fixed
<!--
Text and ## headings in comments do not count.
-->
```markdown
## [9.0.0] - 2099-01-01
```
> #### A nested heading is not content
- #### Nor is a list heading
<details>
hosted HTML is outside the profile
</details>

[](<https://example.com>)

### Added
    indented code is content
[Unreleased]
---
### Changed
~~~text
fenced code is content
~~~
"""
        self.assertEqual(
            sections(text),
            [
                Section(1, "Changelog", 1),
                Section(2, "1.0.0 - 2026-01-01", 2),
                Section(3, "Fixed", 3, True),
                Section(3, "Added", 18, True),
                Section(2, "[Unreleased]", 20),
                Section(3, "Changed", 22, True),
            ],
        )

    def test_fence_markers_and_top_level_heading_boundaries(self):
        sys.path.insert(0, str(SCRIPTS))
        from changelog_markdown import Section, sections

        text = """   # Changelog
####### not a heading
##NoSpace
    ## indented
~~~
## fenced
~~~~
> ## quoted
1. ## listed
## Real
"""
        self.assertEqual(
            sections(text),
            [Section(1, "Changelog", 1, True), Section(2, "Real", 10)],
        )

    def test_nested_category_content_and_duplicate_categories(self):
        release = "# Changelog\n## [1.0.0] - 2026-01-01\n"
        record = self.audit_text(release + "### Fixed\n#### Search\n- Keep filters.\n")
        self.assertFalse([f for f in record["findings"] if f["severity"] == "error"])
        record = self.audit_text(release + "### Fixed\n- Fix A.\n### Fixed\n- Fix B.\n")
        self.assertIn("duplicate-category", [f["rule"] for f in record["findings"]])

    def test_source_errors_and_invalid_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ([], ["--json"]):
                result = self.run_cli("audit_changelog.py", ["--unknown"], mode, tmp)
                self.assertEqual(result.returncode, 2)

    def test_warning_only_changelogs_pass(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "CHANGELOG.md"
            path.write_text(VALID_CHANGELOG.replace(" and Semantic Versioning", ""))
            for mode in ([], ["--json"]):
                result = self.run_cli("audit_changelog.py", [str(path)], mode, tmp)
                self.assertEqual(result.returncode, 0, result.stderr)

            path.write_text(VALID_CHANGELOG.replace("# Changelog", "# Changes"))
            for mode in ([], ["--json"]):
                result = self.run_cli("audit_changelog.py", [str(path)], mode, tmp)
                self.assertEqual(result.returncode, 0, result.stderr)

            path.write_text(
                VALID_CHANGELOG.replace(
                    "All notable changes follow Keep a Changelog and Semantic Versioning.\n",
                    "",
                )
            )
            for mode in ([], ["--json"]):
                result = self.run_cli("audit_changelog.py", [str(path)], mode, tmp)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_invalid_release_versions_are_reported(self):
        for version in ("1.2", "v1.2.3", "1.2.3-", "1٢.2.3", "1.2.3-01"):
            with self.subTest(version=version):
                record = self.audit_text(
                    VALID_CHANGELOG + f"## [{version}] - 2025-01-01\n### Fixed\n- X.\n"
                )
                self.assertIn(version, record["versions"])
                self.assertIn("semver-format", [f["rule"] for f in record["findings"]])

    def test_unreadable_source_types_fail_without_tracebacks(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "invalid.md"
            bad.write_bytes(b"\xff\xfe")
            for path in (Path(tmp), bad):
                for mode in ([], ["--json"]):
                    with self.subTest(path=path, mode=mode):
                        result = self.run_cli(
                            "audit_changelog.py", [str(path)], mode, tmp
                        )
                        self.assertEqual(result.returncode, 1)
                        self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
