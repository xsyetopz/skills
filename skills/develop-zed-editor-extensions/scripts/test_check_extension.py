"""Tests for check_extension.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import io
import os
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_extension

MIT = (
    "MIT License\n\nCopyright (c) 2026 A\n\nPermission is hereby granted, free "
    "of charge, to any person obtaining a copy\nof this software. The above "
    "copyright notice and this permission notice shall be included in all\n"
    'copies. THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, '
    "EXPRESS OR\nIMPLIED.\n"
)
MANIFEST = """\
id = "demo-lang"
name = "Demo"
version = "0.1.0"
schema_version = 1
authors = ["A <a@example.com>"]
description = "Demo language support for tests"
repository = "https://github.com/example/demo"

[grammars.demo]
repository = "https://github.com/example/tree-sitter-demo"
rev = "0123456789abcdef0123456789abcdef01234567"
"""
CONFIG = """\
name = "Demo"
grammar = "demo"
path_suffixes = ["demo"]
"""


def build(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for relative, text in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(text), encoding="utf-8")
    return root


def run(root: Path, *flags: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        status = check_extension.main([str(root), *flags])
    return status, out.getvalue()


def language(**overrides: str) -> dict[str, str]:
    files = {
        "extension.toml": MANIFEST,
        "LICENSE": MIT,
        "languages/demo/config.toml": CONFIG,
        "languages/demo/highlights.scm": "(comment) @comment\n",
    }
    files.update(overrides)
    return files


class ManifestTests(unittest.TestCase):
    def test_valid_language_extension_passes_registry_rules(self) -> None:
        status, output = run(build(language()), "--registry")
        self.assertEqual(status, 0, output)
        self.assertIn("0 errors", output)

    def test_hyphenated_table_is_reported_as_ignored(self) -> None:
        manifest = MANIFEST + '\n[language-servers.x]\nlanguages = ["Demo"]\n'
        status, output = run(build(language(**{"extension.toml": manifest})))
        self.assertEqual(status, 1)
        self.assertIn("did you mean `language_servers`", output)

    def test_branch_name_is_not_a_pinned_rev(self) -> None:
        manifest = MANIFEST.replace("0123456789abcdef0123456789abcdef01234567", "main")
        _, output = run(build(language(**{"extension.toml": manifest})))
        self.assertIn("40-character commit SHA", output)

    def test_slash_commands_are_rejected(self) -> None:
        manifest = MANIFEST + (
            '\n[slash_commands.echo]\ndescription = "echo"\nrequires_argument = true\n'
        )
        status, output = run(build(language(**{"extension.toml": manifest})))
        self.assertEqual(status, 1)
        self.assertIn("slash commands were removed", output)

    def test_file_url_grammar_is_dev_only(self) -> None:
        manifest = MANIFEST.replace(
            "https://github.com/example/tree-sitter-demo",
            "file:///tmp/tree-sitter-demo",
        )
        files = language(**{"extension.toml": manifest})
        status, output = run(build(files))
        self.assertEqual(status, 0, output)
        status, output = run(build(files), "--registry")
        self.assertEqual(status, 1)
        self.assertIn("file:// grammars work only for dev installs", output)

    def test_uncompilable_first_line_pattern_warns(self) -> None:
        config = CONFIG + "first_line_pattern = '^#!(make'\n"
        files = language(**{"languages/demo/config.toml": config})
        status, output = run(build(files))
        self.assertEqual(status, 0, output)
        self.assertIn("`first_line_pattern` does not compile", output)

    def test_commit_alias_is_accepted(self) -> None:
        manifest = MANIFEST.replace("rev =", "commit =")
        status, output = run(build(language(**{"extension.toml": manifest})))
        self.assertEqual(status, 0, output)

    def test_language_grammar_must_be_declared(self) -> None:
        config = CONFIG.replace('"demo"\n', '"other"\n', 1)
        files = language(**{"languages/demo/config.toml": config})
        _, output = run(build(files))
        self.assertIn("grammar 'other' is not in extension.toml", output)

    def test_unknown_query_file_is_rejected(self) -> None:
        files = language(**{"languages/demo/folds.scm": "(x) @fold\n"})
        _, output = run(build(files))
        self.assertIn("query file name is not supported", output)

    def test_not_in_scope_must_exist_in_overrides(self) -> None:
        config = CONFIG + (
            'brackets = [{ start = "(", end = ")", close = true, '
            'newline = false, not_in = ["string"] }]\n'
        )
        files = language(
            **{
                "languages/demo/config.toml": config,
                "languages/demo/overrides.scm": "(comment) @comment\n",
            }
        )
        status, output = run(build(files))
        self.assertEqual(status, 1)
        self.assertIn("Zed fails to load the language", output)

    def test_not_in_without_overrides_file_only_warns(self) -> None:
        config = CONFIG + (
            'brackets = [{ start = "(", end = ")", close = true, '
            'newline = false, not_in = ["string"] }]\n'
        )
        files = language(**{"languages/demo/config.toml": config})
        status, output = run(build(files))
        self.assertEqual(status, 0, output)
        self.assertIn("has no effect", output)


class RustTests(unittest.TestCase):
    CARGO = """\
    [package]
    name = "demo"
    version = "0.1.0"
    edition = "2021"

    [lib]
    crate-type = ["cdylib"]

    [dependencies]
    zed_extension_api = "=0.7.0"
    """

    def server_files(self, cargo: str) -> dict[str, str]:
        manifest = MANIFEST + '\n[language_servers.demo]\nlanguages = ["Demo"]\n'
        return language(
            **{"extension.toml": manifest, "Cargo.toml": cargo, "src/lib.rs": ""}
        )

    def test_pinned_crate_passes(self) -> None:
        status, output = run(build(self.server_files(self.CARGO)))
        self.assertEqual(status, 0, output)

    def test_missing_cdylib_fails(self) -> None:
        cargo = self.CARGO.replace('crate-type = ["cdylib"]', "")
        _, output = run(build(self.server_files(cargo)))
        self.assertIn('crate-type must include "cdylib"', output)

    def test_unreleased_api_is_rejected(self) -> None:
        cargo = self.CARGO.replace("=0.7.0", "0.8.0")
        _, output = run(build(self.server_files(cargo)))
        self.assertIn("newer than the 0.7 API", output)

    def test_rust_without_servers_is_rejected(self) -> None:
        files = language(**{"Cargo.toml": self.CARGO})
        _, output = run(build(files))
        self.assertIn("Rust code without a server", output)


class RegistryTests(unittest.TestCase):
    def test_registry_rejects_bad_identity(self) -> None:
        manifest = (
            MANIFEST.replace('id = "demo-lang"', 'id = "zed-demo-extension"')
            .replace('name = "Demo"', 'name = "Demo Extension"')
            .replace('description = "Demo language support for tests"', "")
        )
        _, output = run(build(language(**{"extension.toml": manifest})), "--registry")
        self.assertIn("must not start with 'zed-'", output)
        self.assertIn("must not contain 'extension'", output)
        self.assertIn("description must be longer than the name", output)

    def test_registry_requires_license(self) -> None:
        files = language()
        del files["LICENSE"]
        _, output = run(build(files), "--registry")
        self.assertIn("no LICENSE/LICENCE file", output)

    def test_theme_cannot_be_mixed_with_languages(self) -> None:
        files = language(**{"themes/t.json": "{}"})
        _, output = run(build(files), "--registry")
        self.assertIn("themes cannot be mixed", output)


if __name__ == "__main__":
    unittest.main()
