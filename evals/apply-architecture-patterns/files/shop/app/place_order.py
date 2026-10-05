from domain.orders import Order, PaymentDeclined
from domain.ports import PaymentGateway


def place_order(order: Order, gateway: PaymentGateway) -> str:
    if order.total_cents <= 0:
        raise PaymentDeclined("empty order")
    return gateway.charge(order.id, order.total_cents)
