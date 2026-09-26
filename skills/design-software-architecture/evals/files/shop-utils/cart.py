from utils import calc


def checkout_total(cart: dict[str, int]) -> int:
    return calc(list(cart.values()), 0.2)
