"""Baseline for the deferred-import card: decimal loads at import time."""

import decimal


def parse_price(text: str) -> decimal.Decimal:
    return decimal.Decimal(text).quantize(decimal.Decimal("0.01"))
