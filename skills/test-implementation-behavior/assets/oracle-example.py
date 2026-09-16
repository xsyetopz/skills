"""One oracle applied to a mutant and correction; no third-party packages."""

import unittest


def mutant(text: str) -> list[str]:
    return [part for part in text.split(":") if part]


def corrected(text: str) -> list[str]:
    return text.split(":")


def contract(splitter) -> None:
    expected = {"": [""], "a:": ["a", ""], ":": ["", ""], "a::b": ["a", "", "b"]}
    for text, parts in expected.items():
        if splitter(text) != parts:
            raise AssertionError(f"field preservation failed for {text!r}")


class OracleTests(unittest.TestCase):
    def test_oracle_detects_the_actual_mutant(self):
        with self.assertRaisesRegex(AssertionError, "field preservation"):
            contract(mutant)

    def test_same_oracle_accepts_correction(self):
        contract(corrected)


if __name__ == "__main__":
    unittest.main()
