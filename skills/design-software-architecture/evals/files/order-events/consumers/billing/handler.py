"""Billing team's consumer (copy of their repo; they deploy it themselves)."""

PRICES = {"SKU-1": 250}


def handle(event: dict) -> int:
    """Return the amount in cents to bill for an order line."""
    return PRICES.get(event["sku"], 0) * event["qty"]
