"""Tests for check_stats.py (stdlib only)."""

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

import check_stats as stats

RESULTS = """\
Participants in the intervention group scored higher, t(28) = 2.20, p = .036.
The three-group comparison was significant, F(2, 57) = 3.40, p < .05.
Completion rates differed, chi2(1) = 4.10, p = .043.
The secondary outcome also differed, t(28) = 1.20, p = .03.
Accuracy correlated with training time, r(48) = .30, p = .034.
"""


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
        self.assertEqual(reports(RESULTS).count(False), 1)


class StatsCommandLineTests(unittest.TestCase):
    def test_json_report(self) -> None:
        out = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "results.txt"
            path.write_text(RESULTS)
            with contextlib.redirect_stdout(out):
                status = stats.main([str(path), "--json"])
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


if __name__ == "__main__":
    unittest.main()
