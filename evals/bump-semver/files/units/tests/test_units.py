import sys
import unittest
import warnings
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import units


class UnitsTest(unittest.TestCase):
    def test_to_seconds(self):
        self.assertEqual(units.to_seconds(1500), 1.5)

    def test_ms_to_s_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertEqual(units.ms_to_s(1500), 1.5)
        self.assertEqual(caught[0].category, DeprecationWarning)

    def test_secs_warns(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertEqual(units.secs(1500), 1.5)
        self.assertEqual(caught[0].category, DeprecationWarning)

    def test_legacy_timeout_key(self):
        self.assertEqual(units.load_config({"timeout": 5}), {"timeout_s": 5})


if __name__ == "__main__":
    unittest.main()
