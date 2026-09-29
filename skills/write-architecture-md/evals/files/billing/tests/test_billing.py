import unittest

from billing import api
from billing.ledger import Ledger


class BillingTests(unittest.TestCase):
    def test_create_and_pay_once(self) -> None:
        ledger = Ledger(":memory:")
        invoice = api.create_invoice(ledger, "acme", 1200, "EUR")
        api.pay(ledger, invoice)
        with self.assertRaises(LookupError):
            api.pay(ledger, invoice)

    def test_rejects_unknown_currency(self) -> None:
        with self.assertRaises(ValueError):
            api.create_invoice(Ledger(":memory:"), "acme", 1200, "GBP")


if __name__ == "__main__":
    unittest.main()
