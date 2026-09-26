"""Charge an invoice once and record the payment."""

from dataclasses import dataclass, replace


class AlreadyPaid(Exception):
    pass


@dataclass(frozen=True)
class Invoice:
    id: str
    amount_cents: int
    paid: bool = False
    charge_id: str | None = None


class PaymentService:
    def __init__(self, repo, gateway) -> None:
        self._repo = repo
        self._gateway = gateway

    def pay(self, invoice_id: str) -> Invoice:
        """Charge the invoice's amount through the gateway and store it as paid.

        Raises AlreadyPaid (and charges nothing) when the invoice is already paid.
        """
        invoice = self._repo.find(invoice_id)
        if invoice.paid:
            raise AlreadyPaid(invoice_id)
        charge_id = self._gateway.charge(invoice.amount_cents, reference=invoice.id)
        paid = replace(invoice, paid=True, charge_id=charge_id)
        self._repo.save(paid)
        return paid
