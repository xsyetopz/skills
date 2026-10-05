"""Grammar, precedence, bump, and command-line tests for semver.py.

Expected values come from the Semantic Versioning 2.0.0 specification
(https://semver.org/spec/v2.0.0.html), not from the implementation.
"""

import io
import json
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import semver

SCRIPT = Path(__file__).resolve().parent / "semver.py"

# Spec item 11, example 4, in ascending order.
SPEC_CHAIN = [
    "1.0.0-alpha",
    "1.0.0-alpha.1",
    "1.0.0-alpha.beta",
    "1.0.0-beta",
    "1.0.0-beta.2",
    "1.0.0-beta.11",
    "1.0.0-rc.1",
    "1.0.0",
]


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = semver.main(list(args))
        except SystemExit as exit_:  # argparse usage errors
            code = exit_.code if isinstance(exit_.code, int) else 2
    return code, out.getvalue(), err.getvalue()


class GrammarTests(unittest.TestCase):
    def test_valid(self):
        for text in (
            "0.0.0",
            "1.2.3",
            "10.20.30",
            "1.0.0-0A",  # alphanumeric: digits then a letter
            "1.0.0-0",
            "1.0.0-x-y-z.--",  # hyphens are identifier characters
            "1.0.0--",
            "1.0.0-alpha+001",  # build identifiers may have leading zeros
            "1.0.0+20130313144700",
            "1.0.0-beta+exp.sha.5114f85",
            "1.0.0+21AF26D3----117B344092BD",
            "1.0.0-00A",  # alphanumeric, so leading zeros are allowed
        ):
            with self.subTest(text):
                self.assertEqual(str(semver.parse(text)), text)

    def test_invalid_with_reason(self):
        for text, reason in (
            ("1.2", "MAJOR.MINOR.PATCH"),
            ("1.2.3.4", "MAJOR.MINOR.PATCH"),
            ("01.2.3", "leading zero"),
            ("1.02.3", "leading zero"),
            ("1.2.03", "leading zero"),
            ("v1.2.3", "'v'"),
            ("1.2.3-01", "leading zero"),  # numeric pre-release identifier
            ("1.2.3-alpha.01", "leading zero"),
            ("1.2.3-", "empty"),
            ("1.2.3-alpha..1", "empty"),
            ("1.2.3-alpha.", "empty"),
            ("1.2.3+", "empty"),
            ("1.2.3+build..1", "empty"),
            ("1.2.3-alpha_1", "character"),
            ("1.2.3+build+2", "character"),
            ("1.2.3-é", "character"),
            ("1.2.3-\u0661", "character"),  # Arabic-Indic digit is not ASCII
            ("a.b.c", "not a number"),
            ("-1.2.3", "MAJOR.MINOR.PATCH"),
            ("1.x.3", "not a number"),
            ("1.2.3\n", "not a number"),  # "$" alone also matches before "\n"
            ("", "MAJOR.MINOR.PATCH"),
        ):
            with self.subTest(text), self.assertRaisesRegex(ValueError, reason):
                semver.parse(text)

    def test_numbers_have_no_size_limit(self):
        big = "9" * 5000  # past Python's default 4300-digit int() limit
        self.assertEqual(semver.parse(f"{big}.0.0").major, int(big))


