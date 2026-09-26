"""Regression reproducers, persisted effects, races, time, and isolation."""

import contextlib
import tempfile
import threading
import unittest
from pathlib import Path

from harness import impl


class SplitRegressionTests(unittest.TestCase):
    def test_empty_fields_are_kept(self):
        # Reproducer from the incident: 'a::b' lost its middle field.
        cases = {"a::b": ["a", "", "b"], "a:": ["a", ""], ":": ["", ""], "": [""]}
        for line, fields in cases.items():
            with self.subTest(line=line):
                self.assertEqual(impl.split_fields(line), fields)


class WriteConfigTests(unittest.TestCase):
    def test_invalid_text_leaves_existing_file_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.conf"
            path.write_text("port=80\n", encoding="utf-8")

            with self.assertRaises(ValueError):
                impl.write_config(path, "not a config")

            self.assertEqual(path.read_text(encoding="utf-8"), "port=80\n")
            self.assertEqual(
                sorted(p.name for p in Path(directory).iterdir()), ["app.conf"]
            )

    def test_valid_text_replaces_file_without_leftovers(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "app.conf"
            path.write_text("port=80\n", encoding="utf-8")

            impl.write_config(path, "port=81\n")

            self.assertEqual(path.read_text(encoding="utf-8"), "port=81\n")
            self.assertEqual([p.name for p in Path(directory).iterdir()], ["app.conf"])


class AccountRaceTests(unittest.TestCase):
    def test_concurrent_deposits_are_not_lost(self):
        account = impl.Account()
        barrier = threading.Barrier(2)

        def both_read_before_either_writes():
            # With the lock held, the second thread cannot arrive: the wait
            # times out and the barrier breaks, which is the expected path.
            with contextlib.suppress(threading.BrokenBarrierError):
                barrier.wait(timeout=0.5)

        account.before_write = both_read_before_either_writes
        threads = [
            threading.Thread(target=account.deposit, args=(10,)) for _ in range(2)
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive(), "deposit thread hung")

        self.assertEqual(account.balance, 20)


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


class SessionTests(unittest.TestCase):
    def test_session_expires_exactly_at_ttl(self):
        clock = FakeClock()
        session = impl.Session(ttl=30, clock=clock)

        clock.now += 29.999
        self.assertFalse(session.expired)
        clock.now += 0.001
        self.assertTrue(session.expired)


class RegistryTests(unittest.TestCase):
    def setUp(self):
        impl.reset_registry()

    def test_first_registration_counts_one(self):
        self.assertEqual(impl.register("alice"), 1)

    def test_second_registration_counts_two(self):
        impl.register("alice")
        self.assertEqual(impl.register("alice"), 2)


class DeliveryFeeTests(unittest.TestCase):
    def test_flat_fee_for_any_distance(self):
        for distance in (0, 10, 500):
            with self.subTest(distance=distance):
                self.assertEqual(impl.delivery_fee(distance), 5)


if __name__ == "__main__":
    unittest.main()
