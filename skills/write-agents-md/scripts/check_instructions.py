#!/usr/bin/env python3
"""Check agent instruction files (AGENTS.md, CLAUDE.md) for measurable issues.

Each FILE argument is resolved through its symlinks first (CLAUDE.md,
AGENTS.md, and GEMINI.md are often symlinked to one file); a dangling
symlink is reported as an error, and a real file reached by more than one
FILE argument is checked once, under its own resolved path. For each real
file it reports:
  - size in bytes and lines, counted after stripping block-level HTML
    comments (Claude Code does not send them); warns above Codex's default
    combined limit (project_doc_max_bytes = 32 KiB) and above Claude Code's
    200-line per-file target;
  - relative Markdown links and `@path` imports that do not resolve (imports
    are followed up to Claude Code's four-hop limit; code spans and fences
    are skipped, as Claude Code does);
  - generic phrases that give an agent nothing to act on;
  - the shell commands found in `sh`/`bash`/`console` fences and in
    backticked lines starting with a known tool, so they can be run.

Usage: check_instructions.py FILE [FILE ...] [--commands | --json]
  --commands  print only the extracted commands, one per line
Exit status: 0 no errors, 1 errors (missing links/imports/dangling symlinks),
  2 bad input. Warnings (size, generic phrases) do not change the exit status.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

CODEX_LIMIT_BYTES = 32 * 1024
CLAUDE_LINE_TARGET = 200
MAX_IMPORT_HOPS = 4
LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s#]+)(?:#[^)]*)?\)")
IMPORT = re.compile(r"(?:^|\s)@((?:~|\.{1,2})?/?[\w./-]+)")
CODE_SPAN = re.compile(r"`[^`]*`")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w-]*)")
FENCED_BLOCK = re.compile(r"(^(?:```|~~~)[\s\S]*?^(?:```|~~~)[^\n]*$)", re.M)
BLOCK_COMMENT = re.compile(r"^[ \t]*<!--[\s\S]*?-->[ \t]*(?:\r?\n|$)", re.M)
SHELL_LANGS = {"sh", "bash", "shell", "console", "zsh"}
TOOLS = (
    "bun", "cargo", "dotnet", "go", "gradle", "just", "make", "mvn", "npm",
    "pnpm", "pytest", "python", "python3", "ruff", "uv", "yarn",
)  # fmt: skip
GENERIC = (
    "best practices",
    "clean code",
    "as appropriate",
    "be careful",
    "high quality",
    "use common sense",
    "follow conventions",
    "write good",
)


def scan(text: str) -> tuple[list[str], list[str]]:
    """Return (prose lines outside fences, commands)."""
    prose: list[str] = []
    commands: list[str] = []
    opener = ""
    language = ""
    for line in text.splitlines():
        fence = FENCE.match(line)
        if fence and not opener:
            opener, language = fence.group(1), fence.group(2).lower()
            continue
        if fence and opener and fence.group(1)[0] == opener[0]:
            opener = ""
            continue
        if opener:
            stripped = line.strip()
            if language in SHELL_LANGS and stripped and not stripped.startswith("#"):
                commands.append(stripped.removeprefix("$ ").strip())
            continue
        prose.append(line)
        for span in re.findall(r"`([^`]+)`", line):
            if span.split(" ", 1)[0] in TOOLS:
                commands.append(span)
    return prose, commands


def strip_block_comments(text: str) -> str:
    """Remove block-level HTML comments outside fenced code, as Claude Code
    strips them before sending instructions to the model."""
    parts = FENCED_BLOCK.split(text)
    return "".join(
        part if index % 2 else BLOCK_COMMENT.sub("", part)
        for index, part in enumerate(parts)
    )


def check_file(path: Path, seen: set[Path], depth: int) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    text = path.read_text(encoding="utf-8")
    prose, _ = scan(text)
    if depth == 0:
        size = len(text.encode("utf-8"))
        lines = len(strip_block_comments(text).splitlines())
        if size > CODEX_LIMIT_BYTES:
            warnings.append(f"{path}: {size} bytes exceeds Codex's 32 KiB default")
        if lines > CLAUDE_LINE_TARGET:
            warnings.append(f"{path}: {lines} lines exceeds Claude's 200-line target")
    for line in prose:
        lowered = line.lower()
        for phrase in GENERIC:
            if phrase in lowered:
                warnings.append(f"{path}: generic phrase '{phrase}'")
        for target in LINK.findall(line):
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (path.parent / target).exists():
                errors.append(f"{path}: missing link target {target}")
        for target in IMPORT.findall(CODE_SPAN.sub("", line)):
            resolved = (path.parent / Path(target).expanduser()).resolve()
            if not resolved.exists():
                errors.append(f"{path}: missing @import {target}")
            elif depth + 1 > MAX_IMPORT_HOPS:
                errors.append(f"{path}: @import {target} exceeds four hops")
            elif resolved not in seen:
                seen.add(resolved)
                nested_errors, nested_warnings = check_file(resolved, seen, depth + 1)
                errors += nested_errors
                warnings += nested_warnings
    return errors, warnings


EPILOG = """\
Exit status:
  0  no errors (warnings do not change the status)
  1  a relative link or @import does not resolve
  2  bad input: a FILE does not exist or is not UTF-8

