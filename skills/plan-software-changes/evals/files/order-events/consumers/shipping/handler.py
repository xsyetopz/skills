"""Shipping team's consumer (copy of their repo; they deploy it themselves)."""


def handle(event: dict) -> str:
    """Return the pick-list line for an order line."""
    return f"{event['qty']} x {event['sku']}"
