#!/usr/bin/env python3
"""Agent Skills checks that skills-ref and validate_repository.py do not cover.

Division of labour (see the justfile):
  skills-ref              frontmatter, name/description/field rules (official)
  validate_repository.py  body line limit, OpenAI metadata, Markdown link targets
  this script             context budgets, bare file references, orphans, nested
                          references, scripts, layout, auxiliary and junk files

Findings are tagged [spec] (agentskills.io), [anthropic] (Anthropic authoring
guidance) or [policy] (thresholds set via flags). Stdlib only.

Usage: skill_lint.py [--strict] [options] [SKILL_DIR ...]   (default: skills/*/)
Exit codes: 0 clean, 1 findings that fail.
Inline suppression on a script line:  skill-lint: allow-interactive
"""

from __future__ import annotations

import argparse
import ast
import math
import os
import re
import subprocess
import sys
from pathlib import Path

STANDARD_ENTRIES = {"SKILL.md", "scripts", "references", "assets"}
LICENSE_RE = re.compile(r"^(LICEN[CS]E|COPYING)(\.(md|txt))?$", re.I)
CONTEXT_SUFFIXES = {".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".csv", ".xml"}
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
# ${CLAUDE_SKILL_DIR}/scripts/x names a file in this skill; ${CLAUDE_PLUGIN_ROOT}
# paths point outside it and are left unchecked.
BARE_PATH_RE = re.compile(
    r"(?:(?<=\$\{CLAUDE_SKILL_DIR\}/)|(?<![\w/.-]))"
    r"((?:scripts|references|assets)/[\w./-]*)"
)
AUX_DOC_RE = re.compile(
    r"^(README|CHANGELOG|CONTRIBUTING|INSTALL(ATION_GUIDE)?|QUICK_REFERENCE|SETUP|TODO|NOTES)\.md$",
    re.I,
)
JUNK_NAME_RE = re.compile(
    r"^(\.ds_store|thumbs\.db|desktop\.ini|\.env(\..*)?)$|\.(py[co]|log|swp|swo|bak|orig|rej)$",
    re.I,
)
JUNK_DIRS = {"__pycache__", "node_modules", ".venv", "venv"}
# Python prompts are found by parsing (see python_prompts); regexes would match
# the word "input (" in docstrings and messages.
INTERACTIVE_RE = {
    ".sh": re.compile(r"\bread\s+(-\w+\s+)*-[ps]\b|\bselect\s+\w+\s+in\b"),
    ".bash": re.compile(r"\bread\s+(-\w+\s+)*-[ps]\b|\bselect\s+\w+\s+in\b"),
    ".js": re.compile(r"readline\.createInterface|\bprompt\s*\("),
    ".mjs": re.compile(r"readline\.createInterface|\bprompt\s*\("),
    ".ts": re.compile(r"readline\.createInterface|\bprompt\s*\("),
    ".rb": re.compile(r"(?<![\w.])gets\b|STDIN\.gets"),
}
SCRIPT_SUFFIXES = {".py", *INTERACTIVE_RE}
HELP_RE = re.compile(r"--help|\b(argparse|click|typer|yargs|commander|OptionParser)\b")
WHEN_RE = re.compile(
    r"\buse\s+(this|it|when|for|if|after|before|while|to)\b|\bwhen\s+(the|a|you|user)\b",
    re.I,
)
SUPPRESS = "skill-lint: allow-interactive"


def estimate_tokens(text: str) -> int:
    """No universal tokenizer exists; take the larger of ~4 chars/token and ~0.75 words/token."""
    return max(math.ceil(len(text) / 4), math.ceil(len(text.split()) / 0.75))


def split_frontmatter(text: str) -> tuple[str, str]:
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            nl = text.find("\n", end + 1)
            return text[: end + 4], text[nl + 1 :] if nl != -1 else ""
    return "", text


def shipped_files(root: Path) -> list[Path]:
    """Tracked + untracked-not-ignored files, i.e. what a commit would ship."""
    try:
        out = subprocess.run(
            ["git", "ls-files", "-co", "--exclude-standard", "-z", "--", "."],
            cwd=root,
            capture_output=True,
            check=True,
        ).stdout.decode()
        return sorted(
            p
            for p in (root / f for f in out.split("\0") if f)
            if p.exists() or p.is_symlink()
        )
    except (OSError, subprocess.CalledProcessError):
        return sorted(p for p in root.rglob("*") if p.is_file() or p.is_symlink())


def local_refs(markdown: str, first_line: int = 1) -> list[tuple[int, str]]:
    refs = []
    for n, line in enumerate(markdown.splitlines(), first_line):
        for m in LINK_RE.finditer(line):
            t = m.group(1).split("#", 1)[0]
            if t and not re.match(r"^[a-z][a-z0-9+.-]*:", t, re.I):
                refs.append((n, t))
        for m in BARE_PATH_RE.finditer(line):
            refs.append((n, m.group(1).rstrip(".,;:)`'\"")))
    return list(dict.fromkeys(refs))


def is_binary(path: Path) -> bool:
    try:
        return b"\0" in path.read_bytes()[:8192]
    except OSError:
        return False


def is_test(path: Path) -> bool:
    """Tests run under `just tests`; agents do not invoke them."""
    return path.name.startswith("test_") or path.stem.endswith(("_test", ".test"))


def python_prompts(text: str) -> list[int]:
    """Lines that call input(), getpass(), or getpass.getpass()."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []  # validate_assets.py reports unparsable scripts
    lines = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
        if name in ("input", "getpass"):
            lines.append(node.lineno)
    return lines


def python_imports(path: Path) -> set[Path]:
    """Sibling modules a Python script imports; they ship with the script."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError, UnicodeError):
        return set()
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split(".")[0])
    return {p.resolve() for n in names if (p := path.parent / f"{n}.py").is_file()}


