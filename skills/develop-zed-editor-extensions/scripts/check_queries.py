"""Check Zed Tree-sitter query files without compiling the grammar.

Stdlib only. For each `*.scm` in a language directory it checks balanced
delimiters, the capture names that Zed v1.21.0 reads for that file
(crates/language_core/src/grammar.rs), and, with `--node-types`, that
every named node, anonymous token, and field exists in the grammar's
`src/node-types.json` at the pinned revision.

    python3 check_queries.py LANGUAGE_DIR [--node-types FILE] [--json]

Exit status: 0 when no errors, 1 when any error, 2 on bad usage (no .scm
files, or an unreadable --node-types file).
A clean run does not prove that patterns match; run
`tree-sitter query` on sample files for that.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# Theme captures from https://zed.dev/docs/extensions/languages.
HIGHLIGHTS = {
    "attribute", "boolean", "comment", "comment.doc", "constant",
    "constant.builtin", "constructor", "embedded", "emphasis",
    "emphasis.strong", "enum", "function", "hint", "keyword", "label",
    "link_text", "link_uri", "number", "operator", "predictive", "preproc",
    "primary", "property", "punctuation", "punctuation.bracket",
    "punctuation.delimiter", "punctuation.list_marker",
    "punctuation.special", "string", "string.escape", "string.regex",
    "string.special", "string.special.symbol", "tag", "tag.doctype",
    "text.literal", "title", "type", "type.builtin", "variable",
    "variable.special", "variable.parameter", "variant",
}  # fmt: skip
# (required, optional) captures per file; None means any name is used.
RULES: dict[str, tuple[set[str], set[str]] | None] = {
    "brackets.scm": ({"open", "close"}, set()),
    "outline.scm": (
        {"item", "name"},
        {"context", "context.extra", "open", "close", "annotation"},
    ),
    "indents.scm": ({"indent"}, {"start", "end", "outdent"}),
    "injections.scm": (
        set(),
        {
            "language",
            "injection.language",
            "content",
            "injection.content",
            "injection.host",
        },
    ),
    "redactions.scm": ({"redact"}, set()),
    "textobjects.scm": (
        set(),
        {
            f"{kind}.{part}"
            for kind in ("function", "class", "comment")
            for part in ("inside", "around")
        },
    ),
    "debugger.scm": (set(), {"debug-variable", "debug-scope"}),
    "overrides.scm": None,
    "runnables.scm": None,
}
TOKEN_RE = re.compile(
    r'"(?:\\.|[^"\\])*"|;[^\n]*|[()\[\]]|@[\w.\-]+|!?[A-Za-z_][\w.\-]*:?'
    r"|#[\w\-?!]+|\S"
)


@dataclass
class Finding:
    level: str
    path: str
    line: int
    message: str


@dataclass
class Token:
    text: str
    line: int


def tokenize(source: str) -> list[Token]:
    tokens = []
    for match in TOKEN_RE.finditer(source):
        text = match.group()
        if text.startswith(";") or text.isspace():
            continue
        tokens.append(Token(text, source.count("\n", 0, match.start()) + 1))
    return tokens


def load_node_types(path: Path) -> tuple[set[str], set[str], set[str]]:
    named, anonymous, fields = set(), set(), set()
    for entry in json.loads(path.read_text(encoding="utf-8")):
        (named if entry.get("named") else anonymous).add(entry["type"])
        fields.update(entry.get("fields", {}))
        for child in entry.get("subtypes", []):
            (named if child.get("named") else anonymous).add(child["type"])
    return named, anonymous, fields


def check_file(
    path: Path, node_types: tuple[set[str], set[str], set[str]] | None
) -> list[Finding]:
    findings: list[Finding] = []

    def report(level: str, line: int, message: str) -> None:
        findings.append(Finding(level, path.name, line, message))

    tokens = tokenize(path.read_text(encoding="utf-8"))
    stack: list[Token] = []
    pairs = {")": "(", "]": "["}
    captures: dict[str, int] = {}
    in_predicate = 0
    for index, token in enumerate(tokens):
        text = token.text
        if text in "([":
            nxt = tokens[index + 1].text if index + 1 < len(tokens) else ""
            if text == "(" and nxt.startswith("#"):
                in_predicate = len(stack) + 1
            stack.append(token)
            if text == "(" and node_types and not in_predicate:
                _check_node(nxt, token.line, node_types, report)
        elif text in pairs:
            if not stack or stack[-1].text != pairs[text]:
                report("ERROR", token.line, f"unbalanced {text!r}")
                return findings
            stack.pop()
            if in_predicate > len(stack):
                in_predicate = 0
        elif text.startswith("@"):
            captures.setdefault(text[1:], token.line)
        elif text.startswith('"') and node_types and not in_predicate:
            literal = json.loads(text) if "\\u" not in text else text[1:-1]
            if literal not in node_types[1]:
                report("ERROR", token.line, f"no anonymous node {text}")
        elif text.endswith(":") and node_types and not in_predicate:
            field = text[:-1].lstrip("!")
            if field not in node_types[2]:
                report("ERROR", token.line, f"no field `{field}`")
        elif text.startswith("!") and node_types and not in_predicate:
            if text[1:] not in node_types[2]:
                report("ERROR", token.line, f"no field `{text[1:]}`")
    for token in stack:
        report("ERROR", token.line, f"unclosed {token.text!r}")
    _check_captures(path.name, captures, report)
    return findings


def _check_node(name, line, node_types, report) -> None:
    if not re.match(r"^[A-Za-z_][\w]*$", name) or name in {"_", "ERROR", "MISSING"}:
        return
    if name not in node_types[0]:
        report("ERROR", line, f"no named node `{name}` in node-types.json")


def _check_captures(file_name, captures, report) -> None:
    names = {n: line for n, line in captures.items() if not n.startswith("_")}
    if file_name == "highlights.scm":
        for name, line in names.items():
            parts = name.split(".")
            prefixes = {".".join(parts[:i]) for i in range(1, len(parts) + 1)}
            if not prefixes & HIGHLIGHTS:
                report("WARN", line, f"@{name} matches no documented theme key")
        return
    rule = RULES.get(file_name, (set(), set()))
    if rule is None:
        return
    required, optional = rule
    for name in sorted(required - set(names)):
        report("ERROR", 1, f"missing required @{name}; Zed ignores the file")
    for name, line in names.items():
        if name in required or name in optional:
            continue
        if file_name == "indents.scm" and name.startswith("start."):
            continue
        report("WARN", line, f"@{name} is not read from {file_name}")
    if file_name == "injections.scm":
        if not {"content", "injection.content"} & set(names):
            report("ERROR", 1, "needs @injection.content (or @content)")
        for short in ("language", "content"):
            if {short, f"injection.{short}"} <= set(names):
                report("ERROR", 1, f"use @{short} or @injection.{short}, not both")


EPILOG = """\
Exit status:
  0  no errors (warnings alone do not fail)
  1  at least one error
  2  bad usage: LANGUAGE_DIR has no .scm files, or --node-types is missing
     or not node-types.json

