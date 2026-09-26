import unittest
from unittest import mock

from payments import AlreadyPaid, Invoice, PaymentService


class PaymentServiceTest(unittest.TestCase):
    def test_pay(self):
        repo = mock.Mock()
        gateway = mock.Mock()
        repo.find.return_value = Invoice("inv-1", 1250)
        gateway.charge.return_value = "ch_1"
        PaymentService(repo, gateway).pay("inv-1")
        self.assertEqual(
            repo.mock_calls[0], mock.call.find("inv-1")
        )
        repo.find.assert_called_once_with("inv-1")
        gateway.charge.assert_called_once_with(1250, reference="inv-1")
        repo.save.assert_called_once_with(Invoice("inv-1", 1250, True, "ch_1"))
        self.assertEqual(len(repo.mock_calls), 2)

    def test_already_paid(self):
        repo = mock.Mock()
        gateway = mock.Mock()
        repo.find.return_value = Invoice("inv-1", 1250, True, "ch_0")
        with self.assertRaises(AlreadyPaid):
            PaymentService(repo, gateway).pay("inv-1")
        repo.find.assert_called_once_with("inv-1")


if __name__ == "__main__":
    unittest.main()
