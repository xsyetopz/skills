def calc(prices: list[int], tax_rate: float) -> int:
    subtotal = sum(prices)
    return round(subtotal * (1 + tax_rate))
