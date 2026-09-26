"""Tests for check_theme.py (stdlib only; run directly).

The schemas below are reduced copies of the published Zed schemas
(https://zed.dev/schema/themes/v0.2.0.json and
https://zed.dev/schema/icon_themes/v0.3.0.json) with the same keywords.
"""

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

import check_theme

THEME_SCHEMA = {
    "title": "ThemeFamilyContent",
    "type": "object",
    "required": ["author", "name", "themes"],
    "properties": {
        "author": {"type": "string"},
        "name": {"type": "string"},
        "themes": {
            "type": "array",
            "items": {"$ref": "#/definitions/ThemeContent"},
        },
    },
    "definitions": {
        "Appearance": {"type": "string", "enum": ["light", "dark"]},
        "ThemeContent": {
            "type": "object",
            "required": ["appearance", "name", "style"],
            "properties": {
                "appearance": {"$ref": "#/definitions/Appearance"},
                "name": {"type": "string"},
                "style": {"$ref": "#/definitions/ThemeStyleContent"},
            },
        },
        "ThemeStyleContent": {
            "type": "object",
            "properties": {
                "background": {"type": ["string", "null"]},
                "text": {"type": ["string", "null"]},
                "syntax": {
                    "type": "object",
                    "additionalProperties": {
                        "type": "object",
                        "properties": {"color": {"type": ["string", "null"]}},
                    },
                },
            },
        },
    },
}
ICON_SCHEMA = {
    "title": "IconThemeFamilyContent",
    "type": "object",
    "required": ["author", "name", "themes"],
    "properties": {"themes": {"type": "array"}},
}


def theme(**style: object) -> dict:
    base: dict[str, object] = {"background": "#101010", "text": "#eeeeeeff"}
    base.update(style)
    return {
        "name": "T",
        "author": "A",
        "themes": [{"name": "T Dark", "appearance": "dark", "style": base}],
    }


def run(data: dict, schema: dict, files: tuple[str, ...] = ()) -> tuple[int, str]:
    root = Path(tempfile.mkdtemp())
    for relative in files:
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        (root / relative).write_text("<svg/>", encoding="utf-8")
    target = root / "subject.json"
    target.write_text(json.dumps(data), encoding="utf-8")
    schema_path = root / "schema.json"
    schema_path.write_text(json.dumps(schema), encoding="utf-8")
    out = io.StringIO()
    argv = [str(target), "--schema", str(schema_path), "--root", str(root)]
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        status = check_theme.main(argv)
    return status, out.getvalue()


class ThemeTests(unittest.TestCase):
    def test_valid_theme_passes(self) -> None:
        data = theme(syntax={"comment": {"color": "#888"}})
        status, output = run(data, THEME_SCHEMA)
        self.assertEqual(status, 0, output)

    def test_schema_violation_is_an_error(self) -> None:
        data = theme()
        data["themes"][0]["appearance"] = "dim"
        del data["author"]
        status, output = run(data, THEME_SCHEMA)
        self.assertEqual(status, 1)
        self.assertIn("'dim' not in", output)
        self.assertIn("missing required `author`", output)

    def test_named_colors_are_rejected(self) -> None:
        status, output = run(theme(text="red"), THEME_SCHEMA)
        self.assertEqual(status, 1)
        self.assertIn("bad color 'red'", output)

    def test_unknown_style_key_is_a_warning(self) -> None:
        status, output = run(theme(**{"editor.bg": "#000"}), THEME_SCHEMA)
        self.assertEqual(status, 0)
        self.assertIn("WARN /themes/0/style/editor.bg", output)

    def test_deprecated_scrollbar_key_is_an_error(self) -> None:
        data = theme(**{"scrollbar_thumb.background": "#fff"})
        status, output = run(data, THEME_SCHEMA)
        self.assertEqual(status, 1)
        self.assertIn("scrollbar.thumb.background", output)


class IconThemeTests(unittest.TestCase):
    def icons(self) -> dict:
        return {
            "name": "I",
            "author": "A",
            "themes": [
                {
                    "name": "I",
                    "appearance": "dark",
                    "file_suffixes": {"rs": "rust", "md": "markdown"},
                    "file_icons": {"rust": {"path": "./icons/rust.svg"}},
                }
            ],
        }

    def test_missing_icon_file_is_an_error(self) -> None:
        status, output = run(self.icons(), ICON_SCHEMA)
        self.assertEqual(status, 1)
        self.assertIn("missing file ./icons/rust.svg", output)

    def test_dangling_suffix_is_a_warning(self) -> None:
        status, output = run(self.icons(), ICON_SCHEMA, ("icons/rust.svg",))
        self.assertEqual(status, 0, output)
        self.assertIn("'markdown' is not a file_icons key", output)


if __name__ == "__main__":
    unittest.main()
