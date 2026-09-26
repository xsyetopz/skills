"""One behavior per test, a visible action, and kept history."""

import unittest

from harness import impl


class ShippingTests(unittest.TestCase):
    def test_zero_weight_has_no_shipping_charge(self):
        self.assertEqual(impl.shipping(0), 0)

    def test_positive_weight_has_flat_charge(self):
        self.assertEqual(impl.shipping(2.5), 5)

    def test_negative_weight_is_rejected(self):
        with self.assertRaises(ValueError):
            impl.shipping(-1)


class CartTests(unittest.TestCase):
    def test_adding_a_book_updates_total(self):
        cart = impl.Cart()

        cart.add("book")

        self.assertEqual(cart.total, 20)

    def test_removing_a_book_clears_total(self):
        cart = impl.Cart()
        cart.add("book")

        cart.remove("book")

        self.assertEqual(cart.total, 0)


class ConnectionTests(unittest.TestCase):
    def test_closed_connection_can_reopen(self):
        connection = impl.Connection()
        connection.open()
        connection.close()
        self.assertFalse(connection.is_open)

        connection.open()

        self.assertTrue(connection.is_open)


if __name__ == "__main__":
    unittest.main()
