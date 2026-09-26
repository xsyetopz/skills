"""Behavioral checks plus deliberate mutants for every example; stdlib only.

Run: python3 test_examples.py (from this directory or any other).
"""

import io
import os
import sys
import tempfile
import timeit
import unittest
import warnings
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import structure
import structure_before
import surface
from explicit_errors import (
    effective_timeout,
    nonempty_lines,
    open_nonempty_lines,
    option,
    parse_release_date,
    read_port,
    remove_if_present,
    render_named,
)


class ExampleTests(unittest.TestCase):
    def test_unspecified_default(self):
        self.assertEqual(effective_timeout(None, 10), 10)

    def test_zero_is_not_missing(self):
        self.assertEqual(effective_timeout(0, 10), 0)
        self.assertEqual(effective_timeout(5, 10), 5)

    def test_present_falsey_options_are_preserved(self):
        for value in (None, False, 0, ""):
            with self.subTest(value=value):
                self.assertIs(option({"x": value}, "x", "default"), value)
        self.assertEqual(option({}, "x", "default"), "default")

    def test_renderer_output(self):
        self.assertEqual(render_named({"plain": str}, "plain", 42), "42")

    def test_missing_renderer_has_lookup_cause(self):
        with self.assertRaisesRegex(ValueError, "unknown renderer") as caught:
            render_named({}, "missing", 42)
        self.assertIsInstance(caught.exception.__cause__, KeyError)

    def test_renderer_keyerror_is_not_relabelled(self):
        error = KeyError("renderer-internal")

        def renderer(_):
            raise error

        with self.assertRaises(KeyError) as caught:
            render_named({"x": renderer}, "x", 42)
        self.assertIs(caught.exception, error)

    def test_renderer_other_exception_propagates(self):
        def renderer(_):
            raise RuntimeError("internal")

        with self.assertRaisesRegex(RuntimeError, "internal"):
            render_named({"x": renderer}, "x", 42)

    def test_borrowed_resource_is_not_closed(self):
        stream = io.StringIO("one\n\n two \r\n")
        self.assertEqual(list(nonempty_lines(stream)), ["one", " two "])
        self.assertFalse(stream.closed)

    def test_owned_resource_closes_after_partial_consumption(self):
        stream = io.StringIO("one\ntwo\n")
        with patch.object(Path, "open", return_value=stream):
            with open_nonempty_lines(Path("fixture")) as lines:
                self.assertEqual(next(lines), "one")
                self.assertFalse(stream.closed)
            self.assertTrue(stream.closed)

    def test_owned_resource_closes_after_exception(self):
        stream = io.StringIO("one\ntwo\n")
        with (
            patch.object(Path, "open", return_value=stream),
            self.assertRaisesRegex(RuntimeError, "consumer"),
            open_nonempty_lines(Path("fixture")) as lines,
        ):
            next(lines)
            raise RuntimeError("consumer")
        self.assertTrue(stream.closed)

    def test_real_file_unicode(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "names.txt"
            path.write_text("café\n\n🙂\n", encoding="utf-8")
            with open_nonempty_lines(path) as lines:
                self.assertEqual(list(lines), ["café", "🙂"])

    def test_oracle_kills_truthiness_mutant(self):
        def mutant(value, default):
            return value or default

        with self.assertRaises(AssertionError):
            self.assertEqual(mutant(0, 10), 0)

    def check_renderer_error_identity(self, operation):
        original = KeyError("renderer-internal")

        def broken(_):
            raise original

        try:
            operation({"x": broken}, "x", 0)
        except KeyError as observed:
            self.assertIs(observed, original, "renderer exception was replaced")
        except ValueError:
            self.fail("renderer exception was replaced")
        else:
            self.fail("renderer exception was swallowed")

    def test_same_oracle_accepts_implementation_and_rejects_exception_mutant(self):
        def mutant(renderers, name, value):
            try:
                return renderers[name](value)
            except KeyError as exc:
                raise ValueError("unknown renderer") from exc

        self.check_renderer_error_identity(render_named)
        with self.assertRaisesRegex(AssertionError, "renderer exception was replaced"):
            self.check_renderer_error_identity(mutant)


class ExplicitErrorTests(unittest.TestCase):
    def test_remove_if_present_silences_only_missing_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gone.txt"
            remove_if_present(path)  # missing: silenced
            path.write_text("x")
            remove_if_present(path)
            self.assertFalse(path.exists())
            # Linux raises IsADirectoryError, macOS PermissionError (EPERM).
            with self.assertRaises((IsADirectoryError, PermissionError)):
                remove_if_present(Path(directory))  # other errors surface

    def test_parse_release_date_refuses_ambiguous_forms(self):
        self.assertEqual(str(parse_release_date("2025-04-03")), "2025-04-03")
        for text in ("03/04/2025", "2025-4-3", "20250403", "2025-04-03T00:00"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_release_date(text)

    def test_read_port_refuses_conflicting_keys(self):
        self.assertEqual(read_port({"port": "80"}), 80)
        self.assertEqual(read_port({"listen_port": "81"}), 81)
        self.assertEqual(read_port({"port": "80", "listen_port": "80"}), 80)
        with self.assertRaisesRegex(ValueError, "conflicts"):
            read_port({"port": "80", "listen_port": "81"})
        with self.assertRaises(KeyError):
            read_port({})

    def test_guessing_mutant_is_rejected(self):
        def mutant(settings):
            return int(settings.get("port") or settings["listen_port"])

        with self.assertRaises(AssertionError), self.assertRaises(ValueError):
            mutant({"port": "80", "listen_port": "81"})


ORDERS = [
    structure.Order(paid, items, address)
    for paid in (True, False)
    for items in (0, 1, 3)
    for address in (None, "Main St 1")
]


class StructureTests(unittest.TestCase):
    def test_format_price_matches_hierarchy(self):
        for cents in (0, 5, 99, 100, 123456):
            for currency in ("EUR", "USD"):
                with self.subTest(cents=cents, currency=currency):
                    self.assertEqual(
                        structure.format_price(cents, currency),
                        structure_before.format_price(cents, currency),
                    )

    def test_flat_label_matches_nested_on_every_order(self):
        for order in ORDERS:
            with self.subTest(order=order):
                self.assertEqual(
                    structure.shipping_label(order),
                    structure_before.shipping_label(order),
                )

    def test_chunks_match_special_cased_version(self):
        for length in range(12):
            for size in range(1, 6):
                items = list(range(length))
                with self.subTest(length=length, size=size):
                    self.assertEqual(
                        structure.chunks(items, size),
                        structure_before.chunks(items, size),
                    )

    def test_retry_succeeds_after_transient_errors(self):
        calls, pauses = [], []

        def flaky():
            calls.append(1)
            if len(calls) < 3:
                raise TimeoutError
            return "ok"

        result = structure.retry(
            flaky,
            attempts=3,
            retry_on=TimeoutError,
            delays=[0.1, 0.2],
            sleep=pauses.append,
        )
        self.assertEqual((result, len(calls), pauses), ("ok", 3, [0.1, 0.2]))

    def test_retry_reraises_last_error_and_skips_other_errors(self):
        def always():
            raise TimeoutError("last")

        with self.assertRaisesRegex(TimeoutError, "last"):
            structure.retry(
                always,
                attempts=2,
                retry_on=TimeoutError,
                delays=[0],
                sleep=lambda _: None,
            )
        calls = []

        def wrong():
            calls.append(1)
            raise KeyError("bug")

        with self.assertRaises(KeyError):
            structure.retry(
                wrong,
                attempts=5,
                retry_on=TimeoutError,
                delays=[0] * 4,
                sleep=lambda _: None,
            )
        self.assertEqual(len(calls), 1)


class SurfaceTests(unittest.TestCase):
    def test_public_surface_is_all(self):
        public = {n for n in dir(surface) if not n.startswith("_")}
        public -= {"annotations", "json", "warnings", "Iterable", "Mapping"}
        self.assertEqual(public, set(surface.__all__))

    def test_deprecated_alias_warns_at_caller(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            self.assertEqual(surface.read_config("{}"), {"retries": 3})
        self.assertEqual(caught[0].category, DeprecationWarning)
        self.assertEqual(caught[0].filename, __file__)

    def test_load_config_rejects_non_objects(self):
        with self.assertRaisesRegex(ValueError, "JSON object"):
            surface.load_config("[1, 2]")

    def test_build_index(self):
        self.assertEqual(surface.build_index(["a", "b", "a"]), {"a": [0, 2], "b": [1]})

    def test_is_power_of_two_matches_its_explanation(self):
        for n in range(-4, 4097):
            with self.subTest(n=n):
                expected = n > 0 and bin(n).count("1") == 1
                self.assertEqual(surface.is_power_of_two(n), expected)

    def test_explanation_mutant_without_positive_check_is_rejected(self):
        def mutant(n):
            return n & (n - 1) == 0

        self.assertTrue(mutant(0))  # 0 is not a power of two
        self.assertFalse(surface.is_power_of_two(0))


class StarImportTests(unittest.TestCase):
    def test_star_import_shadows_builtin_open(self):
        namespace = {}
        exec("from os import *", namespace)
        self.assertIs(namespace["open"], os.open)
        self.assertIsNot(namespace["open"], open)
        with self.assertRaisesRegex(TypeError, "flags"):
            namespace["open"]("f.txt")


def immutable_index(words):
    index = {}
    for position, word in enumerate(words):
        index = {**index, word: [*index.get(word, []), position]}
    return index


def measure_index(n=2000):
    """Return (mutating seconds, immutable seconds) for n words."""
    words = [f"w{i % 500}" for i in range(n)]
    assert immutable_index(words) == surface.build_index(words)
    fast = min(timeit.repeat(lambda: surface.build_index(words), number=10, repeat=7))
    slow = min(timeit.repeat(lambda: immutable_index(words), number=10, repeat=7))
    return fast, slow


if __name__ == "__main__":
    if sys.argv[1:] == ["measure"]:
        fast, slow = measure_index()
        print(f"build_index {fast:.4f}s immutable {slow:.4f}s ratio {slow / fast:.1f}x")
    else:
        unittest.main()
