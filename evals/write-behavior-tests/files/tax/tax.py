from decimal import ROUND_HALF_UP, Decimal


def calculate_tax(amount, rate, inclusive=False):
    if inclusive:
        net = amount / (1 + rate)
        return (amount - net).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
