def order_total(items):
    """Total in cents for (price_cents, quantity) pairs."""
    return sum(price * quantity for price, quantity in items)
