import unittest

from inventory import format_report, parse_rows, problems

CSV = [
    "sku,name,quantity,reorder_at\n",
    "A1,Bolt,3,5\n",
    "B2,Nut,40,10\n",
    "A1,Bolt copy,-1,5\n",
]


class InventoryTests(unittest.TestCase):
    def test_report_lists_low_stock_and_problems(self):
        items = parse_rows(CSV)
        report = format_report(items, problems(items))
        self.assertEqual(
            report,
            "3 items\n"
            "reorder A1 Bolt copy: -1 left\n"
            "reorder A1 Bolt: 3 left\n"
            "problem A1: duplicate SKU\n"
            "problem A1: negative quantity -1",
        )


if __name__ == "__main__":
    unittest.main()
