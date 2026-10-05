"""Count the code lines of one source file, without blank or comment lines.

A line counts when it holds any character outside a comment; lines inside a
multi-line string count. Python docstrings count as comments. Python is
tokenized exactly; other languages use a small lexer that knows each
language's comment markers and string delimiters, not its grammar, so its
counts are close, not exact. Imported by file_length.py.
"""

from __future__ import annotations

import ast
import io
import tokenize
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Str:
    open: str
    close: str
    multiline: bool = False
    escapes: bool = True
    max_len: int | None = None  # char literal: a string only if closed this soon


@dataclass(frozen=True)
class Syntax:
    line: tuple[str, ...] = ()
    block: tuple[tuple[str, str], ...] = ()
    strings: tuple[Str, ...] = ()
    nested: bool = False


DQ, SQ = Str('"', '"'), Str("'", "'")
C_BLOCK = (("/*", "*/"),)
C_LIKE = Syntax(("//",), C_BLOCK, (DQ, SQ))
JS = Syntax(("//",), C_BLOCK, (DQ, SQ, Str("`", "`", multiline=True)))
GO = Syntax(("//",), C_BLOCK, (DQ, SQ, Str("`", "`", True, escapes=False)))
RUST = Syntax(
    ("//",), C_BLOCK, (Str('"', '"', multiline=True), Str("'", "'", max_len=10)), True
)
TRIPLE = Str('"""', '"""', multiline=True)
TEXT_BLOCKS = Syntax(("//",), C_BLOCK, (TRIPLE, DQ, SQ))
NESTING_JVM = Syntax(("//",), C_BLOCK, (TRIPLE, DQ, SQ), nested=True)
HASH = Syntax(("#",), (), (DQ, SQ))
LUA = Syntax(("--",), (("--[[", "]]"),), (DQ, SQ, Str("[[", "]]", True, escapes=False)))
LANGUAGES: tuple[tuple[tuple[str, ...], Syntax], ...] = (
    ((".c", ".h", ".cc", ".cpp", ".cxx", ".hh", ".hpp", ".hxx", ".mm"), C_LIKE),
    ((".dart", ".zig"), C_LIKE),
    ((".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx", ".mts", ".cts"), JS),
    ((".go",), GO),
    ((".rs",), RUST),
    ((".swift",), Syntax(("//",), C_BLOCK, (TRIPLE, DQ), nested=True)),
    ((".java", ".cs", ".groovy"), TEXT_BLOCKS),
    ((".kt", ".kts", ".scala", ".sc"), NESTING_JVM),
    ((".php",), Syntax(("//", "#"), C_BLOCK, (DQ, SQ))),
    ((".sh", ".bash", ".zsh", ".fish", ".rb", ".pl", ".pm", ".r", ".cmake"), HASH),
    ((".ex", ".exs"), Syntax(("#",), (), (TRIPLE, DQ))),
    ((".ps1",), Syntax(("#",), (("<#", "#>"),), (DQ, SQ))),
    ((".jl",), Syntax(("#",), (("#=", "=#"),), (TRIPLE, DQ), nested=True)),
    ((".nim",), Syntax(("#",), (("#[", "]#"),), (TRIPLE, DQ), nested=True)),
    # Python is tokenized; this entry is the fallback for files that do not parse.
    ((".py",), Syntax(("#",), (), (TRIPLE, Str("'''", "'''", True), DQ, SQ))),
    ((".lua",), LUA),
    ((".sql",), Syntax(("--",), C_BLOCK, (SQ, DQ))),
    ((".hs",), Syntax(("--",), (("{-", "-}"),), (DQ,), nested=True)),
    ((".clj", ".cljs", ".cljc", ".el"), Syntax((";",), (), (DQ,))),
    ((".lisp", ".scm", ".rkt"), Syntax((";",), (("#|", "|#"),), (DQ,), True)),
    ((".erl", ".hrl"), Syntax(("%",), (), (DQ,))),
    ((".ml", ".mli"), Syntax((), (("(*", "*)"),), (DQ,), nested=True)),
    ((".fs", ".fsi", ".fsx"), Syntax(("//",), (("(*", "*)"),), (TRIPLE, DQ))),
    ((".vb",), Syntax(("'",), (), (DQ,))),
)
SYNTAX_BY_SUFFIX = {suffix: syntax for group, syntax in LANGUAGES for suffix in group}