Output: one "ERROR|WARN FILE:LINE: message" line per finding, then a
summary line. --json prints a list of {level, path, line, message}.

Examples:
  python3 scripts/check_queries.py languages/mylang
  python3 scripts/check_queries.py languages/mylang \\
    --node-types ../tree-sitter-mylang/src/node-types.json
  python3 scripts/check_queries.py languages/mylang --json | jq length
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n")[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "language_dir", type=Path, help="language directory holding *.scm queries"
    )
    parser.add_argument(
        "--node-types",
        type=Path,
        help="the grammar's src/node-types.json at the pinned revision",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the findings as a JSON list"
    )
    args = parser.parse_args(argv)
    files = sorted(args.language_dir.glob("*.scm"))
    if not files:
        print(
            f"no .scm files in {args.language_dir}; "
            "pass a language directory such as languages/NAME",
            file=sys.stderr,
        )
        return 2
    try:
        node_types = load_node_types(args.node_types) if args.node_types else None
    except (OSError, ValueError, TypeError, KeyError, AttributeError) as error:
        print(
            f"cannot read --node-types {args.node_types}: {error}; "
            "expected the grammar's src/node-types.json",
            file=sys.stderr,
        )
        return 2
    findings = [f for path in files for f in check_file(path, node_types)]
    errors = sum(f.level == "ERROR" for f in findings)
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for f in findings:
            print(f"{f.level} {f.path}:{f.line}: {f.message}")
        checked = "with" if node_types else "without"
        print(
            f"{len(files)} files, {errors} errors, "
            f"{len(findings) - errors} warnings ({checked} node types)"
        )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
