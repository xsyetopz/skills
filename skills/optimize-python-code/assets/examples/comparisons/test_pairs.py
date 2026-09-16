"""Expected values and exhaustive small-domain differential tests."""

import itertools
import unittest
from pairs import PAIRS


class PairTests(unittest.TestCase):
    def test_expected_results_and_input_ownership(self) -> None:
        numeric = [[], [0], [-3, 2, 2, 0, 5], [10**40, -(10**40)]]
        textual = [[], [""], ["é", "e\u0301", "é", "🙂", "\0"]]
        for values in numeric:
            before = list(values)
            for fn in PAIRS[0]:
                self.assertEqual(fn(values), before)
            expected_sum = 0
            for value in values:
                if value % 2 == 0:
                    expected_sum += value * value
            for fn in PAIRS[4]:
                self.assertEqual(fn(values), expected_sum)
            expected_max = None
            for value in values:
                if expected_max is None or value > expected_max:
                    expected_max = value
            for fn in PAIRS[5]:
                self.assertEqual(fn(values), expected_max)
            self.assertEqual(values, before)
        for values in textual:
            for fn in PAIRS[1]:
                self.assertEqual(list(fn(values)), list("".join(values)))
            for fn in PAIRS[2]:
                self.assertEqual(
                    fn(values, ["missing", "é"]), [False, "é" in values]
                )
            counts: dict[str, int] = {}
            for value in values:
                counts[value] = counts.get(value, 0) + 1
            for fn in PAIRS[3]:
                self.assertEqual(list(fn(values).items()), list(counts.items()))
        for fn in PAIRS[1]:
            self.assertEqual(fn(["a", "", "é", "🙂"]), "aé🙂")
        for fn in PAIRS[3]:
            self.assertEqual(fn(["b", "a", "b"]), {"b": 2, "a": 1})

    def test_exhaustive_small_inputs(self) -> None:
        for length in range(6):
            for tup in itertools.product((-1, 0, 2), repeat=length):
                values = list(tup)
                texts = list(map(str, values))
                arguments = [
                    (values,),
                    (texts,),
                    (texts, ["-1", "8"]),
                    (texts,),
                    (values,),
                    (values,),
                    (bytes(value & 0xFF for value in values),),
                    (values,),
                ]
                for (baseline, candidate), args in zip(
                    PAIRS, arguments, strict=True
                ):
                    self.assertEqual(baseline(*args), candidate(*args))

    def test_semantic_traps(self) -> None:
        # Sorting is not interchangeable for arbitrary objects when equal-key
        # identity matters. This pair admits only builtin integers.
        a, b = {"key": 1, "id": "first"}, {"key": 1, "id": "last"}
        self.assertIs(max([a, b], key=lambda value: value["key"]), a)
        self.assertIs(sorted([a, b], key=lambda value: value["key"])[-1], b)
        # Eager and lazy callbacks have different timing. The pair uses only
        # pure callbacks.
        events: list[int] = []
        lazy = (events.append(i) for i in range(3))
        self.assertEqual(events, [])
        next(lazy)
        self.assertEqual(events, [0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
