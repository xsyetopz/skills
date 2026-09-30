"""Acceptance-record checks for check_match_evidence.py.

Recomputes recorded hashes, checks the comparison settings, recomputes
coverage from the function list, and checks negative controls and ABI
checks. Every problem is appended to the report as a defect string.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SHA256 = re.compile(r"^[0-9a-f]{64}$")
ADDRESS = re.compile(r"^0x[0-9a-fA-F]+$")
ORIGINS = {
    "reconstructed",
    "included-asm",
    "emitted-bytes",
    "copied-bytes",
    "dependency",
}
STATUSES = {"matched", "nonmatching"}
SCOPES = {"full-function", "full-image"}
RESULTS = {"match", "nonmatching", "build-failed"}


@dataclass
class Report:
    defects: list[str] = field(default_factory=list)
    matched_bytes: int | None = None
    total_bytes: int | None = None
    attempts: int | None = None


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_tracked(root: Path, relative: str) -> bool:
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--error-unmatch", "--", relative],
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return done.returncode == 0


def check_hashed(entry: Any, label: str, root: Path, defects: list[str]) -> None:
    if not isinstance(entry, dict):
        defects.append(f"{label}: expected an object with path and sha256")
        return
    path, recorded = entry.get("path"), entry.get("sha256")
    if not isinstance(path, str) or not path:
        defects.append(f"{label}: missing path")
        return
    if not isinstance(recorded, str) or not SHA256.fullmatch(recorded):
        defects.append(f"{label} {path}: sha256 must be 64 lowercase hex digits")
        return
    target = root / path
    if not target.is_file():
        defects.append(f"{label} {path}: file not found under {root}")
        return
    actual = sha256_of(target)
    if actual != recorded:
        defects.append(
            f"{label} {path}: stale hash, recorded {recorded[:12]}, now "
            f"{actual[:12]}; rebuild, re-verify, then record the fresh hash"
        )


def check_inputs(data: dict[str, Any], root: Path, defects: list[str]) -> None:
    reference = data.get("reference")
    check_hashed(reference, "reference", root, defects)
    if (
        isinstance(reference, dict)
        and isinstance(reference.get("path"), str)
        and is_tracked(root, reference["path"])
    ):
        defects.append(
            f"reference {reference['path']}: tracked by Git; keep the "
            "reference binary in an ignored directory"
        )
    toolchain = data.get("toolchain")
    if not isinstance(toolchain, list) or not toolchain:
        defects.append("toolchain: expected a non-empty list")
        toolchain = []
    roles = set()
    for index, tool in enumerate(toolchain):
        label = f"toolchain[{index}]"
        check_hashed(tool, label, root, defects)
        if not isinstance(tool, dict):
            continue
        roles.add(tool.get("role"))
        if not isinstance(tool.get("version"), str) or not tool["version"]:
            defects.append(f"{label}: missing version string")
        flags = tool.get("flags")
        if not isinstance(flags, list) or not all(isinstance(f, str) for f in flags):
            defects.append(f"{label}: flags must be a list of strings")
    if toolchain and "compiler" not in roles:
        defects.append("toolchain: no entry has role 'compiler'")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        defects.append("sources: expected a non-empty list")
        sources = []
    for index, source in enumerate(sources):
        check_hashed(source, f"sources[{index}]", root, defects)
    build = data.get("build")
    if not isinstance(build, dict) or not isinstance(build.get("command"), str):
        defects.append("build: expected an object with command and output")
    else:
        check_hashed(build.get("output"), "build.output", root, defects)


def check_compare(data: dict[str, Any], root: Path, defects: list[str]) -> None:
    compare = data.get("compare")
    if not isinstance(compare, dict):
        defects.append("compare: expected an object")
        return
    if compare.get("scope") not in SCOPES:
        defects.append(
            f"compare.scope: {compare.get('scope')!r} is not one of "
            f"{sorted(SCOPES)}; a partial or truncated compare proves nothing"
        )
    if compare.get("masks") != []:
        defects.append(
            "compare.masks: must be an empty list; masked addresses, calls, "
            "branches, or immediates hide mismatches"
        )
    if compare.get("unresolved_relocations") != 0:
        defects.append(
            "compare.unresolved_relocations: must be 0; every relocation "
            "resolves through the reviewed symbol manifest"
        )
    check_hashed(
        compare.get("symbol_manifest"), "compare.symbol_manifest", root, defects
    )


def check_functions(data: dict[str, Any], report: Report) -> dict[str, str]:
    defects = report.defects
    functions = data.get("functions")
    if not isinstance(functions, list) or not functions:
        defects.append("functions: expected a non-empty list")
        return {}
    statuses: dict[str, str] = {}
    matched = total = 0
    for index, function in enumerate(functions):
        label = f"functions[{index}]"
        if not isinstance(function, dict):
            defects.append(f"{label}: expected an object")
            continue
        symbol = function.get("symbol")
        if not isinstance(symbol, str) or not symbol:
            defects.append(f"{label}: missing symbol")
            continue
        label = f"function {symbol}"
        if symbol in statuses:
            defects.append(f"{label}: listed twice")
        size, origin = function.get("size"), function.get("origin")
        status = function.get("status")
        if not isinstance(function.get("address"), str) or not ADDRESS.fullmatch(
            function["address"]
        ):
            defects.append(f"{label}: address must be a hex string such as 0x401000")
        if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
            defects.append(f"{label}: size must be a positive integer")
            size = 0
        if origin not in ORIGINS:
            defects.append(
                f"{label}: origin {origin!r} is not one of {sorted(ORIGINS)}"
            )
        if status not in STATUSES:
            defects.append(
                f"{label}: status {status!r} is not one of {sorted(STATUSES)}"
            )
        if origin in ORIGINS and origin != "reconstructed" and status == "matched":
            defects.append(
                f"{label}: origin {origin} cannot be 'matched'; only "
                "reconstructed source counts as matched"
            )
        total += size
        if origin == "reconstructed" and status == "matched":
            matched += size
        statuses[symbol] = str(status)
    report.matched_bytes, report.total_bytes = matched, total
    coverage = data.get("coverage")
    if not isinstance(coverage, dict):
        defects.append(
            "coverage: expected an object with matched_bytes and total_bytes"
        )
    else:
        for key, value in (("matched_bytes", matched), ("total_bytes", total)):
            if coverage.get(key) != value:
                defects.append(
                    f"coverage.{key}: claims {coverage.get(key)!r}, but the "
                    f"function list gives {value}"
                )
    return statuses


def check_controls(data: dict[str, Any], defects: list[str]) -> None:
    controls = data.get("negative_controls")
    if not isinstance(controls, list) or not controls:
        defects.append(
            "negative_controls: expected at least one known-wrong variant "
            "that the verifier rejected"
        )
        controls = []
    for index, control in enumerate(controls):
        label = f"negative_controls[{index}]"
        if not isinstance(control, dict) or not isinstance(control.get("variant"), str):
            defects.append(
                f"{label}: expected an object with variant and verifier_exit"
            )
            continue
        code = control.get("verifier_exit")
        if not isinstance(code, int) or isinstance(code, bool):
            defects.append(f"{label}: verifier_exit must be an integer")
        elif code == 0:
            defects.append(
                f"{label} ({control['variant']}): the verifier accepted a "
                "known-wrong build, so it cannot detect this fault"
            )
    checks = data.get("abi_checks")
    if not isinstance(checks, list) or not checks:
        defects.append("abi_checks: expected at least one boundary check")
        checks = []
    for index, check in enumerate(checks):
        label = f"abi_checks[{index}]"
        if not isinstance(check, dict) or not isinstance(check.get("boundary"), str):
            defects.append(f"{label}: expected an object with boundary and result")
        elif check.get("result") != "pass":
            defects.append(
                f"{label} ({check['boundary']}): result {check.get('result')!r}, "
                "expected 'pass'"
            )


def check_acceptance(
    data: dict[str, Any], root: Path, report: Report
) -> dict[str, str]:
    if data.get("schema_version") != 1:
        report.defects.append("acceptance: schema_version must be 1")
    check_inputs(data, root, report.defects)
    check_compare(data, root, report.defects)
    statuses = check_functions(data, report)
    check_controls(data, report.defects)
    return statuses