class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def err(self, src, msg):
        self.errors.append(f"[{src}] {msg}")

    def warn(self, src, msg):
        self.warnings.append(f"[{src}] {msg}")


def check_budgets(root, files, a, r):
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    _, body = split_frontmatter(text)
    lines = text.count("\n") + (0 if text.endswith("\n") else 1)
    if lines > a.max_lines:
        r.err(
            "spec",
            f"SKILL.md is {lines} lines (max {a.max_lines}); move detail to references/",
        )
    tok = estimate_tokens(body)
    if tok > a.max_body_tokens:
        r.err(
            "spec",
            f"SKILL.md body is ~{tok} tokens (max {a.max_body_tokens}); move detail to references/",
        )
    elif tok > a.max_body_tokens * (1 - a.headroom):
        r.warn(
            "policy",
            f"SKILL.md body is ~{tok} tokens, within {a.headroom:.0%} of {a.max_body_tokens}",
        )

    for f in files:  # references are read into context on demand; spec gives no number
        rel = f.relative_to(root)
        if (
            rel.parts[0] != "references"
            or f.is_symlink()
            or f.suffix.lower() not in CONTEXT_SUFFIXES
            or is_binary(f)
        ):
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        n_tok = estimate_tokens(t)
        if n_tok > a.max_ref_tokens:
            r.err(
                "policy",
                f"{rel} is ~{n_tok} tokens (max {a.max_ref_tokens}); split it by topic",
            )
        n_lines = t.count("\n") + 1
        if f.suffix.lower() == ".md" and n_lines > a.toc_lines:
            # A partial read (e.g. the first 100 lines) must still show the scope.
            head = "\n".join(t.splitlines()[:100]).lower()
            if (
                "contents" not in head
                and len(re.findall(r"^\s*[-*\d.]+\s*\[.+\]\(#", head, re.M)) < 3
            ):
                r.warn(
                    "anthropic",
                    f"{rel} is {n_lines} lines with no table of contents near the top",
                )


