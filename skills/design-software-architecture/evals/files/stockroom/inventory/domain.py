"""Stock rules: reserving units of an item."""

from dataclasses import dataclass

from inventory.adapters.sqlite_store import SqliteStore


@dataclass
class Item:
    sku: str
    on_hand: int


class OutOfStock(Exception):
    pass


def reserve(sku: str, count: int, store: SqliteStore) -> Item:
    if count <= 0:
        raise ValueError("count must be positive")
    sku_, on_hand = store.load(sku)
    item = Item(sku_, on_hand)
    if item.on_hand < count:
        raise OutOfStock(sku)
    item.on_hand -= count
    store.save(item.sku, item.on_hand)
    return item
