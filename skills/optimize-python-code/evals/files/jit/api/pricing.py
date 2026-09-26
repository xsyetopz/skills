"""Pure-Python pricing rules; this is where profiles show the CPU time."""

BASE = {"A-100": 12.5, "B-200": 7.25}


def quote(sku: str, qty: int) -> float:
    price = BASE[sku] * qty
    for tier in range(1, qty + 1):
        if tier % 10 == 0:
            price *= 0.99
    return round(price, 2)