def check_references(root, r) -> set[Path]:
    text = (root / "SKILL.md").read_text(encoding="utf-8")
    skill_md = (root / "SKILL.md").resolve()
    _, body = split_frontmatter(text)
    body_line = text[: len(text) - len(body)].count("\n") + 1
    rroot = root.resolve()
    references = rroot / "references"

    def resolve(base, target, loc=None):
        if target.startswith(("/", "~")) or re.match(r"^[A-Za-z]:[\\/]", target):
            if loc:
                r.err(
                    "spec",
                    f"{loc}: absolute path '{target}'; use a path relative to the skill root",
                )
            return None
        p = (base / target).resolve()
        if p != rroot and rroot not in p.parents:
            if loc:
                r.err("spec", f"{loc}: '{target}' points outside the skill directory")
            return None
        if not p.exists():
            if loc:
                r.err("spec", f"{loc}: '{target}' does not exist")
            return None
        return p

    direct = {}
    for n, target in local_refs(body, body_line):
        p = resolve(root, target, f"SKILL.md:{n}")
        if p:
            direct[p] = target
    reachable = set(direct)
    for p in direct:
        if p.suffix != ".md" or not p.is_file():
            continue
        for sn, st in local_refs(p.read_text(encoding="utf-8", errors="replace")):
            # Code paths are relative to the skill root.
            sp = resolve(root, st) or resolve(p.parent, st)
            if not sp:
                continue
            reachable.add(sp)
            # Only reference documents nest; assets are templates and examples.
            if (
                sp.suffix == ".md"
                and references in sp.parents
                and sp != skill_md
                and sp not in direct
            ):
                r.err(
                    "spec",
                    f"{p.relative_to(rroot)}:{sn}: links to '{st}'; keep references one level "
                    "deep (link it from SKILL.md directly)",
                )
    for p in list(reachable):
        if p.suffix == ".py":
            reachable |= python_imports(p)
    return reachable


def is_reachable(path: Path, rroot: Path, reachable: set[Path]) -> bool:
    """Reached directly, inside a referenced directory, or beside a referenced
    file below the top-level folder (an example project's harness reaches its
    own files)."""
    fr = path.resolve()
    if fr in reachable:
        return True
    tops = {rroot / d for d in STANDARD_ENTRIES}
    for d in reachable:
        home = d if d.is_dir() else d.parent
        if home in fr.parents and (d.is_dir() or home not in tops):
            return True
    return False


def check_contents(root, files, reachable, a, r):
    rroot = root.resolve()
    for entry in sorted({f.relative_to(root).parts[0] for f in files}):
        if (
            entry.lower() == "skill.md"
            or entry in STANDARD_ENTRIES
            or LICENSE_RE.match(entry)
            or entry in a.allow
        ):
            continue
        r.warn(
            "policy",
            f"'{entry}' is outside the conventional layout "
            "(SKILL.md, scripts/, references/, assets/, LICENSE); allow with --allow",
        )
    for f in files:
        rel = f.relative_to(root)
        if len(rel.parts) == 1 and AUX_DOC_RE.match(f.name):
            r.err(
                "anthropic",
                f"{rel}: auxiliary docs do not belong in a skill; put human docs in the repo README",
            )
        if JUNK_NAME_RE.search(f.name) or JUNK_DIRS.intersection(rel.parts):
            r.err(
                "policy",
                f"{rel}: build, OS, editor, or env artifact; delete it and ignore it",
            )
        if f.is_symlink():
            tgt = f.resolve()
            if tgt != rroot and rroot not in tgt.parents:
                r.err(
                    "policy",
                    f"{rel}: symlink escapes the skill directory ({os.readlink(f)})",
                )
                continue
        if rel.parts[0] == "references" and is_binary(f):
            r.warn(
                "policy",
                f"{rel}: binary file in references/ (read as text); move to assets/",
            )
        if (
            rel.parts[0] in ("scripts", "references", "assets")
            and not is_test(f)
            and not is_reachable(f, rroot, reachable)
        ):
            r.warn(
                "spec",
                f"{rel}: not referenced from SKILL.md (or a file it references); "
                "the agent will never know it exists",
            )


