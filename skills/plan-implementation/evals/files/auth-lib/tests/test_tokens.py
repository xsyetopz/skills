import unittest

from auth.tokens import check_tok, mk_tok


class TokenTest(unittest.TestCase):
    def test_round_trip(self) -> None:
        self.assertEqual(check_tok(mk_tok("u1", b"k"), b"k"), "u1")


if __name__ == "__main__":
    unittest.main()