Output: per file, "FILE: N bytes, N lines, N commands", then "WARN" and
"ERROR" lines. --commands prints only the commands. --json prints
{"files": [{file, bytes, lines, commands, warnings, errors}], "errors": N}.

Examples:
  python3 scripts/check_instructions.py AGENTS.md
  python3 scripts/check_instructions.py AGENTS.md CLAUDE.md --json
  python3 scripts/check_instructions.py AGENTS.md --commands | sort -u
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("files", nargs="+", help="AGENTS.md or CLAUDE.md files")
    output = parser.add_mutually_exclusive_group()
    output.add_argument(
        "--commands", action="store_true", help="print only the extracted commands"
    )
    output.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    all_errors: list[str] = []
    reports: list[dict] = []
    seen_reals: set[Path] = set()
    for raw in args.files:
        path = Path(raw)
        if path.is_symlink() and not path.exists():
            message = f"{path}: symlink target does not exist"
            all_errors.append(message)
            if args.json:
                reports.append(
                    {
                        "file": raw,
                        "bytes": 0,
                        "lines": 0,
                        "commands": [],
                        "warnings": [],
                        "errors": [message],
                    }
                )
            elif not args.commands:
                print(f"{path}: dangling symlink")
                print(f"  ERROR {message}")
            continue
        if not path.is_file():
            print(
                f"error: {raw} is not a file; pass instruction files such as AGENTS.md",
                file=sys.stderr,
            )
            return 2
        path = path.resolve()
        if path in seen_reals:
            continue
        seen_reals.add(path)
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            print(f"error: cannot read {raw}: {error}", file=sys.stderr)
            return 2
        _, commands = scan(text)
        if args.commands:
            print("\n".join(dict.fromkeys(commands)))
            continue
        errors, warnings = check_file(path, {path.resolve()}, 0)
        all_errors += errors
        size = len(text.encode("utf-8"))
        if args.json:
            reports.append(
                {
                    "file": str(path),
                    "bytes": size,
                    "lines": len(text.splitlines()),
                    "commands": list(dict.fromkeys(commands)),
                    "warnings": warnings,
                    "errors": errors,
                }
            )
            continue
        print(
            f"{path}: {size} bytes, {len(text.splitlines())} lines, "
            f"{len(set(commands))} commands"
        )
        for warning in warnings:
            print(f"  WARN {warning}")
        for error in errors:
            print(f"  ERROR {error}")
    if args.json:
        print(json.dumps({"files": reports, "errors": len(all_errors)}, indent=2))
    return 1 if all_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
