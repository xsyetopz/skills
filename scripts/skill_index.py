"""Print a skill index to paste into CLAUDE.md or AGENTS.md.

Each line names a skill and when to use it, taken from the "Use when" or
"Use before" sentence of its description. Manual-only skills
(disable-model-invocation) are left out, because the agent cannot load them.

Examples:
  python3 scripts/skill_index.py
  python3 scripts/skill_index.py --bundle core-engineering --bundle repo-workflow
"""

import argparse
import re
import sys
from pathlib import Path

import tomllib
from validate_repository import BUNDLES, read_frontmatter

# The sentence ends at a period before the next sentence, not inside SKILL.md.
USE = re.compile(r"\bUse ((?:when|before)\b.*?\.)(?=\s+[A-Z]|\s*$)")


def main() -> int:
    bundles: dict[str, list[str]] = tomllib.loads(BUNDLES.read_text())["bundles"]
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--bundle",
        action="append",
        choices=list(bundles),
        help="bundle to include; repeat for more (default: all)",
    )
    args = parser.parse_args()
    lines: list[str] = []
    for bundle in args.bundle or bundles:
        for name in bundles[bundle]:
            skill_md = Path("skills", name, "SKILL.md")
            try:
                metadata, _ = read_frontmatter(skill_md.read_text())
            except (OSError, ValueError) as error:
                print(f"{skill_md}: {error}", file=sys.stderr)
                return 1
            if metadata.get("disable-model-invocation"):
                continue
            use = USE.search(str(metadata.get("description", "")))
            if not use:
                print(
                    f"{skill_md}: description has no 'Use when' sentence",
                    file=sys.stderr,
                )
                return 1
            lines.append(f"- `{name}`: {use.group(1)}")
    print("## Skills\n\nLoad the skill whose line matches the task:\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
