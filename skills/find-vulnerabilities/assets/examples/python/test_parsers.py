"""Exploit-condition and fix tests for parsers.py and yaml_loading.py.

Run: python3 test_parsers.py
The pickle payload calls parsers.record_call (a list append). The XXE
payload reads a synthetic file in a TemporaryDirectory.
"""

from __future__ import annotations

import gc
import importlib.util
import itertools
import json
import os
import pickle
import pyexpat
import sys
import tempfile
import unittest
import warnings
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import parsers

HAVE_YAML = importlib.util.find_spec("yaml") is not None


class CallsRecorder:
    """Pickles to 'call parsers.record_call("ran")' when loaded."""

    def __reduce__(self) -> tuple:
        return (parsers.record_call, ("ran",))


def laughs(levels: int = 10) -> str:
    """Nested entities: each level repeats the previous one ten times."""
    names = [f"e{i}" for i in range(levels)]
    decls = [f'<!ENTITY {names[0]} "lol">']
    for prev, name in itertools.pairwise(names):
        decls.append(f'<!ENTITY {name} "{("&" + prev + ";") * 10}">')
    body = "".join(decls)
    return f"<?xml version='1.0'?><!DOCTYPE r [{body}]><r>&{names[-1]};</r>"


class Deserialization(unittest.TestCase):
    def setUp(self) -> None:
        parsers.CALLS.clear()
        self.payload = pickle.dumps(CallsRecorder())

    def test_pickle_invokes_callable_named_in_data(self) -> None:
        self.assertEqual(parsers.vulnerable_load_session(self.payload), "ran")
        self.assertEqual(parsers.CALLS, ["ran"])

    def test_json_cannot_name_a_callable(self) -> None:
        with self.assertRaises(ValueError):
            parsers.fixed_load_session(self.payload)
        self.assertEqual(parsers.CALLS, [])
        ok = parsers.fixed_load_session(json.dumps({"user": 7}).encode())
        self.assertEqual(ok, {"user": 7})

    def test_restricted_unpickler_forbids_unlisted_globals(self) -> None:
        with self.assertRaises(pickle.UnpicklingError):
            parsers.restricted_load(self.payload)
        self.assertEqual(parsers.CALLS, [])
        self.assertEqual(parsers.restricted_load(pickle.dumps({1, 2})), {1, 2})


@unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
class YamlLoading(unittest.TestCase):
    def test_unsafe_loader_calls_tagged_function(self) -> None:
        import yaml_loading

        parsers.CALLS.clear()
        doc = "!!python/object/apply:parsers.record_call ['ran']"
        self.assertEqual(yaml_loading.vulnerable_load(doc), "ran")
        self.assertEqual(parsers.CALLS, ["ran"])
        with self.assertRaises(Exception) as caught:
            yaml_loading.fixed_load(doc)
        self.assertEqual(type(caught.exception).__name__, "ConstructorError")
        self.assertEqual(yaml_loading.fixed_load("a: [1, 2]"), {"a": [1, 2]})


class ExternalEntities(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        secret = Path(directory.name) / "secret.txt"
        secret.write_text("SYNTHETIC-SECRET")
        self.doc = (
            "<?xml version='1.0'?>"
            f"<!DOCTYPE r [<!ENTITY x SYSTEM '{secret.as_uri()}'>]>"
            "<r>&x;</r>"
        )

    def test_enabled_external_entities_read_local_file(self) -> None:
        # The stdlib SAX reader leaves the entity's file handle to the GC.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            text = parsers.vulnerable_sax_text(self.doc)
            gc.collect()
        self.assertIn("SYNTHETIC-SECRET", text)

    def test_default_sax_skips_external_entity(self) -> None:
        self.assertEqual(parsers.fixed_sax_text(self.doc), "")

    def test_elementtree_rejects_undefined_external_entity(self) -> None:
        with self.assertRaises(ET.ParseError):
            ET.fromstring(self.doc)

    def test_no_dtd_parser_rejects_doctype(self) -> None:
        with self.assertRaises(ValueError):
            parsers.no_dtd_text(self.doc)
        with self.assertRaises(ValueError):
            parsers.no_dtd_text(laughs())
        self.assertEqual(parsers.no_dtd_text("<r>ok</r>"), "ok")


class EntityExpansion(unittest.TestCase):
    def test_expat_amplification_limit(self) -> None:
        print(f"\n  {pyexpat.EXPAT_VERSION}", file=sys.stderr)
        if pyexpat.version_info < (2, 7, 2):
            self.skipTest("Python docs: Expat < 2.7.2 may be vulnerable")
        with self.assertRaises(ET.ParseError) as caught:
            ET.fromstring(laughs())
        self.assertIn("amplification", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
