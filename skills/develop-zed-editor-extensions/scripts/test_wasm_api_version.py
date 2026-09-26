"""Tests for wasm_api_version.py (stdlib only; run directly)."""

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

import wasm_api_version as wav

MODULE_HEADER = b"\0asm\x01\x00\x00\x00"
COMPONENT_HEADER = b"\0asm\x0d\x00\x01\x00"


def section(section_id: int, body: bytes) -> bytes:
    assert len(body) < 128
    return bytes([section_id, len(body)]) + body


def custom(name: str, payload: bytes) -> bytes:
    raw = name.encode()
    return section(0, bytes([len(raw)]) + raw + payload)


def version_bytes(major: int, minor: int, patch: int) -> bytes:
    return b"".join(n.to_bytes(2, "big") for n in (major, minor, patch))


def run(data: bytes, *flags: str) -> tuple[int, str]:
    path = Path(tempfile.mkdtemp()) / "extension.wasm"
    path.write_bytes(data)
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        status = wav.main([str(path), *flags])
    return status, out.getvalue()


class VersionTests(unittest.TestCase):
    def test_reads_section_in_a_core_module(self) -> None:
        data = MODULE_HEADER + custom(wav.SECTION, version_bytes(0, 7, 0))
        self.assertEqual(wav.find_versions(data), [(0, 7, 0)])

    def test_reads_section_nested_in_a_component(self) -> None:
        inner = MODULE_HEADER + custom(wav.SECTION, version_bytes(0, 6, 0))
        data = COMPONENT_HEADER + custom("producers", b"x") + section(1, inner)
        status, output = run(data)
        self.assertEqual(status, 0)
        self.assertIn("zed:api-version 0.6.0", output)

    def test_max_rejects_newer_versions(self) -> None:
        data = MODULE_HEADER + custom(wav.SECTION, version_bytes(0, 8, 0))
        status, output = run(data, "--max", "0.7.0")
        self.assertEqual(status, 1)
        self.assertIn("0.8.0 is newer than 0.7.0", output)

    def test_short_max_is_padded_with_zeros(self) -> None:
        data = MODULE_HEADER + custom(wav.SECTION, version_bytes(0, 7, 0))
        self.assertEqual(run(data, "--max", "0.7")[0], 0)
        self.assertEqual(run(data, "--max", "0.6")[0], 1)

    def test_malformed_max_is_a_usage_error(self) -> None:
        data = MODULE_HEADER + custom(wav.SECTION, version_bytes(0, 7, 0))
        with self.assertRaises(SystemExit) as raised:
            run(data, "--max", "0.x")
        self.assertEqual(raised.exception.code, 2)

    def test_json_report(self) -> None:
        data = MODULE_HEADER + custom(wav.SECTION, version_bytes(0, 8, 0))
        path = Path(tempfile.mkdtemp()) / "extension.wasm"
        path.write_bytes(data)
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            status = wav.main([str(path), "--max", "0.7.0", "--json"])
            plain = io.StringIO()
            with contextlib.redirect_stdout(plain):
                plain_status = wav.main([str(path), "--json"])
        self.assertEqual(status, 1)
        self.assertEqual(
            json.loads(out.getvalue()),
            {"file": str(path), "api_version": "0.8.0", "max": "0.7.0",
             "within_max": False},
        )  # fmt: skip
        self.assertEqual(plain_status, 0)
        self.assertIsNone(json.loads(plain.getvalue())["within_max"])

    def test_missing_section_exits_2(self) -> None:
        status, output = run(MODULE_HEADER + custom("name", b""))
        self.assertEqual(status, 2)
        self.assertIn("no zed:api-version section", output)

    def test_wrong_length_payload_exits_2(self) -> None:
        status, _ = run(MODULE_HEADER + custom(wav.SECTION, b"\x00\x07"))
        self.assertEqual(status, 2)

    def test_non_wasm_exits_2(self) -> None:
        status, output = run(b"not wasm")
        self.assertEqual(status, 2)
        self.assertIn("not a WebAssembly binary", output)


if __name__ == "__main__":
    unittest.main()
