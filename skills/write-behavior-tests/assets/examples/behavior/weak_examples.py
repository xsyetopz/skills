"""Deliberately weak tests. Each passes on the reference implementation and
also passes on (or wrongly fails) a variant named in expectations.json.

Not collected by `unittest discover` (the file name does not start with
test_); run_matrix.py runs it explicitly.
"""

import sqlite3
import unittest
from inspect import getsource
from unittest.mock import MagicMock, Mock, call

import subjects
from harness import impl


class WeakConnection(unittest.TestCase):
    """Split away the history: misses bug_connection_no_reopen."""

    def test_open(self):
        connection = impl.Connection()
        connection.open()
        self.assertTrue(connection.is_open)

    def test_close(self):
        connection = impl.Connection()
        connection.open()
        connection.close()
        self.assertFalse(connection.is_open)


class WeakPercentage(unittest.TestCase):
    """Class middles only: misses bug_percentage_off_by_one."""

    def test_middles(self):
        self.assertTrue(impl.accept_percentage(50))
        self.assertFalse(impl.accept_percentage(150))


class WeakPermissions(unittest.TestCase):
    """Each flag alone: misses bug_can_edit_suspended."""

    def test_editor_can_edit_active(self):
        self.assertTrue(impl.can_edit("editor", "active"))

    def test_admin_can_edit_suspended(self):
        self.assertTrue(impl.can_edit("admin", "suspended"))

    def test_viewer_cannot_edit(self):
        self.assertFalse(impl.can_edit("viewer", "active"))


class WeakTransitions(unittest.TestCase):
    """Every state visited, no forbidden pair: misses bug_state_skip_review."""

    def test_happy_path_visits_every_state(self):
        state = "draft"
        for event in ("submit", "approve", "archive"):
            state = impl.next_state(state, event)
        self.assertEqual(state, "archived")


class WeakBase64(unittest.TestCase):
    """Round trip only: misses bug_b64_urlsafe (encoder and decoder agree)."""

    def test_round_trip(self):
        for raw in (b"", b"foobar", b"\xfb\xff", bytes(range(256))):
            self.assertEqual(impl.b64decode(impl.b64encode(raw)), raw)


class WeakSnapshot(unittest.TestCase):
    """Normalizes away order: misses bug_report_unsorted."""

    def test_same_lines_in_any_order(self):
        text = impl.render_report([("beta", 1), ("alpha", 3)], "T")
        self.assertEqual(
            sorted(text.splitlines()[1:]), ["alpha,3", "beta,1", "name,count"]
        )


class WeakRenderName(unittest.TestCase):
    """Tests the helper and the source: misses bug_render_ignores_trim and
    fails alt_render_inline."""

    def test_uses_trim_helper(self):
        self.assertIn("_trim", getsource(impl.render_name))
        self.assertEqual(subjects._trim(" Ada "), "Ada")


class WeakBasket(unittest.TestCase):
    """Pins private storage: misses bug_basket_counts_once and fails
    alt_counting_basket."""

    def test_items_list(self):
        basket = impl.Basket()
        basket.add("book")
        basket.add("book")
        self.assertEqual(basket._items, ["book", "book"])


class WeakPrice(unittest.TestCase):
    """Pins call choreography: misses bug_price_zero, fails alt_price_direct."""

    def test_lookup_calls(self):
        catalog = MagicMock()
        catalog.__contains__.return_value = True
        catalog.__getitem__.return_value = 20
        impl.price_for("book", catalog)
        self.assertEqual(
            catalog.mock_calls,
            [call.__contains__("book"), call.__getitem__("book")],  # pyright: ignore[reportCallIssue, reportArgumentType]
        )


class WeakNotify(unittest.TestCase):
    """Return value only: misses both notify bugs."""

    def test_acceptance(self):
        for allowed in (True, False):
            self.assertIs(impl.notify("a@example.invalid", allowed, Mock()), allowed)


class WeakUsers(unittest.TestCase):
    """Checks the id only: misses bug_users_case_sensitive."""

    def test_add_returns_id(self):
        users = impl.Users(sqlite3.connect(":memory:"))
        self.assertEqual(users.add("Ada@example.invalid"), 1)
        self.assertEqual(users.add("grace@example.invalid"), 2)


class WeakSplit(unittest.TestCase):
    """No empty fields in the input: misses bug_split_drops_empty."""

    def test_two_fields(self):
        self.assertEqual(impl.split_fields("a:b"), ["a", "b"])


class WeakWriteConfig(unittest.TestCase):
    """Checks the exception only: misses bug_config_truncates."""

    def test_invalid_text_raises(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.conf"
            path.write_text("port=80\n")
            with self.assertRaises(ValueError):
                impl.write_config(path, "not a config")


class WeakAccount(unittest.TestCase):
    """Sequential calls: misses bug_account_no_lock."""

    def test_two_deposits(self):
        account = impl.Account()
        account.deposit(10)
        account.deposit(10)
        self.assertEqual(account.balance, 20)


class WeakRegistry(unittest.TestCase):
    """Shared state, no reset: the second test fails only after the first."""

    def test_a_first_registration(self):
        self.assertEqual(impl.register("bob"), 1)

    def test_b_first_registration_again(self):
        self.assertEqual(impl.register("bob"), 1)


class WeakFeeMirror(unittest.TestCase):
    """Mirrors private storage: fails alt_fees_tuple although the fee is
    right."""

    def test_fee_storage_and_value(self):
        self.assertEqual(subjects.DELIVERY_FEES, [5])
        self.assertEqual(impl.delivery_fee(10), 5)


if __name__ == "__main__":
    unittest.main()
