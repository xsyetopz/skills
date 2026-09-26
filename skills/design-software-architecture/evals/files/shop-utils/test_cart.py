import unittest

from cart import checkout_total


class CheckoutTotalTest(unittest.TestCase):
    def test_total_includes_tax(self) -> None:
        self.assertEqual(checkout_total({"a": 100, "b": 50}), 180)


if __name__ == "__main__":
    unittest.main()
