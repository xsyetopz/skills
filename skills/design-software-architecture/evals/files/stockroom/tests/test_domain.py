import unittest

from inventory.adapters.sqlite_store import SqliteStore
from inventory.domain import OutOfStock, reserve


class ReserveTest(unittest.TestCase):
    def setUp(self) -> None:
        self.store = SqliteStore(":memory:")
        self.store.add("A-1", 5)

    def test_reserve_reduces_stock(self) -> None:
        item = reserve("A-1", 2, self.store)
        self.assertEqual(item.on_hand, 3)
        self.assertEqual(reserve("A-1", 3, self.store).on_hand, 0)

    def test_reserve_more_than_on_hand_fails(self) -> None:
        with self.assertRaises(OutOfStock):
            reserve("A-1", 6, self.store)


if __name__ == "__main__":
    unittest.main()
