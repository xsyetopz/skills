#!/usr/bin/env python3
"""Check a skill directory's reference structure.

Checks, for one skill directory:
  1. every Markdown file under references/ is linked directly from SKILL.md
     (one level deep, so agents read whole files instead of previews);
  2. every reference longer than 100 lines has a "## Contents" section;
  3. every relative Markdown link in SKILL.md and references/ resolves to a
     file, and every "#anchor" resolves to a heading in the target file
     (GitHub-style slugs);
  4. SKILL.md has YAML frontmatter with `name` equal to the directory name
     and a non-empty `description` of at most 1024 characters.

Complements `skills-ref validate` (frontmatter schema); it does not judge
content quality.

Usage: check_reference_structure.py [--json] SKILL_DIR [SKILL_DIR ...]
Exit status: 0 no problems, 1 problems found, 2 bad input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

INLINE_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)\s]+)\)")
DEFINITION = re.compile(r"^\[[^\]]+\]:\s*(\S+)", re.MULTILINE)
HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")


def github_slug(heading: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", heading.strip().lower())
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def outside_fences(text: str) -> list[str]:
    """Lines outside fenced code blocks; a fence closes only with a marker
    of the same character at least as long as the opening one."""
    lines: list[str] = []
    opener = ""
    for line in text.splitlines():
        fence = FENCE.match(line)
        if fence:
            marker = fence.group(1)
            if not opener:
                opener = marker
                continue
            closes = marker[0] == opener[0] and len(marker) >= len(opener)
            if closes and not line.strip()[len(marker) :].strip():
                opener = ""
                continue
        if not opener:
            lines.append(line)
    return lines


def headings(path: Path) -> set[str]:
    slugs: set[str] = set()
    counts: dict[str, int] = {}
    for line in outside_fences(path.read_text(encoding="utf-8")):
        match = HEADING.match(line)
        if not match:
            continue
        slug = github_slug(match.group(2))
        seen = counts.get(slug, 0)
        slugs.add(slug if seen == 0 else f"{slug}-{seen}")
        counts[slug] = seen + 1
    return slugs


def links(path: Path) -> list[str]:
    joined = "\n".join(outside_fences(path.read_text(encoding="utf-8")))
    return INLINE_LINK.findall(joined) + DEFINITION.findall(joined)


def frontmatter(skill_md: Path) -> dict[str, str]:
    text = skill_md.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    fields: dict[str, str] = {}
    current = None
    for line in text[4:end].splitlines():
        key = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
        if key:
            current = key.group(1)
            value = key.group(2)
            fields[current] = "" if value in (">-", ">", "|", "|-") else value
        elif current and line.startswith(" "):
            fields[current] = (fields[current] + " " + line.strip()).strip()
    return fields


def check_skill(skill: Path) -> list[str]:
    problems: list[str] = []
    skill_md = skill / "SKILL.md"
    if not skill_md.is_file():
        return [f"{skill}: missing SKILL.md"]

    meta = frontmatter(skill_md)
    if meta.get("name") != skill.name:
        problems.append(f"{skill_md}: name must equal directory '{skill.name}'")
    description = meta.get("description", "")
    if not description or len(description) > 1024:
        problems.append(f"{skill_md}: description must be 1-1024 characters")

    references = sorted((skill / "references").glob("**/*.md"))
    linked_from_skill = {
        (skill_md.parent / target.split("#")[0]).resolve()
        for target in links(skill_md)
        if "://" not in target and not target.startswith("#")
    }
    for reference in references:
        if reference.resolve() not in linked_from_skill:
            problems.append(f"{reference}: not linked directly from SKILL.md")
        lines = reference.read_text(encoding="utf-8").splitlines()
        if len(lines) > 100 and not any(
            line.strip() == "## Contents" for line in lines
        ):
            problems.append(
                f"{reference}: {len(lines)} lines but no '## Contents' section"
            )

    for document in [skill_md, *references]:
        for target in links(document):
            if "://" in target or target.startswith("mailto:"):
                continue
            file_part, _, anchor = target.partition("#")
            destination = document if not file_part else (document.parent / file_part)
            if not destination.exists():
                problems.append(f"{document}: missing link target {target}")
                continue
            is_markdown = destination.suffix == ".md"
            if anchor and is_markdown and anchor not in headings(destination):
                problems.append(f"{document}: missing anchor {target}")
    return problems


EPILOG = """\
Output: one "PATH: problem" line per problem, or "OK N skill(s)". --json
prints {"problems": [{file, message}], "skills": N}.

Examples:
  python3 scripts/check_reference_structure.py skills/my-skill
  python3 scripts/check_reference_structure.py skills/* --json \\
    | jq '.problems[].message'
"""


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        usage="check_reference_structure.py [-h] [--json] SKILL_DIR [SKILL_DIR ...]",
        description=(__doc__ or "").strip(),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("skills", nargs="+", metavar="SKILL_DIR", help="skill folder")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit:  # keep main() returning a status for callers
        return int(exit.code or 0)
    problems: list[str] = []
    for raw in args.skills:
        skill = Path(raw)
        if not skill.is_dir():
            print(
                f"error: {raw} is not a directory; pass a skill folder that holds "
                "SKILL.md",
                file=sys.stderr,
            )
            return 2
        problems.extend(check_skill(skill))
    if args.json:
        records = [
            dict(zip(("file", "message"), problem.split(": ", 1), strict=True))
            for problem in problems
        ]
        print(json.dumps({"problems": records, "skills": len(args.skills)}, indent=2))
        return 1 if problems else 0
    for problem in problems:
        print(problem)
    if not problems:
        print(f"OK {len(args.skills)} skill(s)")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
