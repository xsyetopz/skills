import json

from domain.pricing import order_total


def checkout(request_body: str) -> tuple[int, str]:
    data = json.loads(request_body)
    items = [(item["price_cents"], item["qty"]) for item in data["items"]]
    return 200, json.dumps({"total_cents": order_total(items)})
