"""Public order events published to the `orders` topic."""


def order_line_added(order_id: str, sku: str, qty: int) -> dict:
    return {
        "type": "order.line_added",
        "version": 1,
        "order_id": order_id,
        "sku": sku,
        "qty": qty,
    }