class PrecedenceTests(unittest.TestCase):
    def test_spec_chain_pairwise(self):
        for i, lower in enumerate(SPEC_CHAIN):
            for higher in SPEC_CHAIN[i + 1 :]:
                with self.subTest(lower=lower, higher=higher):
                    a, b = semver.parse(lower), semver.parse(higher)
                    self.assertEqual(semver.compare(a, b), -1)
                    self.assertEqual(semver.compare(b, a), 1)

    def test_core_is_numeric(self):
        self.assertEqual(
            semver.compare(semver.parse("1.10.0"), semver.parse("1.9.0")), 1
        )
        self.assertEqual(
            semver.compare(semver.parse("2.0.0"), semver.parse("10.0.0")), -1
        )

    def test_numeric_identifier_below_alphanumeric(self):
        self.assertEqual(
            semver.compare(semver.parse("1.0.0-1"), semver.parse("1.0.0-0A")), -1
        )

    def test_alphanumeric_is_ascii_order(self):
        # ASCII: uppercase sorts before lowercase, '-' before digits.
        self.assertEqual(
            semver.compare(semver.parse("1.0.0-Z"), semver.parse("1.0.0-a")), -1
        )
        self.assertEqual(
            semver.compare(semver.parse("1.0.0--"), semver.parse("1.0.0-0A")), -1
        )

    def test_build_metadata_ignored(self):
        for a, b in (
            ("1.0.0+a", "1.0.0+b"),
            ("1.0.0", "1.0.0+build.1"),
            ("1.0.0-rc.1+x", "1.0.0-rc.1+y.2"),
        ):
            with self.subTest(a=a, b=b):
                self.assertEqual(semver.compare(semver.parse(a), semver.parse(b)), 0)

    def test_sort_is_precedence_and_stable_for_build(self):
        shuffled = [*reversed(SPEC_CHAIN), "1.0.0+b", "1.0.0+a"]
        ordered = [str(v) for v in semver.sort_versions(shuffled)]
        self.assertEqual(ordered, [*SPEC_CHAIN, "1.0.0+b", "1.0.0+a"])


class BumpTests(unittest.TestCase):
    def bump(self, version, part, pre_id=None, build=None):
        return str(semver.bump(semver.parse(version), part, pre_id, build))

    def test_resets(self):
        self.assertEqual(self.bump("1.4.7", "major"), "2.0.0")
        self.assertEqual(self.bump("1.4.7", "minor"), "1.5.0")
        self.assertEqual(self.bump("1.4.7", "patch"), "1.4.8")
        self.assertEqual(self.bump("0.9.3", "minor"), "0.10.0")

    def test_core_bump_drops_prerelease_and_build(self):
        self.assertEqual(self.bump("1.4.7-rc.1+sha.abc", "patch"), "1.4.8")
        self.assertEqual(self.bump("1.4.7+sha.abc", "minor"), "1.5.0")

    def test_core_bump_can_start_a_train(self):
        self.assertEqual(self.bump("1.4.7", "major", "rc"), "2.0.0-rc.1")
        self.assertEqual(self.bump("1.4.7", "minor", "beta"), "1.5.0-beta.1")

    def test_prerelease_from_final_bumps_patch(self):
        self.assertEqual(self.bump("1.4.7", "prerelease", "alpha"), "1.4.8-alpha.1")

    def test_prerelease_from_final_needs_id(self):
        with self.assertRaisesRegex(semver.UsageError, "--pre-id"):
            self.bump("1.4.7", "prerelease")

    def test_prerelease_increments_last_numeric(self):
        self.assertEqual(self.bump("2.0.0-rc.1", "prerelease"), "2.0.0-rc.2")
        self.assertEqual(self.bump("2.0.0-beta.9", "prerelease"), "2.0.0-beta.10")
        self.assertEqual(self.bump("2.0.0-alpha.1.x", "prerelease"), "2.0.0-alpha.2.x")
        self.assertEqual(self.bump("2.0.0-rc.1", "prerelease", "rc"), "2.0.0-rc.2")

    def test_prerelease_appends_one_without_numeric(self):
        self.assertEqual(self.bump("2.0.0-rc", "prerelease"), "2.0.0-rc.1")
        self.assertEqual(self.bump("2.0.0-0A", "prerelease"), "2.0.0-0A.1")

    def test_prerelease_switches_train_forward_only(self):
        self.assertEqual(self.bump("2.0.0-beta.3", "prerelease", "rc"), "2.0.0-rc.1")
        with self.assertRaisesRegex(ValueError, "lower"):
            self.bump("2.0.0-rc.2", "prerelease", "alpha")

    def test_every_bump_increases_precedence(self):
        for version, part, pre_id in (
            ("1.4.7", "major", None),
            ("1.4.7", "minor", None),
            ("1.4.7", "patch", None),
            ("1.4.7", "prerelease", "rc"),
            ("2.0.0-rc.1", "prerelease", None),
            ("2.0.0-rc.1", "release", None),
        ):
            with self.subTest(version=version, part=part):
                old = semver.parse(version)
                new = semver.bump(old, part, pre_id, None)
                self.assertEqual(semver.compare(old, new), -1)

    def test_release_drops_prerelease(self):
        self.assertEqual(self.bump("2.0.0-rc.3+ci.7", "release"), "2.0.0")
        with self.assertRaisesRegex(ValueError, "no pre-release"):
            self.bump("2.0.0", "release")

    def test_build_replaced_and_validated(self):
        self.assertEqual(
            self.bump("1.0.0+old", "patch", build="sha.0a1b2c3"), "1.0.1+sha.0a1b2c3"
        )
        self.assertEqual(self.bump("1.0.0", "patch", build="007"), "1.0.1+007")
        for bad in ("", "a..b", "a_b", "a+b"):
            with self.subTest(bad), self.assertRaises(semver.UsageError):
                self.bump("1.0.0", "patch", build=bad)

    def test_pre_id_validated(self):
        for bad in ("", "01", "rc_1", "rc..1"):
            with self.subTest(bad), self.assertRaises(semver.UsageError):
                self.bump("1.0.0", "prerelease", bad)


