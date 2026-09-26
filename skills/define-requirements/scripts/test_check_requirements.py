"""Tests for check_requirements.py (stdlib only; run directly)."""

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

import check_requirements as cr

GOOD = """\
- REQ-A-1 [source: issue 42] When a cancel request is accepted before
  publication starts, the export service shall remove the job's temporary file.
"""


class PatternTests(unittest.TestCase):
    def test_each_ears_pattern(self) -> None:
        cases = {
            "The service shall log each request.": "ubiquitous",
            "When a file arrives, the service shall parse it.": "event-driven",
            "While offline, the client shall queue writes.": "state-driven",
            "If the disk is full, then the service shall reject writes.": "unwanted",
            "Where audit mode is enabled, the service shall sign logs.": "optional",
            "While offline, when a write arrives, the client shall queue it.": "complex",
        }
        for statement, kind in cases.items():
            self.assertEqual(cr.classify(statement), kind, statement)

    def test_non_ears_statement(self) -> None:
        self.assertIsNone(cr.classify("Users can cancel exports."))


class DocumentTests(unittest.TestCase):
    def test_clean_document(self) -> None:
        text = (
            "- REQ-A-1 [source: issue 42] When a cancel request is accepted, "
            "the export service shall remove the temporary file.\n"
            "- AC-A-1 verifies REQ-A-1: Given a running export, when cancel "
            "is accepted, then no temporary file remains.\n"
        )
        report = cr.check(text)
        self.assertEqual(report.defects, [])
        self.assertEqual(report.patterns, {"event-driven": 1})

    def test_defects_are_counted(self) -> None:
        text = (
            "- REQ-B-1 The export shall be fast and user-friendly.\n"
            "- REQ-B-1 [source: x] Exports can be cancelled.\n"
            "- REQ-B-2 [source: x] The service shall retry TBD times.\n"
            "- AC-B-1 verifies REQ-B-9: when x then y\n"
        )
        defects = "\n".join(cr.check(text).defects)
        for expected in (
            "REQ-B-1 has no [source",
            "vague term 'fast'",
            "vague term 'user-friendly'",
            "matches no EARS pattern",
            "duplicate ID",
            "open TBD marker",
            "references unknown REQ-B-9",
            "lacks Given/When/Then",
            "REQ-B-2: no acceptance criterion",
        ):
            self.assertIn(expected, defects)

    def test_wrapped_list_items_are_joined(self) -> None:
        text = GOOD + (
            "- AC-A-1 verifies REQ-A-1: Given a running export, when cancel\n"
            "  is accepted, then no temporary file remains.\n"
        )
        report = cr.check(text)
        self.assertEqual(report.defects, [])

    def test_fenced_examples_are_ignored(self) -> None:
        text = "```text\n- REQ-X-1 bad\n```\n"
        self.assertEqual(cr.check(text).requirements, 0)


class MainTests(unittest.TestCase):
    def test_json_report_and_exit_status(self) -> None:
        text = (
            "- REQ-A-1 [source: issue 42] When a cancel request is accepted, "
            "the export service shall remove the temporary file.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            spec = Path(tmp) / "spec.md"
            spec.write_text(text, encoding="utf-8")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = cr.main([str(spec), "--json"])
        report = json.loads(out.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(report["requirements"], 1)
        self.assertEqual(report["acceptance_criteria"], 0)
        self.assertEqual(report["patterns"], {"event-driven": 1})
        self.assertEqual(
            report["defects"], ["REQ-A-1: no acceptance criterion verifies it"]
        )

    def test_unreadable_file_is_input_error(self) -> None:
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(cr.main(["/nonexistent/spec.md"]), 2)
        self.assertIn("cannot read /nonexistent/spec.md", err.getvalue())


if __name__ == "__main__":
    unittest.main()
