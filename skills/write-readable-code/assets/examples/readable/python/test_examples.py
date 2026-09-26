"""Behavior equivalence for every baseline/candidate pair (stdlib only).

Run: python3 test_examples.py
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import names_types as nt
import shape
import state_errors as se

ORDERS: list[dict[str, object]] = [
    {"paid": True, "items": [1], "address": "x"},
    {"paid": False, "items": [1], "address": "x"},
    {"paid": True, "items": [], "address": "x"},
    {"paid": True, "items": [1], "address": ""},
    {"paid": True, "items": [1], "address": "x", "cancelled": True},
    {},
]


def outcome(function, *args):
    try:
        return ("ok", function(*args))
    except Exception as error:  # noqa: BLE001 - comparing any outcome
        return ("error", type(error).__name__, str(error))


class ShapeTests(unittest.TestCase):
    def test_guard_clauses_preserve_order_of_checks(self) -> None:
        for order in ORDERS:
            self.assertEqual(
                outcome(shape.baseline_ship_order, order),
                outcome(shape.candidate_ship_order, order),
            )

    def test_phases_preserve_totals_and_errors(self) -> None:
        cases: list[list[dict[str, object]]] = [
            [],
            [{"price_cents": 250, "quantity": 2}],
            [{"price_cents": 250, "quantity": 2}, {"price_cents": 99, "quantity": 1}],
            [{"price_cents": -1, "quantity": 1}],
            [{"price_cents": 1.5, "quantity": 1}],
            [{"quantity": 1}],
        ]
        for lines in cases:
            self.assertEqual(
                outcome(shape.baseline_invoice_total, lines, 0.2),
                outcome(shape.candidate_invoice_total, lines, 0.2),
            )

    def test_band_lookup_matches_nested_conditional(self) -> None:
        for weight in (0, 100, 101, 2000, 2001, 10000, 10001):
            self.assertEqual(
                shape.baseline_shipping_band(weight),
                shape.candidate_shipping_band(weight),
            )

    def test_parameter_object_builds_same_url(self) -> None:
        settings = shape.ConnectionSettings(
            host="db",
            port=5432,
            user="app",
            database="main",
            use_tls=True,
            timeout_ms=5000,
            application_name="api",
        )
        self.assertEqual(
            shape.baseline_connect_url("db", 5432, "app", "main", True, 5000, "api"),
            shape.candidate_connect_url(settings),
        )

    def test_dispatch_table_matches_chain(self) -> None:
        for op in ("add", "sub", "mul", "min", "max", "div"):
            self.assertEqual(
                outcome(shape.baseline_apply, op, 7, 3),
                outcome(shape.candidate_apply, op, 7, 3),
            )

    def test_explaining_variables(self) -> None:
        for status in (200, 429, 500, 599, 600):
            for attempt in (0, 4, 5):
                for elapsed in (0, 29_999, 30_000):
                    self.assertEqual(
                        shape.baseline_can_retry(status, attempt, elapsed),
                        shape.candidate_can_retry(status, attempt, elapsed),
                    )

    def test_flag_argument_split(self) -> None:
        for cents in (0, 5, 123456, -250):
            self.assertEqual(
                shape.baseline_format_amount(cents, compact=False),
                shape.format_amount(cents),
            )
            self.assertEqual(
                shape.baseline_format_amount(cents, compact=True),
                shape.format_amount_compact(cents),
            )


class NamesTypesTests(unittest.TestCase):
    def test_units_and_ids_keep_values(self) -> None:
        self.assertEqual(
            nt.baseline_deadline(1000, 250),
            nt.candidate_deadline_ms(nt.Milliseconds(1000), nt.Milliseconds(250)),
        )
        self.assertEqual(
            nt.baseline_membership_key(7, 3),
            nt.candidate_membership_key(nt.UserId(7), nt.TenantId(3)),
        )

    def test_state_enum_covers_meaningful_boolean_combinations(self) -> None:
        pairs = [
            (nt.BaselineUpload(), nt.UploadState.PENDING),
            (nt.BaselineUpload(is_started=True), nt.UploadState.RUNNING),
            (nt.BaselineUpload(is_started=True, is_done=True), nt.UploadState.DONE),
            (nt.BaselineUpload(is_started=True, is_failed=True), nt.UploadState.FAILED),
            (nt.BaselineUpload(is_cancelled=True), nt.UploadState.CANCELLED),
        ]
        for baseline, state in pairs:
            self.assertEqual(
                nt.baseline_describe(baseline),
                nt.candidate_describe(nt.CandidateUpload(state)),
            )

    def test_predicate_name(self) -> None:
        for path in ("a.yml", "b.yaml", "c.json", ""):
            self.assertEqual(nt.baseline_check(path), nt.is_yaml_path(path))


class StateErrorTests(unittest.TestCase):
    def test_explicit_dependencies_are_deterministic(self) -> None:
        due = dt.date(2026, 1, 1)
        self.assertFalse(se.candidate_is_overdue(due, dt.date(2026, 1, 4), 3))
        self.assertTrue(se.candidate_is_overdue(due, dt.date(2026, 1, 5), 3))
        today = dt.date.today()
        self.assertEqual(
            se.baseline_is_overdue(due),
            se.candidate_is_overdue(due, today, se._SETTINGS["grace_days"]),
        )

    def test_pure_core_matches_combined_function(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            for scores in ([], [1, 2, 3], [10]):
                first = os.path.join(tmp, "a.json")
                second = os.path.join(tmp, "b.json")
                se.baseline_summarize_and_save(scores, first)
                se.save_summary(se.summarize(scores), second)
                with (
                    open(first, encoding="utf-8") as a,
                    open(second, encoding="utf-8") as b,
                ):
                    self.assertEqual(json.load(a), json.load(b))

    def test_specific_errors_replace_silent_default(self) -> None:
        def missing(_: str) -> str:
            raise FileNotFoundError

        self.assertEqual(se.baseline_load_port(missing, "c.json"), 8080)
        self.assertEqual(se.candidate_load_port(missing, "c.json"), 8080)
        self.assertEqual(
            se.candidate_load_port(lambda _: '{"port": 9000}', "c.json"), 9000
        )
        # The baseline hides these failures; the candidate reports them.
        for text in ("{not json", '{"prot": 1}', '{"port": "x"}'):
            self.assertEqual(se.baseline_load_port(lambda _, t=text: t, "c"), 8080)
            with self.assertRaises(se.ConfigError):
                se.candidate_load_port(lambda _, t=text: t, "c")


if __name__ == "__main__":
    unittest.main()
