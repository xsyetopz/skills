"""Independent expected values, partitions, tables, transitions, vectors."""

import unittest

from harness import impl


class InvoiceTests(unittest.TestCase):
    def test_total_matches_reviewed_value(self):
        # Reviewed requirement: 2 x 199 cents less a 49-cent discount.
        self.assertEqual(impl.invoice_total(199, 2, 49), 349)


class PercentageTests(unittest.TestCase):
    def test_boundaries_and_neighbors(self):
        expected = {0: False, 1: True, 2: True, 99: True, 100: True, 101: False}
        for value, accepted in expected.items():
            with self.subTest(value=value):
                self.assertIs(impl.accept_percentage(value), accepted)

    def test_class_representatives(self):
        for value, accepted in {-40: False, 50: True, 1000: False}.items():
            with self.subTest(value=value):
                self.assertIs(impl.accept_percentage(value), accepted)


TABLE = {
    ("admin", "active"): True,
    ("admin", "suspended"): True,
    ("editor", "active"): True,
    ("editor", "suspended"): False,
    ("viewer", "active"): False,
    ("viewer", "suspended"): False,
}


class PermissionTableTests(unittest.TestCase):
    def test_every_role_and_account_combination(self):
        for (role, account), allowed in TABLE.items():
            with self.subTest(role=role, account=account):
                self.assertIs(impl.can_edit(role, account), allowed)


STATES = ["draft", "review", "published", "archived"]
EVENTS = ["submit", "approve", "reject", "archive"]
ALLOWED = {
    ("draft", "submit"): "review",
    ("review", "approve"): "published",
    ("review", "reject"): "draft",
    ("published", "archive"): "archived",
}


class TransitionTests(unittest.TestCase):
    def test_allowed_transitions(self):
        for (state, event), target in ALLOWED.items():
            with self.subTest(state=state, event=event):
                self.assertEqual(impl.next_state(state, event), target)

    def test_every_other_pair_is_rejected(self):
        for state in STATES:
            for event in EVENTS:
                if (state, event) in ALLOWED:
                    continue
                with (
                    self.subTest(state=state, event=event),
                    self.assertRaises(ValueError),
                ):
                    impl.next_state(state, event)


# RFC 4648 section 10, plus 0xfbff which uses alphabet values 62 ('+')
# and 63 ('/') from Table 1.
VECTORS = {
    b"": "",
    b"f": "Zg==",
    b"fo": "Zm8=",
    b"foo": "Zm9v",
    b"foob": "Zm9vYg==",
    b"fooba": "Zm9vYmE=",
    b"foobar": "Zm9vYmFy",
    b"\xfb\xff": "+/8=",
}


class Base64Tests(unittest.TestCase):
    def test_standard_vectors(self):
        for raw, encoded in VECTORS.items():
            with self.subTest(raw=raw):
                self.assertEqual(impl.b64encode(raw), encoded)
                self.assertEqual(impl.b64decode(encoded), raw)


GOLDEN = """\
generated: <TIME>
name,count
alpha,3
beta,1
"""


class ReportSnapshotTests(unittest.TestCase):
    def test_report_matches_reviewed_golden_text(self):
        text = impl.render_report([("beta", 1), ("alpha", 3)], "2026-09-25T10:00Z")
        normalized = text.replace("2026-09-25T10:00Z", "<TIME>", 1)
        self.assertEqual(normalized, GOLDEN)


if __name__ == "__main__":
    unittest.main()
