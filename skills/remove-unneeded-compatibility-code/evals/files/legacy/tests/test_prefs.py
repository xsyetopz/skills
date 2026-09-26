import tempfile
import unittest
from pathlib import Path

from prefs import DEFAULTS, load, save


class PrefsTest(unittest.TestCase):
    def test_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.json"
            save(path, {**DEFAULTS, "theme": "dark"})
            self.assertEqual(load(path)["theme"], "dark")
