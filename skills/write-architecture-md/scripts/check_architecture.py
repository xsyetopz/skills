#!/usr/bin/env python3
"""Check an ARCHITECTURE.md against the repository it describes.

The outline follows the architecture.md template
(https://github.com/timajwilliams/architecture). The file's directory is
the repository (or monorepo system) root it describes. Errors:
  - the file is not named ARCHITECTURE.md, or sits in a docs directory
    instead of the root;
  - a template section is missing (project structure, diagram, core
    components, data stores, integrations, deployment, security,
    development, future, project identification, glossary);
  - a section is empty (write "Not evident from the repository." instead);
  - template text or placeholders remain (`[e.g., ...]`, `[Insert ...]`,
    `{placeholder}`, the template's instruction sentences);
  - the diagram section has no fenced diagram (Mermaid or text);
  - a path in a tree block, or a backticked path or file name, does not
    exist under the root;
  - a top-level directory of the root appears neither in a tree block nor as
    `dir/` or `` `dir` `` in the text.
Warnings: relative links to local files (they go stale; name the file in
backticks), `file:line` references, "see FILE.md" instead of the facts, and
no YYYY-MM-DD date in the project identification section.

Usage: check_architecture.py FILE [--json | --commands]
  --commands  print only the commands in sh/bash/shell/console fences
Exit status: 0 no errors, 1 errors, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

SECTIONS = {
    "project structure": r"project structure",
    "high-level system diagram": r"diagram",
    "core components": r"core components",
    "data stores": r"data stores?",
    "external integrations": r"integrations|external (?:apis?|services)",
    "deployment and infrastructure": r"deployment|infrastructure",
    "security": r"security",
    "development and testing": r"development|testing environment",
    "future considerations": r"future|roadmap",
    "project identification": r"project identification",
    "glossary": r"glossary|acronyms",
}
PLACEHOLDERS = [
    re.compile(
        r"\[(?:(?:e\.g\.|insert |service name|data store type)[^\]]*"
        r"|yyyy-mm-dd|project root|acronym|term|full definition"
        r"|explanation)\]",
        re.I,
    ),
    re.compile(
        r"(?:briefly describe|\(repeat for each|list and (?:briefly )?"
        r"describe|list any third-party|highlight any critical"
        r"|briefly note any|define any project-specific"
        r"|living template designed to)",
        re.I,
    ),
]
BRACE_PLACEHOLDER = re.compile(r"\{[A-Za-z][^{}]*\}")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*([\w-]*)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
CODE_SPAN = re.compile(r"`([^`\n]+)`")
LOCAL_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
SEE_FILE = re.compile(
    r"\b(?:see|refer to|described in)\s+(?:the\s+)?`?[\w./-]+\.(?:md|rst|txt)\b",
    re.I,
)
TREE_MARK = re.compile(r"[├└]──")
EXTENSIONS = [
    "c",
    "cfg",
    "cjs",
    "cpp",
    "cs",
    "css",
    "go",
    "h",
    "hpp",
    "html",
    "ini",
    "java",
    "js",
    "json",
    "jsx",
    "kt",
    "lock",
    "md",
    "mjs",
    "php",
    "proto",
    "py",
    "rb",
    "rs",
    "sh",
    "sql",
    "swift",
    "toml",
    "ts",
    "tsx",
    "txt",
    "xml",
    "yaml",
    "yml",
]
LINE_REF = re.compile(r"\b[\w./-]+\.(?:%s):\d+\b" % "|".join(EXTENSIONS))
BARE_FILE = re.compile(
    r"^(?:[\w.-]+\.(?:%s)|Makefile|Dockerfile|justfile|Justfile|Procfile)$"
    % "|".join(EXTENSIONS)
)
PATHLIKE = re.compile(r"^\.?[\w@-][\w.@-]*(?:/[\w.@-]+)*/?$")
DOMAIN = re.compile(r"^[a-z0-9-]+\.[a-z]{2,}$")
SKIP_DIRS = {
    ".git",
    "node_modules",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    "target",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
}
SHELL_LANGS = {"sh", "bash", "shell", "console", "zsh"}
DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


@dataclass
class Finding:
    level: str
    line: int
    message: str


@dataclass
class Block:
    lang: str
    start: int
    lines: list[str]


def split_fences(lines: list[str]) -> tuple[list[Block], set[int]]:
    """Return fenced blocks and the 1-based line numbers inside any fence."""
    blocks: list[Block] = []
    inside: set[int] = set()
    opener = ""
    current: Block | None = None
    for number, line in enumerate(lines, 1):
        match = FENCE.match(line)
        if match and not opener:
            opener = match.group(1)
            current = Block(match.group(2).lower(), number, [])
            inside.add(number)
            continue
        if opener:
            inside.add(number)
            marker = match.group(1) if match else ""
            if (
                marker
                and marker[0] == opener[0]
                and len(marker) >= len(opener)
                and not line.strip()[len(marker) :].strip()
            ):
                opener = ""
                assert current is not None
                blocks.append(current)
                current = None
            elif current is not None:
                current.lines.append(line)
    return blocks, inside


def headings(lines: list[str], inside: set[int]) -> list[tuple[int, int, str]]:
    found = []
    for number, line in enumerate(lines, 1):
        match = HEADING.match(line)
        if match and number not in inside:
            found.append((number, len(match.group(1)), match.group(2)))
    return found


def section_body(
    lines: list[str], heads: list[tuple[int, int, str]], index: int
) -> list[str]:
    """Lines under heading `index` up to the next heading of equal or higher rank."""
    start, level, _ = heads[index]
    end = len(lines) + 1
    for number, other, _ in heads[index + 1 :]:
        if other <= level:
            end = number
            break
    return lines[start : end - 1]


def tree_paths(block: Block) -> list[tuple[int, str]]:
    """Reconstruct relative paths from a `tree`-style block."""
    stack: list[str] = []
    paths = []
    for offset, raw in enumerate(block.lines, 1):
        mark = TREE_MARK.search(raw)
        if not mark:
            continue
        column = mark.end()
        name_part = raw[column:].lstrip()
        column += len(raw[column:]) - len(name_part)
        name = re.split(r"\s{2,}|\s#", name_part.strip(), maxsplit=1)[0].strip()
        level = max(column // 4 - 1, 0)
        stack = stack[:level]
        if not name or "*" in name or "..." in name or "…" in name:
            stack.append(name)
            continue
        stack.append(name.rstrip("/"))
        paths.append((block.start + offset, "/".join(stack)))
    return paths


def file_index(root: Path) -> set[str]:
    names: set[str] = set()
    for path in root.rglob("*"):
        if not any(part in SKIP_DIRS for part in path.relative_to(root).parts):
            names.add(path.name)
    return names


def top_level_dirs(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "-C", str(root), "ls-files"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0 and result.stdout.strip():
        dirs = {
            line.split("/", 1)[0] for line in result.stdout.splitlines() if "/" in line
        }
    else:
        dirs = {p.name for p in root.iterdir() if p.is_dir()}
    return sorted(d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS)


def path_candidate(token: str) -> str | None:
    if (
        " " in token
        or "://" in token
        or token.startswith(("/", "~", "-"))
        or any(c in token for c in "*<>{}$=:")
    ):
        return None
    if "/" in token and PATHLIKE.match(token):
        if DOMAIN.match(token.split("/", 1)[0]):
            return None
        return token
    return token if BARE_FILE.match(token) else None


DOCS_DIRS = {"doc", "docs", "documentation"}


def placement(path: Path) -> list[Finding]:
    """ARCHITECTURE.md lives at the root it describes, next to README."""
    findings = []
    if path.name != "ARCHITECTURE.md":
        findings.append(
            Finding("error", 1, f"name the file ARCHITECTURE.md, not {path.name}")
        )
    if path.resolve().parent.name.lower() in DOCS_DIRS:
        findings.append(
            Finding(
                "error",
                1,
                "move the file to the repository root, next to README; "
                "paths are checked relative to the file's directory",
            )
        )
    return findings


def check(text: str, root: Path) -> list[Finding]:
    lines = text.splitlines()
    blocks, inside = split_fences(lines)
    heads = headings(lines, inside)
    findings: list[Finding] = []

    def add(level: str, line: int, message: str) -> None:
        findings.append(Finding(level, line, message))

    titles = [(n, lvl, t.lower()) for n, lvl, t in heads]
    section_at: dict[str, int] = {}
    for name, pattern in SECTIONS.items():
        hit = next(
            (
                i
                for i, (_, lvl, t) in enumerate(titles)
                if lvl >= 2 and re.search(pattern, t)
            ),
            None,
        )
        if hit is None:
            add("error", 1, f"missing section: {name}")
        else:
            section_at[name] = hit

    for i, (number, _, title) in enumerate(heads):
        if not any(line.strip() for line in section_body(lines, heads, i)):
            add(
                "error",
                number,
                f"section '{title}' is empty; state the "
                "facts or 'Not evident from the repository.'",
            )

    for number, line in enumerate(lines, 1):
        for pattern in PLACEHOLDERS:
            if pattern.search(line):
                add("error", number, f"template text left: {line.strip()[:60]}")
                break
        if number in inside:
            continue
        prose = CODE_SPAN.sub("", line)
        if BRACE_PLACEHOLDER.search(prose):
            add("error", number, f"placeholder left: {line.strip()[:60]}")
        for target in LOCAL_LINK.findall(prose):
            if not re.match(r"^(?:[a-z]+:|#)", target):
                add(
                    "warning",
                    number,
                    f"link to local file '{target}' goes "
                    "stale on moves; name it in backticks instead",
                )
        if SEE_FILE.search(prose):
            add(
                "warning",
                number,
                "points to another file instead of stating "
                "the facts; the document must be self-contained",
            )
        if LINE_REF.search(line):
            add(
                "warning",
                number,
                "file:line reference goes stale; name the file and symbol",
            )

    if "high-level system diagram" in section_at:
        body_start = heads[section_at["high-level system diagram"]][0]
        body_end = body_start + len(
            section_body(lines, heads, section_at["high-level system diagram"])
        )
        if not any(body_start < b.start <= body_end for b in blocks):
            add(
                "error",
                body_start,
                "diagram section has no fenced Mermaid or text diagram",
            )

    if "project identification" in section_at:
        idx = section_at["project identification"]
        if not DATE.search("\n".join(section_body(lines, heads, idx))):
            add("warning", heads[idx][0], "no YYYY-MM-DD date of last update")

    for block in blocks:
        for number, rel in tree_paths(block):
            if not (root / rel).exists():
                add("error", number, f"tree names '{rel}', which does not exist")

    names = file_index(root)
    for number, line in enumerate(lines, 1):
        if number in inside:
            continue
        for token in CODE_SPAN.findall(line):
            candidate = path_candidate(re.sub(r":\d+$", "", token.strip()))
            if candidate is None:
                continue
            exists = (
                (root / candidate).exists() if "/" in candidate else candidate in names
            )
            if not exists:
                add("error", number, f"names `{candidate}`, which does not exist")

    in_trees = {
        rel.split("/", 1)[0] for block in blocks for _, rel in tree_paths(block)
    }
    for directory in top_level_dirs(root):
        named = re.search(
            rf"(?<![\w.-]){re.escape(directory)}/|`{re.escape(directory)}`", text
        )
        if directory not in in_trees and not named:
            add("error", 1, f"top-level directory '{directory}/' is not described")

    return sorted(findings, key=lambda f: (f.line, f.level))


def commands(text: str) -> list[str]:
    blocks, _ = split_fences(text.splitlines())
    found = []
    for block in blocks:
        if block.lang not in SHELL_LANGS:
            continue
        for raw in block.lines:
            line = raw.strip()
            if line.startswith("$ "):
                line = line[2:]
            if line and not line.startswith("#") and line not in found:
                found.append(line)
    return found


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("file", type=Path)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--json", action="store_true")
    mode.add_argument("--commands", action="store_true")
    args = parser.parse_args(argv)
    if not args.file.is_file():
        print(f"error: {args.file} is not a file", file=sys.stderr)
        return 2
    text = args.file.read_text(encoding="utf-8")
    if args.commands:
        print("\n".join(commands(text)))
        return 0
    findings = placement(args.file) + check(text, args.file.resolve().parent)
    errors = sum(f.level == "error" for f in findings)
    if args.json:
        print(
            json.dumps(
                {
                    "file": str(args.file),
                    "errors": errors,
                    "findings": [asdict(f) for f in findings],
                },
                indent=2,
            )
        )
    else:
        for f in findings:
            print(f"{args.file}:{f.line}: {f.level}: {f.message}")
        print(f"{errors} error(s), {len(findings) - errors} warning(s)")
    return int(errors > 0)


if __name__ == "__main__":
    raise SystemExit(main())
