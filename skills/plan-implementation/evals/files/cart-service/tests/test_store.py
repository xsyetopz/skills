import unittest

from cart.store import FakeRedis, read_cart, write_cart


class StoreTest(unittest.TestCase):
    def test_round_trip(self) -> None:
        client = FakeRedis()
        write_cart(client, "u1", ["apple"])
        self.assertEqual(read_cart(client, "u1"), ["apple"])


if __name__ == "__main__":
    unittest.main()
