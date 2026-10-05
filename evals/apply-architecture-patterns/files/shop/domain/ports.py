from typing import Protocol


class PaymentGateway(Protocol):
    def charge(self, order_id: str, amount_cents: int) -> str:
        """Charge the order and return the provider's charge id."""
        ...
