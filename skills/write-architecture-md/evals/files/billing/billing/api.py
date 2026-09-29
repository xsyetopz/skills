"""Public operations. Validates input, then calls Ledger; no SQL here."""

from billing.ledger import Ledger

CURRENCIES = {"EUR", "USD"}


def create_invoice(ledger: Ledger, customer: str, cents: int, currency: str) -> int:
    if cents <= 0 or currency not in CURRENCIES:
        raise ValueError("invalid amount or currency")
    return ledger.add_invoice(customer, cents, currency)


def pay(ledger: Ledger, invoice_id: int) -> None:
    if not ledger.mark_paid(invoice_id):
        raise LookupError(f"invoice {invoice_id} is unknown or already paid")
