from shipping import fee, label


def summary(order):
    cost = fee(order["weight_g"], True) if order["priority"] else fee(order["weight_g"], False)
    return f"{label(order['status'])}: {cost} cents"
