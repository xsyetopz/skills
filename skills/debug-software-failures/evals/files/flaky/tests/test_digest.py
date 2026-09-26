import unittest
from datetime import datetime, timezone

from alerts.digest import Alert, digest

T = datetime(2026, 9, 1, 14, 5, tzinfo=timezone.utc)


class DigestTest(unittest.TestCase):
    def test_digest_groups_by_category(self):
        alerts = [
            Alert(T, "billing", "latency", "p99 over 2s"),
            Alert(T, "auth", "errors", "5xx rate 3%"),
            Alert(T, "billing", "errors", "5xx rate 1%"),
            Alert(T, "search", "latency", "p99 over 1s"),
            Alert(T, "auth", "saturation", "CPU 95%"),
        ]
        self.assertEqual(
            digest(alerts, now=T),
            "Alert digest 2026-09-01 14:00 UTC: 5 alerts\n"
            "- latency: 2 (billing, search)\n"
            "- errors: 2 (auth, billing)\n"
            "- saturation: 1 (auth)",
        )

    def test_empty(self):
        self.assertEqual(digest([], now=T), "Alert digest 2026-09-01 14:00 UTC: 0 alerts")


if __name__ == "__main__":
    unittest.main()
