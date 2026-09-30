"""Order pricing and notification for a small shop."""


class Customer:
    def __init__(self, name, email, street, city, postcode, tier):
        self.name = name
        self.email = email
        self.street = street
        self.city = city
        self.postcode = postcode
        self.tier = tier


def shipping_cost(kind, weight, street, city, postcode, express, gift, insured):
    if kind == "book":
        cost = 2.0 + weight * 0.5
    elif kind == "electronics":
        cost = 5.0 + weight * 1.5
    elif kind == "grocery":
        cost = 3.0 + weight * 0.8
    else:
        cost = 4.0 + weight
    if express:
        cost = cost * 2
    if gift:
        cost = cost + 1.5
    if insured:
        cost = cost + 3.0
    if postcode.startswith("9"):
        cost = cost + 4.0
    return round(cost, 2)


def tax_rate(kind):
    if kind == "book":
        return 0.05
    elif kind == "electronics":
        return 0.23
    elif kind == "grocery":
        return 0.08
    else:
        return 0.23


def return_window_days(kind):
    if kind == "book":
        return 30
    elif kind == "electronics":
        return 14
    elif kind == "grocery":
        return 0
    else:
        return 30


def discount(customer, subtotal):
    if customer.tier == "gold" and customer.city == "Warsaw":
        return subtotal * 0.15
    if customer.tier == "gold":
        return subtotal * 0.10
    if customer.tier == "silver":
        return subtotal * 0.05
    return 0.0


def order_confirmation(customer, items):
    lines = [f"Hello {customer.name},"]
    total = 0.0
    for item in items:
        price = item["price"] * (1 + tax_rate(item["kind"]))
        total += price
        lines.append(f"{item['name']}: {price:.2f}")
    lines.append(f"Total: {total:.2f}")
    lines.append(f"Ship to: {customer.street}, {customer.postcode} {customer.city}")
    return "\n".join(lines)


def refund_confirmation(customer, items):
    lines = [f"Hello {customer.name},"]
    total = 0.0
    for item in items:
        price = item["price"] * (1 + tax_rate(item["kind"]))
        total += price
        lines.append(f"{item['name']}: {price:.2f}")
    lines.append(f"Refunded: {total:.2f}")
    lines.append(f"Return to: {customer.street}, {customer.postcode} {customer.city}")
    return "\n".join(lines)
