import unittest

from calc import mean


class MeanTest(unittest.TestCase):
    def test_mean(self):
        self.assertEqual(mean([1, 2, 3]), 2)

    def test_empty(self):
        self.assertEqual(mean([]), 0)
