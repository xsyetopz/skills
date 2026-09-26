"""Candidate for the deferred-import card: decimal loads on first call."""

from __future__ import annotations

TYPE_CHECKING = False  # avoids importing typing just for the guard
if TYPE_CHECKING:
    import decimal


def parse_price(text: str) -> decimal.Decimal:
    import decimal  # PERF: deferred; first call pays the import once.

    return decimal.Decimal(text).quantize(decimal.Decimal("0.01"))
