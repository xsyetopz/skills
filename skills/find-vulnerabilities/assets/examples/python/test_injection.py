"""Exploit-condition and fix tests for injection.py (stdlib only).

Run: python3 test_injection.py
Every payload targets a local in-memory database, a temp directory, or a
string; nothing leaves the machine.
"""

from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import injection as inj


class Tags(HTMLParser):
    """Collects (tag, attributes) pairs the way a browser tokenizer would."""

    def __init__(self) -> None:
        super().__init__()
        self.found: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        self.found.append((tag, dict(attrs)))


def tags(markup: str) -> list[tuple[str, dict[str, str | None]]]:
    parser = Tags()
    parser.feed(markup)
    return parser.found


class SqlInjection(unittest.TestCase):
    def setUp(self) -> None:
        self.db = inj.make_db()
        self.addCleanup(self.db.close)

    def test_tautology_leaks_every_row(self) -> None:
        rows = inj.vulnerable_find_user(self.db, "x' OR '1'='1")
        self.assertEqual(len(rows), 3)

    def test_parameter_keeps_payload_as_data(self) -> None:
        self.assertEqual(inj.fixed_find_user(self.db, "x' OR '1'='1"), [])
        self.assertEqual(
            inj.fixed_find_user(self.db, "bob"), [("bob", "bob@example.test")]
        )

    def test_quote_in_legitimate_name_breaks_only_vulnerable(self) -> None:
        with self.assertRaises(sqlite3.OperationalError):
            inj.vulnerable_find_user(self.db, "o'brien")
        self.assertEqual(inj.fixed_find_user(self.db, "o'brien"), [])

    def test_identifier_injection_runs_attacker_expression(self) -> None:
        # A subquery in ORDER BY proves attacker-controlled SQL executes.
        payload = "(SELECT CASE WHEN 1 THEN name END)"
        self.assertEqual(len(inj.vulnerable_list_users(self.db, payload)), 3)
        with self.assertRaises(ValueError):
            inj.fixed_list_users(self.db, payload)

    def test_identifier_mapping_keeps_legitimate_sorts(self) -> None:
        names = [r[0] for r in inj.fixed_list_users(self.db, "name", True)]
        self.assertEqual(names, ["carol", "bob", "alice"])


class CommandInjection(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.data = self.root / "data.txt"
        self.data.write_text("a\nb\n")
        self.marker = self.root / "MARKER"

    def test_metacharacter_runs_second_command(self) -> None:
        inj.vulnerable_count_lines(f"{self.data}; touch {self.marker}")
        self.assertTrue(self.marker.exists())

    def test_argv_passes_one_literal_argument(self) -> None:
        inj.fixed_count_lines(f"{self.data}; touch {self.marker}")
        self.assertFalse(self.marker.exists())
        self.assertIn("2", inj.fixed_count_lines(str(self.data)))


class ArgumentInjection(unittest.TestCase):
    def test_leading_dash_becomes_option(self) -> None:
        self.assertIn("RAN", inj.vulnerable_lookup("--exec=payload"))

    def test_double_dash_ends_option_parsing(self) -> None:
        out = inj.fixed_lookup("--exec=payload")
        self.assertIn("NAMES --exec=payload", out)


class CrossSiteScripting(unittest.TestCase):
    def test_text_context(self) -> None:
        payload = "<script>alert(1)</script>"
        self.assertIn("script", [t for t, _ in tags(inj.vulnerable_greeting(payload))])
        self.assertNotIn("script", [t for t, _ in tags(inj.fixed_greeting(payload))])

    def test_attribute_context(self) -> None:
        payload = '" autofocus onfocus="alert(1)'
        _, attrs = tags(inj.vulnerable_input_value(payload))[0]
        self.assertIn("onfocus", attrs)
        _, attrs = tags(inj.fixed_input_value(payload))[0]
        self.assertEqual(set(attrs), {"name", "value"})
        self.assertEqual(attrs["value"], payload)

    def test_url_context(self) -> None:
        payload = " JavaScript:alert(1)"
        _, attrs = tags(inj.vulnerable_profile_link(payload))[0]
        self.assertTrue((attrs["href"] or "").strip().lower().startswith("javascript:"))
        self.assertEqual(tags(inj.fixed_profile_link(payload))[0][0], "span")
        ok = tags(inj.fixed_profile_link("https://example.test/u?a=1&b=2"))
        self.assertEqual(ok[0][1]["href"], "https://example.test/u?a=1&b=2")


if __name__ == "__main__":
    unittest.main()
