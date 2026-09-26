import unittest

from payments.charges import connect, create_charge


class CreateChargeTest(unittest.TestCase):
    def test_charge_is_stored(self) -> None:
        conn = connect(":memory:")
        charge_id = create_charge(conn, "cus_1", 500)
        self.assertTrue(charge_id.startswith("ch_"))
        rows = conn.execute("SELECT customer_id, amount_cents FROM charges").fetchall()
        self.assertEqual(rows, [("cus_1", 500)])

    def test_non_positive_amount_is_rejected(self) -> None:
        conn = connect(":memory:")
        with self.assertRaises(ValueError):
            create_charge(conn, "cus_1", 0)


if __name__ == "__main__":
    unittest.main()
