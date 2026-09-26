#!/usr/bin/env python3
"""Run the shell commands a Markdown file documents and check their output.

Blocks checked:
  ```sh / ```bash / ```shell   each non-comment line is one command; if
                               the next fenced block is ```text and the
                               prose between them says "Expected", its
                               content is the expected stdout
  ```console                   lines starting with "$ " are commands; the
                               lines after each, up to the next "$ ", are
                               its expected stdout

Commands run with `sh -c` in a temporary copy of the directory given by
--cwd (default: the Markdown file's directory), so documented commands
cannot change the real checkout. A block marked with the HTML comment
<!-- doc-check: skip --> on the line before its fence is listed, not run.

Usage: check_doc_commands.py FILE.md [--cwd DIR] [--list] [--timeout S] [--json]
Exit status: 0 every command passed, 1 a command failed or its output
differed, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

FENCE = re.compile(r"^(```+|~~~+)\s*([\w-]*)")
SHELLS = {"sh", "bash", "shell"}
EPILOG = """\
Exit status:
  0  every command passed (or was skipped or only listed)
  1  a command failed, timed out, or printed other output than documented
  2  unreadable input: FILE cannot be read or --cwd is not a directory

Output: one line per command, "ok", "FAIL" (with the reason on the next
line), "skip", or "list", then "P/N documented commands passed". --json
prints {"checks": [{file, line, command, status, output_checked,
problem}], "passed": P, "total": N}.

Examples:
  python3 scripts/check_doc_commands.py README.md
  python3 scripts/check_doc_commands.py docs/usage.md --cwd . --timeout 30
  python3 scripts/check_doc_commands.py README.md --list
  python3 scripts/check_doc_commands.py README.md --json \\
    | jq '.checks[] | select(.status == "fail")'
"""


@dataclass
class Check:
    line: int
    command: str
    expected: str | None
    skip: bool


def blocks(text: str) -> list[tuple[int, str, list[str], str, bool]]:
    """Return (line, info, body lines, prose before, skip) per fenced block."""
    lines = text.splitlines()
    found = []
    prose: list[str] = []
    i = 0
    while i < len(lines):
        match = FENCE.match(lines[i])
        if not match:
            prose.append(lines[i])
            i += 1
            continue
        fence, info = match.group(1), match.group(2).lower()
        skip = i > 0 and "doc-check: skip" in lines[i - 1]
        body = []
        j = i + 1
        while j < len(lines) and not lines[j].startswith(fence):
            body.append(lines[j])
            j += 1
        found.append((i + 1, info, body, "\n".join(prose), skip))
        prose = []
        i = j + 1
    return found


def checks(text: str) -> list[Check]:
    result: list[Check] = []
    parsed = blocks(text)
    for index, (line, info, body, _, skip) in enumerate(parsed):
        if info in SHELLS:
            commands = [b for b in body if b.strip() and not b.lstrip().startswith("#")]
            expected = None
            if index + 1 < len(parsed):
                _, next_info, next_body, between, _ = parsed[index + 1]
                if next_info == "text" and "expected" in between.lower():
                    expected = "\n".join(next_body)
            for n, command in enumerate(commands):
                last = n == len(commands) - 1
                result.append(Check(line, command, expected if last else None, skip))
        elif info == "console":
            command, output = None, []
            for body_line in [*body, "$ "]:
                if body_line.startswith("$ "):
                    if command:
                        result.append(Check(line, command, "\n".join(output), skip))
                    command, output = body_line[2:].strip(), []
                else:
                    output.append(body_line)
    return result


def run(check: Check, cwd: Path, timeout: float) -> str | None:
    """Return None on success, otherwise a failure description."""
    try:
        result = subprocess.run(
            ["sh", "-c", check.command],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"timed out after {timeout:g}s"
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()[-3:]
        return f"exit {result.returncode}: " + " | ".join(detail)
    if check.expected is not None and result.stdout.rstrip("\n") != check.expected:
        return f"output differs:\n  expected {check.expected!r}\n  actual   {result.stdout.rstrip()!r}"
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", type=Path, help="Markdown file to check")
    parser.add_argument(
        "--cwd",
        type=Path,
        help="directory to copy and run in (default: FILE's directory)",
    )
    parser.add_argument(
        "--list", action="store_true", help="list the commands without running them"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=60.0,
        help="seconds each command may run (default: 60)",
    )
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        found = checks(args.file.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        print(
            f"error: cannot read {args.file}: {error}; expected a UTF-8 Markdown file",
            file=sys.stderr,
        )
        return 2
    source = (args.cwd or args.file.parent).resolve()
    if not args.list and not source.is_dir():
        print(
            f"error: --cwd {source} is not a directory; pass the directory the "
            "documented commands run in",
            file=sys.stderr,
        )
        return 2
    results: list[dict] = []
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp) / "work"
        if not args.list:
            shutil.copytree(source, work, ignore=shutil.ignore_patterns(".git"))
        for check in found:
            status, problem = "skip" if check.skip else "list", None
            if not (args.list or check.skip):
                problem = run(check, work, args.timeout)
                status = "ok" if problem is None else "fail"
            result = {
                "file": str(args.file),
                "line": check.line,
                "command": check.command,
                "status": status,
                "output_checked": check.expected is not None,
                "problem": problem,
            }
            results.append(result)
            if not args.json:
                print(describe(result))
    passed = sum(result["status"] != "fail" for result in results)
    if args.json:
        report = {"checks": results, "passed": passed, "total": len(found)}
        print(json.dumps(report, indent=2))
    else:
        print(f"{passed}/{len(found)} documented commands passed")
    return 0 if passed == len(found) else 1


def describe(result: dict) -> str:
    where = f"{result['file']}:{result['line']}: {result['command']}"
    if result["status"] == "fail":
        return f"FAIL {where}\n  {result['problem']}"
    if result["status"] == "ok":
        shown = " (output matches)" if result["output_checked"] else ""
        return f"ok   {where}{shown}"
    return f"{result['status']} {where}"


if __name__ == "__main__":
    raise SystemExit(main())
