"""Tests for check_match_evidence.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_match_evidence as cme

FILES = {
    "orig/GAME.EXE": b"MZ reference image",
    "tools/cc.exe": b"compiler",
    "tools/link.exe": b"linker",
    "src/player.c": b"int Player_Update(void) { return 0; }\n",
    "build/GAME.EXE": b"MZ reference image",
    "symbols.txt": b"0x401000 Player_Update\n",
}
HASH_A = "a" * 64
HASH_B = "b" * 64


def digest(name: str) -> str:
    return hashlib.sha256(FILES[name]).hexdigest()


def acceptance() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "reference": {"path": "orig/GAME.EXE", "sha256": digest("orig/GAME.EXE")},
        "toolchain": [
            {
                "role": "compiler",
                "path": "tools/cc.exe",
                "sha256": digest("tools/cc.exe"),
                "version": "cc 6.0",
                "flags": ["/O2"],
            },
            {
                "role": "linker",
                "path": "tools/link.exe",
                "sha256": digest("tools/link.exe"),
                "version": "link 6.0",
                "flags": [],
            },
        ],
        "sources": [{"path": "src/player.c", "sha256": digest("src/player.c")}],
        "build": {
            "command": "just build",
            "output": {"path": "build/GAME.EXE", "sha256": digest("build/GAME.EXE")},
        },
        "compare": {
            "scope": "full-function",
            "masks": [],
            "unresolved_relocations": 0,
            "symbol_manifest": {"path": "symbols.txt", "sha256": digest("symbols.txt")},
        },
        "functions": [
            {
                "symbol": "Player_Update",
                "address": "0x401000",
                "size": 64,
                "origin": "reconstructed",
                "status": "matched",
            },
            {
                "symbol": "Crt_Start",
                "address": "0x401040",
                "size": 32,
                "origin": "included-asm",
                "status": "nonmatching",
            },
        ],
        "coverage": {"matched_bytes": 64, "total_bytes": 96},
        "negative_controls": [{"variant": "swap two stores", "verifier_exit": 1}],
        "abi_checks": [
            {"boundary": "Player_Update", "convention": "cdecl", "result": "pass"}
        ],
    }


def iterations() -> dict[str, Any]:
    attempt = {
        "function": "Player_Update",
        "source_sha256": HASH_A,
        "toolchain_sha256": HASH_B,
        "change": "first translation",
        "diff_summary": "two registers swapped",
    }
    return {
        "schema_version": 1,
        "attempts": [
            {**attempt, "id": 1, "result": "nonmatching", "differing_bytes": 4},
            {**attempt, "id": 2, "result": "build-failed", "differing_bytes": None},
            {**attempt, "id": 3, "result": "match", "differing_bytes": 0},
        ],
    }


class Case(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        for name, content in FILES.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)

    def defects(
        self,
        accepted: dict[str, Any] | None,
        attempts: dict[str, Any] | None = None,
    ) -> str:
        return "\n".join(cme.check(accepted, attempts, self.root).defects)


class AcceptanceTests(Case):
    def test_clean_record(self) -> None:
        report = cme.check(acceptance(), iterations(), self.root)
        self.assertEqual(report.defects, [])
        self.assertEqual((report.matched_bytes, report.total_bytes), (64, 96))
        self.assertEqual(report.attempts, 3)

    def test_edited_source_is_a_stale_hash(self) -> None:
        (self.root / "src/player.c").write_bytes(b"int Player_Update(void);\n")
        self.assertIn("sources[0] src/player.c: stale hash", self.defects(acceptance()))

    def test_missing_file_fails_closed(self) -> None:
        (self.root / "symbols.txt").unlink()
        self.assertIn("symbols.txt: file not found", self.defects(acceptance()))

    def test_toolchain_without_flags_or_compiler(self) -> None:
        data = acceptance()
        del data["toolchain"][0]["flags"]
        data["toolchain"][0]["role"] = "assembler"
        defects = self.defects(data)
        self.assertIn("toolchain[0]: flags must be a list", defects)
        self.assertIn("no entry has role 'compiler'", defects)

    def test_masks_truncation_and_relocations(self) -> None:
        data = acceptance()
        data["compare"].update(
            scope="shorter-body", masks=["call targets"], unresolved_relocations=2
        )
        defects = self.defects(data)
        self.assertIn("compare.scope", defects)
        self.assertIn("compare.masks", defects)
        self.assertIn("compare.unresolved_relocations", defects)

    def test_included_asm_cannot_count_as_matched(self) -> None:
        data = acceptance()
        data["functions"][1]["status"] = "matched"
        data["coverage"]["matched_bytes"] = 96
        defects = self.defects(data)
        self.assertIn("origin included-asm cannot be 'matched'", defects)
        self.assertIn("coverage.matched_bytes: claims 96", defects)

    def test_negative_control_that_passed(self) -> None:
        data = acceptance()
        data["negative_controls"][0]["verifier_exit"] = 0
        self.assertIn("accepted a known-wrong build", self.defects(data))

    def test_missing_controls_and_abi_checks(self) -> None:
        data = acceptance()
        data["negative_controls"] = []
        data["abi_checks"] = []
        defects = self.defects(data)
        self.assertIn("negative_controls: expected at least one", defects)
        self.assertIn("abi_checks: expected at least one", defects)

    def test_bad_function_fields(self) -> None:
        data = acceptance()
        data["functions"][0].update(address="401000", size=0, origin="guessed")
        data["functions"].append(copy.deepcopy(data["functions"][1]))
        defects = self.defects(data)
        self.assertIn("address must be a hex string", defects)
        self.assertIn("size must be a positive integer", defects)
        self.assertIn("origin 'guessed'", defects)
        self.assertIn("function Crt_Start: listed twice", defects)

    @unittest.skipUnless(shutil.which("git"), "git unavailable")
    def test_tracked_reference_binary(self) -> None:
        for command in (["init", "-q"], ["add", "orig/GAME.EXE"]):
            subprocess.run(["git", "-C", str(self.root), *command], check=True)
        self.assertIn("tracked by Git", self.defects(acceptance()))


class IterationTests(Case):
    def test_result_and_differing_bytes_disagree(self) -> None:
        data = iterations()
        data["attempts"][0]["differing_bytes"] = 0
        data["attempts"][2]["differing_bytes"] = 3
        defects = self.defects(None, data)
        self.assertIn(
            "attempts[0]: result 'nonmatching' needs differing_bytes > 0", defects
        )
        self.assertIn("attempts[2]: result 'match' needs differing_bytes 0", defects)

    def test_ids_hashes_and_fields(self) -> None:
        data = iterations()
        data["attempts"][1].update(id=1, source_sha256="abc", change="")
        data["attempts"][2]["result"] = "close"
        defects = self.defects(None, data)
        self.assertIn("attempts[1]: id must be an integer greater than 1", defects)
        self.assertIn("attempts[1]: source_sha256 must be 64", defects)
        self.assertIn("attempts[1]: missing change", defects)
        self.assertIn("attempts[2]: result 'close'", defects)

    def test_accepted_function_needs_matching_latest_attempt(self) -> None:
        data = iterations()
        data["attempts"].append(
            {**data["attempts"][0], "id": 4, "change": "reordered stores"}
        )
        self.assertIn(
            "latest attempt is 'nonmatching'", self.defects(acceptance(), data)
        )
        data["attempts"] = [
            {**attempt, "function": "Other"} for attempt in data["attempts"]
        ]
        self.assertIn(
            "with no attempt in iterations.json", self.defects(acceptance(), data)
        )


class CommandLineTests(Case):
    def run_main(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cme.main(list(args))
        return code, out.getvalue(), err.getvalue()

    def write(self, name: str, data: object) -> str:
        path = self.root / name
        path.write_text(json.dumps(data), encoding="utf-8")
        return str(path)

    def test_clean_exit_and_json(self) -> None:
        accepted = self.write("acceptance.json", acceptance())
        attempts = self.write("iterations.json", iterations())
        code, out, _ = self.run_main("--acceptance", accepted, "--iterations", attempts)
        self.assertEqual(code, 0)
        self.assertIn("defects=0 matched_bytes=64 total_bytes=96 attempts=3", out)
        code, out, _ = self.run_main("--acceptance", accepted, "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["matched_bytes"], 64)

    def test_defects_exit_one(self) -> None:
        data = acceptance()
        data["compare"]["masks"] = ["immediates"]
        code, out, _ = self.run_main("--acceptance", self.write("a.json", data))
        self.assertEqual(code, 1)
        self.assertIn("DEFECT compare.masks", out)

    def test_bad_input_exits_two(self) -> None:
        code, _, err = self.run_main()
        self.assertEqual(code, 2)
        self.assertIn("give --acceptance FILE", err)
        (self.root / "broken.json").write_text("{", encoding="utf-8")
        code, _, err = self.run_main("--iterations", str(self.root / "broken.json"))
        self.assertEqual(code, 2)
        self.assertIn("cannot read", err)
        code, _, err = self.run_main("--iterations", self.write("list.json", []))
        self.assertEqual(code, 2)
        self.assertIn("top level must be a JSON object", err)

    def test_help_runs_as_a_script(self) -> None:
        script = Path(__file__).with_name("check_match_evidence.py")
        done = subprocess.run(
            [sys.executable, str(script), "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(done.returncode, 0)
        self.assertIn("Exit status:", done.stdout)


if __name__ == "__main__":
    unittest.main()
