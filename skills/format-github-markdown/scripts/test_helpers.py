"""Run with Python unittest; the real lint-runner test requires bunx."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent


class MarkdownToolsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "project with spaces"
        self.root.mkdir()

    def ensure(self):
        return subprocess.run(
            ["bash", str(SCRIPTS / "ensure-markdownlint-cli2.sh"), str(self.root)],
            capture_output=True,
            text=True,
            check=False,
            env={**os.environ, "CDPATH": self.temporary.name},
        )

    def test_installed_policy_is_discovered_by_real_cli(self):
        installed = self.ensure()
        self.assertEqual(installed.returncode, 0, installed.stderr)
        self.assertEqual(
            installed.stdout.strip(), str(self.root / ".markdownlint-cli2.jsonc")
        )
        document = self.root / "sample.md"
        document.write_text("# Sample\n\n* Item\n")
        result = subprocess.run(
            ["bash", str(SCRIPTS / "lint-markdown.sh"), "sample.md"],
            cwd=self.root,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("MD004", result.stdout + result.stderr)

    def test_preserves_existing_rule_configuration(self):
        config = self.root / ".markdownlint.json"
        original = b'{"MD013":{"line_length":120}}\n'
        config.write_bytes(original)
        result = self.ensure()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(config))
        self.assertEqual(config.read_bytes(), original)
        self.assertFalse((self.root / ".markdownlint-cli2.jsonc").exists())

    def test_preserves_existing_cli_configuration(self):
        config = self.root / ".markdownlint-cli2.yaml"
        original = b"config:\n  MD013:\n    line_length: 100\n"
        config.write_bytes(original)
        result = self.ensure()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(config.read_bytes(), original)
        self.assertFalse((self.root / ".markdownlint-cli2.jsonc").exists())

    def test_refuses_to_mask_unsupported_configuration_name(self):
        config = self.root / ".markdownlint-cli2.json"
        original = b'{"config":{"MD013":false}}\n'
        config.write_bytes(original)
        result = self.ensure()
        self.assertEqual(result.returncode, 1)
        self.assertIn("not auto-discovered", result.stderr)
        self.assertEqual(config.read_bytes(), original)
        self.assertFalse((self.root / ".markdownlint-cli2.jsonc").exists())

    def test_does_not_replace_dangling_configuration_symlink(self):
        config = self.root / ".markdownlint-cli2.jsonc"
        target = self.root / "absent.jsonc"
        config.symlink_to(target)
        result = self.ensure()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(config.is_symlink())
        self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
