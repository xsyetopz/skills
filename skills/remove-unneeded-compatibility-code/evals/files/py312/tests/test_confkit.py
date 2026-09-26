import unittest
from pathlib import Path

from confkit import backoff_schedule, gaps, load_config

DATA = Path(__file__).resolve().parent.parent / "data"


class ConfkitTest(unittest.TestCase):
    def test_current(self):
        self.assertEqual(load_config(DATA / "current.toml"), {"timeout": 10, "retries": 3})

    def test_backoff(self):
        self.assertEqual(backoff_schedule(4), (1, 2, 4, 8))
        self.assertEqual(gaps(backoff_schedule(4)), [1, 2, 4])
