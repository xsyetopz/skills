"""Tests for validate_schema.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import validate_schema as vs

SCHEMA = {
    "additionalProperties": False,
    "definitions": {
        "Decision": {"enum": ["allow", "deny"], "type": "string"},
        "Nullable": {"type": ["string", "null"]},
    },
    "properties": {
        "kind": {"const": "PreToolUse", "type": "string"},
        "decision": {"allOf": [{"$ref": "#/definitions/Decision"}]},
        "note": {"$ref": "#/definitions/Nullable"},
        "anything": True,
    },
    "required": ["kind"],
    "type": "object",
}


def errors(value):
    return vs.validate(SCHEMA, SCHEMA, value)


class ValidateTests(unittest.TestCase):
    def test_valid_document(self) -> None:
        document = {"kind": "PreToolUse", "decision": "deny", "note": None}
        self.assertEqual(errors(document), [])

    def test_boolean_schema_accepts_any_value(self) -> None:
        self.assertEqual(errors({"kind": "PreToolUse", "anything": [1, {}]}), [])

    def test_missing_required_and_wrong_const(self) -> None:
        self.assertIn("$: missing required 'kind'", errors({}))
        self.assertEqual(errors({"kind": "Stop"}), ["$.kind: expected 'PreToolUse'"])

    def test_enum_through_allof_ref(self) -> None:
        found = errors({"kind": "PreToolUse", "decision": "ask"})
        self.assertEqual(found, ["$.decision: 'ask' not in ['allow', 'deny']"])

    def test_additional_property_rejected(self) -> None:
        found = errors({"kind": "PreToolUse", "permission": "deny"})
        self.assertEqual(found, ["$: unexpected property 'permission'"])

    def test_bool_is_not_a_string(self) -> None:
        self.assertEqual(
            errors({"kind": "PreToolUse", "note": True}),
            ["$.note: expected string/null"],
        )

    def test_unknown_keyword_is_refused(self) -> None:
        schema = {"type": "string", "pattern": "^a"}
        with self.assertRaises(vs.Unsupported):
            vs.validate(schema, schema, "abc")


class CommandLineTests(unittest.TestCase):
    def run_main(self, schema: object, document: object, *extra: str):
        with tempfile.TemporaryDirectory() as tmp:
            schema_path = Path(tmp) / "schema.json"
            document_path = Path(tmp) / "doc.json"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")
            document_path.write_text(json.dumps(document), encoding="utf-8")
            out, err = io.StringIO(), io.StringIO()
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                status = vs.main([str(schema_path), str(document_path), *extra])
        return status, out.getvalue(), err.getvalue()

    def test_json_invalid_document(self) -> None:
        status, out, _ = self.run_main(SCHEMA, {}, "--json")
        self.assertEqual(status, 1)
        self.assertEqual(
            json.loads(out), {"valid": False, "errors": ["$: missing required 'kind'"]}
        )

    def test_json_valid_document(self) -> None:
        status, out, _ = self.run_main(SCHEMA, {"kind": "PreToolUse"}, "--json")
        self.assertEqual(status, 0)
        self.assertEqual(json.loads(out), {"valid": True, "errors": []})

    def test_unresolved_ref_is_exit_2_not_traceback(self) -> None:
        schema = {"$ref": "#/definitions/Missing"}
        status, out, err = self.run_main(schema, {}, "--json")
        self.assertEqual((status, out), (2, ""))
        self.assertIn("no matching definition", err)

    def test_non_object_subschema_is_exit_2(self) -> None:
        status, _, err = self.run_main({"properties": {"a": [1]}}, {"a": 1})
        self.assertEqual(status, 2)
        self.assertIn("schema at $.a is list", err)

    def test_ref_cycle_is_exit_2(self) -> None:
        schema = {
            "$ref": "#/definitions/A",
            "definitions": {"A": {"$ref": "#/definitions/A"}},
        }
        status, _, err = self.run_main(schema, {})
        self.assertEqual(status, 2)
        self.assertIn("$ref cycle", err)

    def test_wrong_argument_count_is_usage_error(self) -> None:
        with (
            contextlib.redirect_stderr(io.StringIO()),
            self.assertRaises(SystemExit) as caught,
        ):
            vs.main(["only-one.json"])
        self.assertEqual(caught.exception.code, 2)

    def test_help_documents_exit_status(self) -> None:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), self.assertRaises(SystemExit) as caught:
            vs.main(["--help"])
        self.assertEqual(caught.exception.code, 0)
        self.assertIn("Exit status:", out.getvalue())


if __name__ == "__main__":
    unittest.main()
