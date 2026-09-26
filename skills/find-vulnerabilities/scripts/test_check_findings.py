"""Tests for check_findings.py (stdlib only). Run: python3 test_check_findings.py"""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_findings as cf

COMPLETE = """
### F1: SQL injection in user search

- CWE: CWE-89 SQL Injection
- Location: app/search.py:42 `find_user`
- Status: confirmed
- Preconditions: any authenticated user
- Trace: GET /search?q -> search() -> find_user(name)
  -> db.execute(query)
- Impact: reads every row of users
- Evidence: test_tautology_leaks_every_row fails before the fix
- Severity: High, CVSS:3.1/AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N
- Remediation: bind name as a parameter
- Verification: same test passes; legitimate lookup still returns bob
"""


class Vectors(unittest.TestCase):
    def test_valid_examples_from_first_specifications(self) -> None:
        for vector in (
            "CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:L/I:L/A:N",
            "CVSS:3.1/S:U/AV:N/AC:L/PR:H/UI:N/C:L/I:L/A:N",  # any order
            "CVSS:4.0/AV:N/AC:L/AT:N/PR:H/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N",
            "CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N"
            "/E:P/U:Amber",
        ):
            with self.subTest(vector=vector):
                self.assertEqual(cf.vector_problems(vector), [])

    def test_invalid_vectors(self) -> None:
        cases = {
            "CVSS:3.1/AV:N/AC:L/PR:H/UI:N/S:U/C:L/I:L": "missing base",
            "CVSS:3.1/AV:Q/AC:L/PR:H/UI:N/S:U/C:L/I:L/A:N": "AV:Q",
            "CVSS:3.1/AV:N/AV:N/AC:L/PR:H/UI:N/S:U/C:L/I:L/A:N": "more than once",
            "CVSS:4.0/AC:L/AV:N/AT:N/PR:H/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N": (
                "order"
            ),
            "CVSS:4.0/AV:N/AC:L/AT:N/PR:H/UI:R/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N": ("UI:R"),
            "CVSS:2.0/AV:N": "unsupported",
        }
        for vector, expected in cases.items():
            with self.subTest(vector=vector):
                self.assertIn(expected, "; ".join(cf.vector_problems(vector)))


class Findings(unittest.TestCase):
    def test_complete_finding_passes(self) -> None:
        (finding,) = cf.parse(COMPLETE)
        self.assertEqual(cf.problems_for(finding), [])
        self.assertTrue(
            finding["Trace"].endswith("find_user(name) -> db.execute(query)")
        )

    def test_each_gap_is_reported(self) -> None:
        text = (
            COMPLETE.replace("CWE-89 ", "")
            .replace("app/search.py:42", "search module")
            .replace("confirmed", "likely")
            .replace(" -> ", " then ")
            .replace("  -> ", "  then ")
            .replace(
                "- Evidence: test_tautology_leaks_every_row fails before the fix\n", ""
            )
        )
        problems = "; ".join(cf.problems_for(cf.parse(text)[0]))
        for expected in (
            "CWE-<number>",
            "path:line",
            "Status",
            "Trace",
            "missing Evidence",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, problems)

    def test_cli_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good, bad, empty = (Path(tmp) / n for n in ("g.md", "b.md", "e.md"))
            good.write_text(COMPLETE)
            bad.write_text(COMPLETE.replace("- Impact: reads every row of users\n", ""))
            empty.write_text("# Review\n")
            with (
                contextlib.redirect_stdout(io.StringIO()),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                codes = [cf.main([str(p)]) for p in (good, bad, empty)]
        self.assertEqual(codes, [0, 1, 2])

    def test_missing_review_is_input_error(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(cf.main(["/nonexistent/review.md"]), 2)
        self.assertIn("cannot read /nonexistent/review.md", err.getvalue())


if __name__ == "__main__":
    unittest.main()
