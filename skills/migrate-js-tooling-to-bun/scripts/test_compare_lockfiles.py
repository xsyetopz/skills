"""Tests for compare_lockfiles.py (stdlib only; run directly)."""

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

import compare_lockfiles as cl

NPM = {
    "lockfileVersion": 3,
    "packages": {
        "": {},
        "node_modules/left-pad": {"version": "1.3.0"},
        "node_modules/@x/util": {"resolved": "packages/util", "link": True},
    },
}
BUN = """{
  "lockfileVersion": 2,
  "packages": {
    "left-pad": ["left-pad@1.3.0", "", {}, "sha512-x"],
    "@x/util": ["@x/util@workspace:packages/util"],
  },
}
"""


def run(old: str, bun_text: str, *flags: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        npm_path = Path(tmp) / "package-lock.json"
        bun_path = Path(tmp) / "bun.lock"
        npm_path.write_text(old)
        bun_path.write_text(bun_text)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            status = cl.main([str(npm_path), str(bun_path), *flags])
        return status, out.getvalue()


class CompareTests(unittest.TestCase):
    def test_same_resolutions(self) -> None:
        status, output = run(json.dumps(NPM), BUN)
        self.assertEqual(status, 0, output)
        self.assertIn("same=2", output)

    def test_changed_version_is_reported(self) -> None:
        status, output = run(json.dumps(NPM), BUN.replace("1.3.0", "1.3.1"))
        self.assertEqual(status, 1)
        self.assertIn("~ left-pad 1.3.0 -> 1.3.1", output)

    def test_added_package_is_reported(self) -> None:
        extra = BUN.replace(
            '"packages": {', '"packages": {\n    "chalk": ["chalk@5.0.0", "", {}, ""],'
        )
        status, output = run(json.dumps(NPM), extra)
        self.assertEqual(status, 1)
        self.assertIn("+ chalk 5.0.0", output)

    def test_json_report(self) -> None:
        status, output = run(json.dumps(NPM), BUN.replace("1.3.0", "1.3.1"), "--json")
        self.assertEqual(status, 1)
        self.assertEqual(
            json.loads(output),
            {
                "added": {},
                "removed": {},
                "changed": {"left-pad": ["1.3.0", "1.3.1"]},
                "same": 1,
            },
        )

    def test_bad_json_is_input_error(self) -> None:
        status, output = run("{not json", BUN)
        self.assertEqual(status, 2)
        self.assertIn("expected OLD to be package-lock.json", output)

    def test_nested_versions_are_refused(self) -> None:
        for path in (
            "node_modules/a/node_modules/left-pad",
            "packages/x/node_modules/b",
        ):
            with self.subTest(path=path):
                nested = {"packages": {**NPM["packages"], path: {"version": "1.0.0"}}}
                status, output = run(json.dumps(nested), BUN)
                self.assertEqual(status, 2)
                self.assertIn("nested install", output)


if __name__ == "__main__":
    unittest.main()
