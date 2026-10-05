import unittest

from app.place_order import place_order
from domain.orders import Order, PaymentDeclined


class FakeGateway:
    def __init__(self):
        self.charges = []

    def charge(self, order_id, amount_cents):
        self.charges.append((order_id, amount_cents))
        return f"fake-{order_id}"


class PlaceOrderTest(unittest.TestCase):
    def test_charges_the_total(self):
        gateway = FakeGateway()
        self.assertEqual(place_order(Order("o1", 500), gateway), "fake-o1")
        self.assertEqual(gateway.charges, [("o1", 500)])

    def test_empty_order_is_declined(self):
        with self.assertRaises(PaymentDeclined):
            place_order(Order("o2", 0), FakeGateway())
