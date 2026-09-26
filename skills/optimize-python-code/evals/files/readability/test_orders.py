import unittest

from orders import summarize


class SummarizeTest(unittest.TestCase):
    def test_totals_refunds_and_discounts(self):
        orders = [
            {"id": 1, "status": "paid", "customer": " Ann ", "ts": 5,
             "items": [{"qty": 2, "price_cents": 1000, "discount_pct": 10}]},
            {"id": 2, "status": "refunded", "customer": "ann", "ts": 9,
             "items": [{"price_cents": 500}]},
            {"id": 3, "status": "pending", "customer": "bob", "items": []},
            {"id": 4, "status": "shipped", "ts": 2, "items": [{"qty": 1, "price_cents": 250}]},
        ]
        self.assertEqual(
            summarize(orders),
            [("ann", 1, 1300, 1, 3, 9), ("unknown", 1, 250, 0, 1, 2)],
        )

    def test_negative_quantity(self):
        with self.assertRaises(ValueError):
            summarize([{"id": 7, "status": "paid", "customer": "c",
                        "items": [{"qty": -1, "price_cents": 1}]}])

    def test_empty(self):
        self.assertEqual(summarize([]), [])


if __name__ == "__main__":
    unittest.main()
