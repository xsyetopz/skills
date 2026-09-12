"""Validate skill identities, OpenAI metadata, and internal Markdown links."""

import re
import sys
from pathlib import Path

import yaml

SKILL_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)")
REFERENCE_LINK = re.compile(r"^\[[^]]+\]:\s*(?:\n\s*)?([^\s#]+)", re.MULTILINE)
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def fail(message: str) -> None:
    print(message, file=sys.stderr)


def main() -> int:
    errors = 0
    roots = sorted(Path("skills").glob("*/SKILL.md"))
    names = {path.parent.name for path in roots}
    for skill_md in roots:
        skill = skill_md.parent
        text = skill_md.read_text()
        try:
            _, frontmatter, _ = text.split("---", 2)
            metadata = yaml.safe_load(frontmatter)
        except (ValueError, yaml.YAMLError) as error:
            fail(f"{skill_md}: invalid frontmatter: {error}")
            errors += 1
            continue
        if metadata.get("name") != skill.name or not NAME.fullmatch(skill.name):
            fail(f"{skill_md}: name must match its valid directory name")
            errors += 1
        openai_path = skill / "agents/openai.yaml"
        try:
            openai = yaml.safe_load(openai_path.read_text())
            interface = openai["interface"]
            if not all(
                isinstance(interface[field], str)
                for field in ("display_name", "short_description", "default_prompt")
            ):
                raise TypeError("interface fields must be strings")
            if f"${skill.name}" not in interface["default_prompt"]:
                raise ValueError("default_prompt must name the skill")
            policy = openai.get("policy", {})
            if "allow_implicit_invocation" in policy and not isinstance(
                policy["allow_implicit_invocation"], bool
            ):
                raise TypeError("invocation policy must be a boolean")
        except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as error:
            fail(f"{openai_path}: invalid OpenAI metadata: {error}")
            errors += 1
        for markdown in skill.rglob("*.md"):
            if markdown.name.endswith(".template.md"):
                continue
            markdown_text = markdown.read_text()
            targets = [
                *SKILL_LINK.findall(markdown_text),
                *REFERENCE_LINK.findall(markdown_text),
            ]
            for target in targets:
                if "://" in target or target.startswith("mailto:"):
                    continue
                resolved = (markdown.parent / target).resolve()
                if not resolved.exists():
                    fail(f"{markdown}: missing link target {target}")
                    errors += 1
        for match in re.findall(r"\$([a-z0-9-]+)", text):
            if match not in names:
                fail(f"{skill_md}: unknown skill ${match}")
                errors += 1
    return int(errors > 0)


if __name__ == "__main__":
    raise SystemExit(main())
