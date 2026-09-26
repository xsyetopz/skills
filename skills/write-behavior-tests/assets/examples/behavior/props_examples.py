# pyright: reportMissingImports=false
# (hypothesis is supplied at run time by `uv run --with`, see below)
"""Property-based and stateful tests with Hypothesis (a third-party package).

Run with a pinned Hypothesis, outside the repository's environment:
  uv run --no-project --with hypothesis==6.168.1 python -m unittest props_examples
VARIANT selects the implementation exactly as for the other test files.
"""

import unittest
from collections import Counter

from harness import impl
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, precondition, rule


class SplitProperties(unittest.TestCase):
    @given(st.text(alphabet="ab:", max_size=12))
    def test_join_inverts_split(self, line):
        self.assertEqual(":".join(impl.split_fields(line)), line)

    @given(st.lists(st.text(alphabet="xy", max_size=3), min_size=1, max_size=5))
    def test_field_count_is_separators_plus_one(self, fields):
        line = ":".join(fields)
        self.assertEqual(len(impl.split_fields(line)), line.count(":") + 1)


class CartMachine(RuleBasedStateMachine):
    """Compare Cart with a Counter model after every step."""

    def __init__(self) -> None:
        super().__init__()
        self.cart = impl.Cart()
        self.model: Counter[str] = Counter()

    @rule(item=st.sampled_from(["book", "pen"]))
    def add(self, item):
        self.cart.add(item)
        self.model[item] += 1

    @precondition(lambda self: sum(self.model.values()) > 0)
    @rule(data=st.data())
    def remove(self, data):
        item = data.draw(st.sampled_from(sorted(+self.model)))
        self.cart.remove(item)
        self.model[item] -= 1

    @invariant()
    def total_matches_model(self):
        expected = sum(impl.PRICES[i] * n for i, n in self.model.items())
        assert self.cart.total == expected, (self.cart.total, expected)


CartMachine.TestCase.settings = settings(max_examples=200, deadline=None)
TestCart = CartMachine.TestCase


if __name__ == "__main__":
    unittest.main()
