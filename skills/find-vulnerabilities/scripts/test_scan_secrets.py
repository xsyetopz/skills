"""Tests for scan_secrets.py (stdlib only). Run: python3 test_scan_secrets.py

Synthetic credentials are assembled at run time so this file itself does
not look like a leak to gitleaks or push protection.
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import secrets
import string
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import scan_secrets


def fake(prefix: str, alphabet: str, size: int) -> str:
    return prefix + "".join(secrets.choice(alphabet) for _ in range(size))


UPPER = string.ascii_uppercase + string.digits
ALNUM = string.ascii_letters + string.digits


class Rules(unittest.TestCase):
    def rules(self, text: str) -> list[str]:
        return [m.rule for m in scan_secrets.scan_text("x", text)]

    def test_each_rule_matches_a_synthetic_value(self) -> None:
        cases = {
            "aws-access-key-id": f'k = "{fake("AK" + "IA", UPPER, 16)}"',
            "github-token": f"t={fake('gh' + 'p_', ALNUM, 36)}",
            "private-key": "-----BEGIN RSA " + "PRIVATE KEY-----",
            "assigned-secret": 'db_password = "' + secrets.token_hex(8) + '"',
        }
        for rule, text in cases.items():
            with self.subTest(rule=rule):
                self.assertIn(rule, self.rules(text))

    def test_ordinary_code_does_not_match(self) -> None:
        text = "\n".join(
            [
                'password = os.environ["DB_PASSWORD"]',
                "token = request.headers.get('X-Token')",
                'name = "AKIA"',
                "-----BEGIN PUBLIC KEY-----",
            ]
        )
        self.assertEqual(self.rules(text), [])

    def test_preview_is_redacted(self) -> None:
        value = secrets.token_hex(12)
        match = scan_secrets.scan_text("x", f'api_key = "{value}"')[0]
        self.assertEqual(match.preview, value[:4] + "...")
        self.assertNotIn(value, repr(match))


class Cli(unittest.TestCase):
    def test_exit_codes_and_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.py").write_text("x = 1\n")
            code, out = self.run_main([str(root)])
            self.assertEqual((code, out.strip()), (0, "0 match(es)"))
            (root / "app.py").write_text(f'K = "{fake("AS" + "IA", UPPER, 16)}"\n')
            (root / ".git").mkdir()
            (root / ".git" / "cfg").write_text(f'K = "{fake("AK" + "IA", UPPER, 16)}"')
            code, out = self.run_main([str(root), "--json"])
            self.assertEqual(code, 1)
            data = json.loads(out)
            self.assertEqual(
                [(d["rule"], d["line"]) for d in data], [("aws-access-key-id", 1)]
            )

    def test_skip_dirs_apply_below_the_root_only(self) -> None:
        # A checkout under a directory named "target" is still scanned.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "target" / "repo"
            root.mkdir(parents=True)
            (root / "app.py").write_text(f'K = "{fake("AK" + "IA", UPPER, 16)}"\n')
            code, _ = self.run_main([str(root)])
            self.assertEqual(code, 1)

    def test_limit_bounds_the_listing_not_the_count(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            keys = [f'K = "{fake("AK" + "IA", UPPER, 16)}"' for _ in range(3)]
            (root / "app.py").write_text("\n".join(keys) + "\n")
            with contextlib.redirect_stderr(io.StringIO()) as err:
                code, out = self.run_main([str(root), "--limit", "1"])
                json_code, json_out = self.run_main(
                    [str(root), "--limit", "2", "--json"]
                )
        self.assertEqual(code, 1)
        self.assertEqual(len(out.splitlines()), 2)
        self.assertEqual(out.splitlines()[-1], "3 match(es)")
        self.assertEqual((json_code, len(json.loads(json_out))), (1, 2))
        self.assertIn("showing 1 of 3 matches", err.getvalue())

    def test_missing_path_is_a_usage_error(self) -> None:
        with contextlib.redirect_stderr(io.StringIO()) as err:
            code, out = self.run_main(["/nonexistent/scan-root"])
        self.assertEqual((code, out), (2, ""))
        self.assertIn("no such file or directory", err.getvalue())

    def run_main(self, argv: list[str]) -> tuple[int, str]:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = scan_secrets.main(argv)
        return code, buffer.getvalue()


if __name__ == "__main__":
    unittest.main()
