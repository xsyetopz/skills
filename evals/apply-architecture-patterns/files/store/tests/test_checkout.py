import json
import unittest

from web.handlers import checkout


class CheckoutTest(unittest.TestCase):
    def test_total(self):
        body = json.dumps({"items": [{"price_cents": 2500, "qty": 2}, {"price_cents": 1200, "qty": 1}]})
        self.assertEqual(checkout(body), (200, json.dumps({"total_cents": 6200})))
