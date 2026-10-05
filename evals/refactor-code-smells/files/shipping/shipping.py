def label(status):
    if status == "pending":
        return "Waiting for payment"
    elif status == "paid":
        return "Paid"
    elif status == "shipped":
        return "On the way"
    elif status == "delivered":
        return "Delivered"
    elif status == "returned":
        return "Returned"
    else:
        raise ValueError(f"unknown status: {status}")


def fee(weight_g, express):
    if express:
        base = 900
        per_kg = 250
    else:
        base = 400
        per_kg = 100
    return base + per_kg * -(-weight_g // 1000)
