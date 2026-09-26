"""Public consequences, values, outcomes, required effects, real engines."""

import sqlite3
import unittest
from unittest.mock import Mock

from harness import impl


class RenderNameTests(unittest.TestCase):
    def test_surrounding_whitespace_is_removed(self):
        self.assertEqual(impl.render_name("  Ada \n"), "Ada")


class BasketTests(unittest.TestCase):
    def test_count_reports_each_addition(self):
        basket = impl.Basket()
        basket.add("book")
        basket.add("book")

        self.assertEqual(basket.count("book"), 2)


class PriceTests(unittest.TestCase):
    def test_listed_price_is_returned(self):
        self.assertEqual(impl.price_for("book", {"book": 20}), 20)

    def test_unlisted_item_raises_key_error(self):
        with self.assertRaises(KeyError):
            impl.price_for("pen", {"book": 20})


class NotifyTests(unittest.TestCase):
    def test_allowed_address_gets_exactly_one_ready_message(self):
        send = Mock()

        accepted = impl.notify("a@example.invalid", True, send)

        self.assertIs(accepted, True)
        send.assert_called_once_with("a@example.invalid", "ready")

    def test_denied_address_gets_no_message(self):
        send = Mock()

        accepted = impl.notify("a@example.invalid", False, send)

        self.assertIs(accepted, False)
        send.assert_not_called()


class UsersTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)

    def test_email_differing_only_in_case_is_rejected(self):
        users = impl.Users(self.db)
        users.add("Ada@example.invalid")

        with self.assertRaises(sqlite3.IntegrityError):
            users.add("ada@example.invalid")


if __name__ == "__main__":
    unittest.main()
