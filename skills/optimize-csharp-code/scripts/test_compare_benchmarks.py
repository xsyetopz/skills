"""Independent numerical fixtures and adversarial CSV cases; no .NET required."""

import contextlib
import csv
import io
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from compare_benchmarks import InputError, compare, duration_ns, main, read_table


class DurationTests(unittest.TestCase):
    def test_scientific_notation_is_not_truncated(self):
        self.assertEqual(duration_ns("1e3 ns"), Decimal(1000))
        self.assertEqual(duration_ns("2.5e-3 ms"), Decimal(2500))

    def test_units_and_whitespace(self):
        for unit in ("us", "µs", "μs"):
            with self.subTest(unit=unit):
                self.assertEqual(duration_ns(" 1.5\u00a0" + unit), Decimal(1500))
        self.assertEqual(duration_ns(".01 s"), Decimal(10000000))

    def test_decimal_comma_is_explicit(self):
        self.assertEqual(duration_ns("1,5 ms", decimal=","), Decimal(1500000))
        with self.assertRaises(InputError):
            duration_ns("1,5 ms")

    def test_unitless_requires_an_explicit_unit(self):
        self.assertEqual(duration_ns("10", unit="ns"), Decimal(10))
        with self.assertRaises(InputError):
            duration_ns("10")

    def test_rejects_ambiguous_or_invalid_measurements(self):
        for value in (
            "NA",
            "NaN ns",
            "Infinity ns",
            "-1 ns",
            "0 ns",
            "1,000 ns",
            "10 bananas",
            "10 ns trailing junk",
            "",
            "1e+ ns",
            "1 000 ns",
        ):
            with self.subTest(value=value), self.assertRaises(InputError):
                duration_ns(value)


class TableTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def table(self, name, text):
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def read(self, text, **kwargs):
        return read_table(
            self.table("input.csv", text),
            ["Method", "Job", "N"],
            "Mean",
            ["Error"],
            **kwargs,
        )

    def test_complete_identity_and_bom(self):
        rows = self.read(
            "\ufeffMethod,Job,N,Mean,Error\nA,J,1,1e3 ns,1 ns\nA,J,2,2 us,1 ns\n"
        )
        self.assertEqual(
            rows, {("A", "J", "1"): Decimal(1000), ("A", "J", "2"): Decimal(2000)}
        )

    def test_quoted_identity_preserved(self):
        rows = self.read('Method,Job,N,Mean,Error\n"A,quoted",J,1,10 ns,0 ns\n')
        self.assertIn(("A,quoted", "J", "1"), rows)

    def test_duplicate_identity_fails(self):
        with self.assertRaisesRegex(InputError, "duplicate identity"):
            self.read("Method,Job,N,Mean,Error\nA,J,1,10 ns,0 ns\nA,J,1,11 ns,0 ns\n")

    def test_unclassified_parameter_fails_instead_of_disappearing(self):
        with self.assertRaisesRegex(InputError, "unclassified"):
            self.read("Method,Job,N,Runtime,Mean,Error\nA,J,1,net10.0,10 ns,0 ns\n")

    def test_invalid_rows_never_yield_success(self):
        for text in (
            "",
            "Method,Job,N,Mean,Error\n",
            "Method,Job,N,Mean,Mean\n",
            "Method,Job,N,Mean,Error\nA,J,1,NA,0 ns\n",
            "Method,Job,N,Mean,Error\nA,J,1,10 ns,0 ns,extra\n",
            "Method,Job,N,Mean,Error\nA,,1,10 ns,0 ns\n",
        ):
            with self.subTest(text=text), self.assertRaises(InputError):
                self.read(text)

    def test_decimal_comma_export(self):
        rows = self.read(
            "Method;Job;N;Mean;Error\nA;J;1;1,5 us;0,1 us\n", delimiter=";", decimal=","
        )
        self.assertEqual(rows[("A", "J", "1")], Decimal(1500))

    def test_cli_exit_codes_and_no_partial_success_output(self):
        base = self.table("base.csv", "Method,Job,N,Mean,Error\nA,J,1,100 ns,0 ns\n")
        candidate = self.table(
            "new.csv", "Method,Job,N,Mean,Error\nA,J,1,106 ns,0 ns\n"
        )
        args = [
            str(base),
            str(candidate),
            "--keys",
            "Method",
            "Job",
            "N",
            "--ignore-columns",
            "Error",
            "--max-regression-percent",
            "5",
        ]
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            self.assertEqual(main(args), 1)
        self.assertEqual(
            list(csv.reader(io.StringIO(stdout.getvalue())))[1][-1], "true"
        )
        candidate.write_text("Method,Job,N,Mean,Error\nA,J,1,105 ns,0 ns\n")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args), 0)
        candidate.write_text("Method,Job,N,Mean,Error\nA,J,2,100 ns,0 ns\n")
        stdout = io.StringIO()
        with (
            contextlib.redirect_stdout(stdout),
            contextlib.redirect_stderr(io.StringIO()),
        ):
            self.assertEqual(main(args), 2)
        self.assertEqual(stdout.getvalue(), "")


class ComparisonTests(unittest.TestCase):
    def test_exact_threshold_and_speedup(self):
        base = {("A",): Decimal(100), ("B",): Decimal(200)}
        cand = {("A",): Decimal(105), ("B",): Decimal(100)}
        result = compare(base, cand, Decimal(5))
        self.assertEqual([row[3] for row in result], [Decimal(5), Decimal(-50)])
        self.assertFalse(any(row[-1] for row in result))

    def test_missing_extra_empty_and_invalid_threshold(self):
        for base, cand, limit in (
            ({("A",): Decimal(1)}, {}, Decimal(0)),
            ({("A",): Decimal(1)}, {("B",): Decimal(1)}, Decimal(0)),
            ({("A",): Decimal(1)}, {("A",): Decimal(1)}, Decimal("NaN")),
            ({("A",): Decimal(1)}, {("A",): Decimal(1)}, Decimal(-1)),
        ):
            with (
                self.subTest(base=base, candidate=cand, limit=limit),
                self.assertRaises(InputError),
            ):
                compare(base, cand, limit)


if __name__ == "__main__":
    unittest.main()
