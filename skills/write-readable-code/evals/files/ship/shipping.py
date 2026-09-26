def ship(order):
    if order.get("paid"):
        if order.get("items"):
            if order.get("address"):
                if not order.get("hold"):
                    if order.get("weight", 0) <= 30:
                        return "shipped"
                    else:
                        if order.get("freight_ok"):
                            return "freight"
                        else:
                            return "too heavy"
                else:
                    return "on hold"
            else:
                return "no address"
        else:
            return "empty"
    else:
        return "unpaid"
