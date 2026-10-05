"""Order pricing rules (see PRICING.md for the contract)."""

from decimal import ROUND_HALF_UP, Decimal


def order_total(subtotal: Decimal, member: bool) -> Decimal:
    """Total after the volume discount and the member discount.

    Volume discount on the subtotal: 5% from 100.00, 10% from 500.00.
    Members get a further 2% off the discounted amount. Totals are rounded
    to cents, halves up.
    """
    if subtotal < 0:
        raise ValueError("subtotal must not be negative")
    if subtotal >= Decimal("500"):
        rate = Decimal("0.10")
    elif subtotal > Decimal("100"):
        rate = Decimal("0.05")
    else:
        rate = Decimal("0")
    total = subtotal * (1 - rate)
    if member:
        total = total * Decimal("0.98")
    return total.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