class CommandLineTests(unittest.TestCase):
    def test_check_exit_codes(self):
        self.assertEqual(run("check", "1.2.3", "1.0.0-rc.1+b")[0], 0)
        code, out, _ = run("check", "1.2.3", "1.02.3")
        self.assertEqual(code, 1)
        self.assertIn("FAIL  1.02.3", out)

    def test_check_json(self):
        code, out, _ = run("check", "--json", "1.0.0-rc.1+b.5", "v1.0.0")
        self.assertEqual(code, 1)
        first, second = json.loads(out)
        self.assertEqual(first["prerelease"], ["rc", "1"])
        self.assertEqual(first["build"], ["b", "5"])
        self.assertFalse(second["valid"])

    def test_check_tag_prefix(self):
        version, note = semver.from_tag("v1.2.3")
        self.assertEqual(str(version), "1.2.3")
        self.assertIn("'v'", note)
        self.assertEqual(semver.from_tag("1.2.3"), (semver.parse("1.2.3"), ""))

    def test_compare(self):
        self.assertEqual(run("compare", "1.0.0-rc.1", "1.0.0"), (0, "<\n", ""))
        self.assertEqual(run("compare", "1.0.0+a", "1.0.0+b"), (0, "=\n", ""))
        self.assertEqual(run("compare", "1.10.0", "1.9.0"), (0, ">\n", ""))
        code, _, err = run("compare", "1.0", "1.0.0")
        self.assertEqual(code, 1)
        self.assertIn("MAJOR.MINOR.PATCH", err)

    def test_sort(self):
        code, out, _ = run("sort", "1.0.0", "1.0.0-rc.1", "0.9.0")
        self.assertEqual((code, out), (0, "0.9.0\n1.0.0-rc.1\n1.0.0\n"))
        self.assertEqual(run("sort", "1.0.0", "x")[0], 1)

    def test_bump_usage_errors_exit_2(self):
        self.assertEqual(run("bump", "1.0.0", "prerelease")[0], 2)
        self.assertEqual(run("bump", "1.0.0", "patch", "--build", "a_b")[0], 2)
        self.assertEqual(run("bump", "1.0.0", "huge")[0], 2)
        self.assertEqual(run()[0], 2)

    def test_bump_prints_version(self):
        self.assertEqual(
            run("bump", "1.0.0", "minor", "--build", "sha.1"), (0, "1.1.0+sha.1\n", "")
        )

    def test_help_documents_exit_status(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("Exit status", result.stdout)


if __name__ == "__main__":
    unittest.main()
