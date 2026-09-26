import sys
import unittest
from pathlib import Path

# Runnable from the project root (python -m unittest) or directly as a file.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from counter import count_delimiters, count_delimiters_split

CASES = [
    ("", ","),
    ("a,b,c", ","),
    (",a,,b,", ","),
    ("no match", ";"),
    ("aaa", "aa"),
    ("żółw,kot", ","),
    ("a--b--", "--"),
]


class CountDelimitersTests(unittest.TestCase):
    def test_matches_split_oracle(self) -> None:
        for text, delimiter in CASES:
            with self.subTest(text=text, delimiter=delimiter):
                self.assertEqual(
                    count_delimiters(text, delimiter),
                    count_delimiters_split(text, delimiter),
                )

    def test_empty_delimiter_raises_like_split(self) -> None:
        with self.assertRaises(ValueError):
            count_delimiters_split("abc", "")
        with self.assertRaises(ValueError):
            count_delimiters("abc", "")


if __name__ == "__main__":
    unittest.main()