def lexed_code_lines(text: str, syntax: Syntax) -> set[int]:
    lines: set[int] = set()
    blocks = sorted(syntax.block, key=lambda pair: -len(pair[0]))
    strings = sorted(syntax.strings, key=lambda s: -len(s.open))
    line, i, n = 1, 0, len(text)
    depth, block, string = 0, ("", ""), None
    while i < n:
        ch = text[i]
        if ch == "\n":
            if string is not None and not string.multiline:
                string = None  # unterminated single-line string ends here
            line += 1
            i += 1
        elif depth:
            if syntax.nested and text.startswith(block[0], i):
                depth, i = depth + 1, i + len(block[0])
            elif text.startswith(block[1], i):
                depth, i = depth - 1, i + len(block[1])
            else:
                i += 1
        elif string is not None:
            if not ch.isspace():
                lines.add(line)
            if string.escapes and ch == "\\" and text[i + 1 : i + 2] != "\n":
                i += 2
            elif text.startswith(string.close, i):
                string, i = None, i + len(string.close)
            else:
                i += 1
        elif ch.isspace():
            i += 1
        elif opened := next((b for b in blocks if text.startswith(b[0], i)), None):
            depth, block, i = 1, opened, i + len(opened[0])
        elif any(text.startswith(marker, i) for marker in syntax.line):
            end = text.find("\n", i)
            i = n if end < 0 else end
        else:
            lines.add(line)
            found = next((s for s in strings if text.startswith(s.open, i)), None)
            if found is None:
                i += 1
            elif found.max_len is None:
                string, i = found, i + len(found.open)
            else:
                i = skip_char_literal(text, i, found)
    return lines


def skip_char_literal(text: str, i: int, quote: Str) -> int:
    start = i + len(quote.open)
    search_from = start + 2 if text[start : start + 1] == "\\" else start + 1
    end = text.find(quote.close, search_from, start + (quote.max_len or 0))
    if end < 0 or "\n" in text[start:end]:
        return i + 1  # a lifetime or label, not a character literal
    return end + len(quote.close)


def docstring_lines(tree: ast.AST, source_lines: list[str]) -> set[int]:
    owners = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    lines: set[int] = set()
    for node in ast.walk(tree):
        if not isinstance(node, owners) or not node.body:
            continue
        first = node.body[0]
        if not (
            isinstance(first, ast.Expr)
            and isinstance(first.value, ast.Constant)
            and isinstance(first.value.value, str)
        ):
            continue
        end_line = first.end_lineno or first.lineno
        before = source_lines[first.lineno - 1][: first.col_offset]
        after = source_lines[end_line - 1][first.end_col_offset or 0 :].strip()
        if not before.strip() and (not after or after.startswith("#")):
            lines.update(range(first.lineno, end_line + 1))
    return lines


NON_CODE_TOKENS = {
    tokenize.COMMENT,
    tokenize.NL,
    tokenize.NEWLINE,
    tokenize.INDENT,
    tokenize.DEDENT,
    tokenize.ENDMARKER,
}


def python_code_lines(text: str) -> set[int]:
    try:
        tree = ast.parse(text)
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (SyntaxError, tokenize.TokenError, ValueError):
        return lexed_code_lines(text, SYNTAX_BY_SUFFIX[".py"])
    lines: set[int] = set()
    for token in tokens:
        if token.type not in NON_CODE_TOKENS:
            lines.update(range(token.start[0], token.end[0] + 1))
    return lines - docstring_lines(tree, text.splitlines())


def count_code_lines(path: Path) -> int | None:
    """Return the code-line count, or None for an unknown or binary file."""
    suffix = path.suffix.lower()
    if suffix not in SYNTAX_BY_SUFFIX:
        return None
    data = path.read_bytes()
    if b"\0" in data[:8192]:
        return None
    text = data.decode("utf-8", errors="replace")
    if suffix == ".py":
        return len(python_code_lines(text))
    return len(lexed_code_lines(text, SYNTAX_BY_SUFFIX[suffix]))
