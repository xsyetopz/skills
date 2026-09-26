"""Tests for check_stats.py and check_evidence_note.py (stdlib only)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_evidence_note as notes
import check_stats as stats

EXAMPLES = Path(__file__).resolve().parents[1] / "assets/examples"


class PValueTests(unittest.TestCase):
    """Critical values from standard tables give p = .05."""

    def test_table_critical_values(self) -> None:
        cases = [
            ("t", 2.048, 28, None),
            ("F", 4.196, 1, 28),
            ("chi2", 3.841, 1, None),
            ("z", 1.960, None, None),
        ]
        for test, stat, df1, df2 in cases:
            with self.subTest(test=test):
                self.assertAlmostEqual(stats.p_value(test, stat, df1, df2), 0.05, 3)

    def test_chi2_with_four_df(self) -> None:
        self.assertAlmostEqual(stats.p_value("chi2", 9.488, 4, None), 0.05, 3)

    def test_t_squared_equals_f_with_one_numerator_df(self) -> None:
        self.assertAlmostEqual(
            stats.p_value("t", 2.5, 20, None), stats.p_value("F", 6.25, 1, 20), 10
        )


def reports(text: str) -> list[bool]:
    return [stats.check_report(m)[0] for m in stats.REPORT.finditer(text)]


class ReportTests(unittest.TestCase):
    def test_consistent_and_inconsistent(self) -> None:
        self.assertEqual(reports("t(28) = 2.20, p = .036"), [True])
        self.assertEqual(reports("t(28) = 1.20, p = .03"), [False])

    def test_rounding_of_the_statistic_is_allowed(self) -> None:
        # 2.2 could be 2.15..2.25 -> p .033..0.040; p = .040 is consistent.
        self.assertEqual(reports("t(28) = 2.2, p = .040"), [True])

    def test_inequalities(self) -> None:
        self.assertEqual(reports("F(2, 57) = 3.40, p < .05"), [True])
        self.assertEqual(reports("F(2, 57) = 3.40, p < .01"), [False])
        self.assertEqual(reports("z = 1.00, p > .05"), [True])

    def test_correlation_at_or_beyond_one(self) -> None:
        self.assertEqual(reports("r(48) = .998, p < .001"), [True])
        self.assertEqual(reports("r(48) = 1.00, p < .001"), [True])
        self.assertEqual(reports("r(48) = -1.00, p = .04"), [False])
        (match,) = stats.REPORT.finditer("r(48) = 1.20, p < .001")
        result = stats.assess(match)
        self.assertFalse(result["consistent"])
        self.assertIn("outside -1..1", result["detail"])

    def test_example_results_file_flags_one(self) -> None:
        text = (EXAMPLES / "results-section.txt").read_text()
        self.assertEqual(reports(text).count(False), 1)


class StatsCommandLineTests(unittest.TestCase):
    def test_json_report(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = stats.main([str(EXAMPLES / "results-section.txt"), "--json"])
        report = json.loads(out.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(report["count"], len(report["reports"]))
        self.assertEqual(report["inconsistent"], 1)
        (flagged,) = [r for r in report["reports"] if not r["consistent"]]
        self.assertEqual(flagged["test"], "t")
        self.assertLess(flagged["low"], flagged["computed_p"], flagged)

    def test_missing_df_has_null_values(self) -> None:
        (match,) = stats.REPORT.finditer("t = 2.0, p = .05")
        result = stats.assess(match)
        self.assertFalse(result["consistent"])
        self.assertIsNone(result["computed_p"])
        self.assertEqual(result["detail"], "missing degrees of freedom")


class EvidenceNoteCommandLineTests(unittest.TestCase):
    def test_json_report(self) -> None:
        good = str(EXAMPLES / "note-supported.md")
        bad = str(EXAMPLES / "note-abstract-only.md")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            status = notes.main([good, bad, "--json"])
        report = json.loads(out.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(report["failed"], 1)
        self.assertEqual(report["notes"][0], {"file": good, "ok": True, "problems": []})
        self.assertIn("missing field Updates", report["notes"][1]["problems"])

    def test_usage_errors_return_2(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(notes.main([]), 2)
            self.assertEqual(notes.main(["/nonexistent/note.md"]), 2)
        self.assertIn("cannot read /nonexistent/note.md", err.getvalue())


class EvidenceNoteTests(unittest.TestCase):
    def test_full_text_note_passes(self) -> None:
        self.assertEqual(notes.check((EXAMPLES / "note-supported.md").read_text()), [])

    def test_abstract_only_support_is_rejected(self) -> None:
        problems = notes.check((EXAMPLES / "note-abstract-only.md").read_text())
        self.assertIn(
            "supported from abstract only: read the full text first", problems
        )
        self.assertIn("missing field Updates", problems)

    def test_unresolved_from_metadata_is_acceptable(self) -> None:
        text = (EXAMPLES / "note-supported.md").read_text()
        text = text.replace("Status: full text", "Status: metadata").replace(
            "Conclusion: supported, for the benchmark setting only.",
            "Conclusion: unresolved until the full text is read.",
        )
        self.assertEqual(notes.check(text), [])


if __name__ == "__main__":
    unittest.main()
