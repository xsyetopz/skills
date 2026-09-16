"""Behavioral checks plus deliberate mutants; stdlib only."""

import importlib.util
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

_module_path = (
    Path(__file__).resolve().parents[1] / "assets/examples/explicit_behavior.py"
)
_spec = importlib.util.spec_from_file_location("explicit_behavior", _module_path)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"cannot load {_module_path}")
_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_module)
effective_timeout = _module.effective_timeout
nonempty_lines = _module.nonempty_lines
open_nonempty_lines = _module.open_nonempty_lines
option = _module.option
render_named = _module.render_named


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


if __name__ == "__main__":
    unittest.main()
