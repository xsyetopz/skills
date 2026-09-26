"""Handle Paylane `invoice.due` webhooks by charging the customer."""

from payments import billing


def handle(event: dict) -> dict:
    if event["type"] != "invoice.due":
        return {"status": "ignored"}
    invoice = event["data"]["invoice"]
    charge = billing.charge(invoice["customer"], invoice["amount_cents"])
    return {"status": "charged", "charge_id": charge.id}
