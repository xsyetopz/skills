"""Acceptance tests: one test per AC in export-cancellation-spec.md.

Run: python3 test_export_cancel.py
"""

from __future__ import annotations

import os
import sys
import tempfile
import threading
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from export_cancel import ExportJob

NEW = b"EXPORT\nnew\n"
OLD = b"previous export\n"


class AcceptanceTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.destination = Path(directory.name) / "report.csv"
        self.destination.write_bytes(OLD)

    def test_ac_exp_001_cancel_before_publication(self) -> None:
        at_barrier = threading.Event()
        release = threading.Event()

        def hold() -> None:
            at_barrier.set()
            release.wait(5)

        job = ExportJob(self.destination, NEW, before_publish=hold)
        writer = threading.Thread(target=job.run)
        writer.start()
        self.assertTrue(at_barrier.wait(5))
        self.assertEqual(job.cancel(), "cancelled")
        release.set()
        writer.join(5)
        self.assertEqual(job.state, "cancelled")
        self.assertFalse(job.temporary.exists())
        self.assertEqual(self.destination.read_bytes(), OLD)

    def test_ac_exp_002_cancel_after_publication_started(self) -> None:
        responses: list[str] = []
        job = ExportJob(self.destination, NEW)

        original_replace = os.replace

        def replace_and_cancel(src: str, dst: str) -> None:
            responses.append(job.cancel())  # publication has started
            original_replace(src, dst)

        os.replace = replace_and_cancel  # type: ignore[assignment]
        try:
            job.run()
        finally:
            os.replace = original_replace  # type: ignore[assignment]
        self.assertEqual(responses, ["publication started"])
        self.assertEqual(job.state, "published")
        self.assertEqual(self.destination.read_bytes(), NEW)

    def test_ac_exp_003_repeated_cancel_is_a_no_op(self) -> None:
        cancelled = ExportJob(self.destination, NEW)
        cancelled.cancel()
        published = ExportJob(self.destination, NEW)
        published.run()
        snapshot = self.destination.read_bytes()
        self.assertEqual(cancelled.cancel(), "cancelled")
        self.assertEqual(published.cancel(), "published")
        self.assertEqual(self.destination.read_bytes(), snapshot)

    def test_ac_exp_004_validation_failure(self) -> None:
        job = ExportJob(self.destination, b"not an export\n")
        job.run()
        self.assertEqual(job.state, "failed")
        self.assertIn("rule V1", job.error or "")
        self.assertFalse(job.temporary.exists())
        self.assertEqual(self.destination.read_bytes(), OLD)


if __name__ == "__main__":
    unittest.main()
