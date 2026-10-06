from store import CustomerStore


def invoice_total(store: CustomerStore, customer_id: str, net_cents: int) -> int:
    customer = store.find(customer_id)
    if customer is None:
        raise KeyError(f"unknown customer: {customer_id}")
    rate = 0 if customer.get("tax_exempt") else 20
    return net_cents + net_cents * rate // 100
