"""Validate each skill against the Agent Skills spec, allowing Claude Code fields.

The reference validator (skills-ref) rejects every field outside the spec. The fields
below are documented Claude Code extensions that other hosts ignore, so they are removed
before the spec check runs. Their own limits are checked in validate_repository.py.
"""

import sys
from pathlib import Path

from skills_ref.errors import ParseError
from skills_ref.parser import find_skill_md, parse_frontmatter
from skills_ref.validator import validate_metadata

# https://code.claude.com/docs/en/skills#frontmatter-reference
CLAUDE_CODE_FIELDS = frozenset({"when_to_use", "disable-model-invocation"})


def validate(skill_dir: Path) -> list[str]:
    skill_md = find_skill_md(skill_dir)
    if skill_md is None:
        return ["Missing required file: SKILL.md"]
    try:
        metadata, _ = parse_frontmatter(skill_md.read_text())
    except ParseError as error:
        return [str(error)]
    spec = {k: v for k, v in metadata.items() if k not in CLAUDE_CODE_FIELDS}
    return validate_metadata(spec, skill_dir)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: validate_spec.py SKILL_DIR...", file=sys.stderr)
        return 2
    failed = 0
    for arg in argv:
        errors = validate(Path(arg))
        for error in errors:
            print(f"{arg}: {error}", file=sys.stderr)
        failed += bool(errors)
    print(f"{len(argv)} skill(s) checked against the spec, {failed} invalid")
    return int(failed > 0)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
