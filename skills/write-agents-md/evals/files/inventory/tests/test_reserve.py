import unittest

from inventory import reserve


class ReserveTest(unittest.TestCase):
    def test_reserves(self):
        stock = {"a": 3}
        self.assertTrue(reserve(stock, "a", 2))
        self.assertEqual(stock, {"a": 1})

    def test_insufficient(self):
        self.assertFalse(reserve({"a": 1}, "a", 2))