def check_scripts(root, files, r):
    for f in files:
        rel = f.relative_to(root)
        if (
            rel.parts[0] != "scripts"
            or f.suffix not in SCRIPT_SUFFIXES
            or is_test(f)
            or is_binary(f)
        ):
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        lines = text.splitlines()
        if f.suffix == ".py":
            prompts = python_prompts(text)
        else:
            prompts = [
                n
                for n, line in enumerate(lines, 1)
                if INTERACTIVE_RE[f.suffix].search(line)
            ]
        for n in prompts:
            if SUPPRESS not in lines[n - 1]:
                r.err(
                    "spec",
                    f"{rel}:{n}: interactive input; agents run non-interactively, "
                    "take flags/env/stdin instead",
                )
        # An imported Python module has no command line to document.
        entry_point = f.suffix != ".py" or "__main__" in text
        if entry_point and not HELP_RE.search(text):
            r.warn(
                "spec",
                f"{rel}: no --help; agents learn a script's interface from --help",
            )


def check_description(root, r):
    fm, _ = split_frontmatter((root / "SKILL.md").read_text(encoding="utf-8"))
    m = re.search(r"^description:\s*(.*(?:\n[ \t]+.*)*)", fm, re.M)
    if m and not WHEN_RE.search(m.group(1)):
        r.warn(
            "spec",
            "description should say when to use the skill, not just what it does",
        )


def lint(root: Path, a) -> Report:
    r = Report()
    if not (root / "SKILL.md").is_file():
        return r  # missing or misnamed SKILL.md is reported by skills-ref
    files = shipped_files(root)
    check_budgets(root, files, a, r)
    reachable = check_references(root, r)
    check_contents(root, files, reachable, a, r)
    check_scripts(root, files, r)
    check_description(root, r)
    return r


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument(
        "skills",
        nargs="*",
        type=Path,
        help="skill directories (default: <skills-dir>/*/)",
    )
    ap.add_argument("--skills-dir", type=Path, default=Path("skills"))
    ap.add_argument("--strict", action="store_true", help="treat warnings as errors")
    ap.add_argument("--max-lines", type=int, default=500, help="[spec] SKILL.md lines")
    ap.add_argument(
        "--max-body-tokens", type=int, default=5000, help="[spec] SKILL.md body tokens"
    )
    ap.add_argument(
        "--headroom",
        type=float,
        default=0.10,
        help="warn within this fraction of the body budget",
    )
    ap.add_argument(
        "--max-ref-tokens",
        type=int,
        default=10000,
        help="[policy] tokens per reference file",
    )
    ap.add_argument(
        "--toc-lines",
        type=int,
        default=100,
        help="[anthropic] ref .md length needing a TOC",
    )
    ap.add_argument(
        "--allow",
        action="append",
        default=[],
        help="extra top-level skill entry (repeatable)",
    )
    a = ap.parse_args(argv)

    roots = a.skills or sorted(p.parent for p in a.skills_dir.glob("*/SKILL.md"))
    n_err = n_warn = 0
    for root in roots:
        r = lint(root, a)
        errors, warnings = (
            (r.errors + r.warnings, []) if a.strict else (r.errors, r.warnings)
        )
        for e in errors:
            print(f"{root}: error: {e}")
        for w in warnings:
            print(f"{root}: warning: {w}")
        n_err, n_warn = n_err + len(errors), n_warn + len(warnings)
    print(
        f"{len(roots)} skill(s) checked: {n_err} error(s), {n_warn} warning(s)",
        file=sys.stderr,
    )
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
