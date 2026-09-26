import unittest

from strings import greeting, price


class StringsTest(unittest.TestCase):
    def test_greeting(self):
        self.assertEqual(greeting("Ada", 3), "Hello Ada, you have 3 new messages")

    def test_price(self):
        self.assertEqual(price(2.5), "2.50 EUR")


if __name__ == "__main__":
    unittest.main()
