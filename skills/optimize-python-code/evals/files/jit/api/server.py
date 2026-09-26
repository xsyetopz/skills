"""Pricing API entry point (simplified)."""

from api.pricing import quote


def handle(request: dict) -> dict:
    return {"price": quote(request["sku"], request["qty"])}


if __name__ == "__main__":
    print(handle({"sku": "A-100", "qty": 3}))
