"""Import customer events (JSON lines) and print net revenue per customer."""

import json
import sys


def net_revenue(lines):
    last_order = {}
    totals = {}
    for line in lines:
        event = json.loads(line)
        customer = event["customer_id"]
        if event["kind"] == "order":
            last_order[customer] = event
            totals[customer] = totals.get(customer, 0) + event["price"]
        elif event["kind"] == "subscription":
            last_order[customer] = event
            totals[customer] = totals.get(customer, 0) + event["monthly"]
        elif event["kind"] == "refund":
            original = last_order[customer]
            totals[customer] = totals.get(customer, 0) - original["price"]
    return totals


def main(path):
    with open(path, encoding="utf-8") as handle:
        totals = net_revenue(handle)
    for customer, total in sorted(totals.items()):
        print(f"{customer}\t{total}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
