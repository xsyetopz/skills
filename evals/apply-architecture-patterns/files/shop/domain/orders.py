from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    id: str
    total_cents: int


class PaymentDeclined(Exception):
    pass
