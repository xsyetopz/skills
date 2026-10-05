import re
import unittest

from stamp import age_days, stamp


class StampTest(unittest.TestCase):
    def test_format(self):
        self.assertRegex(stamp(), re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$"))

    def test_fresh_stamp_is_zero_days_old(self):
        self.assertEqual(age_days(stamp()), 0)

    def test_old_stamp(self):
        self.assertGreater(age_days("2020-01-01T00:00:00Z"), 365)
