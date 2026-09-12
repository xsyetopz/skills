"""Validate skill identities, OpenAI metadata, and internal Markdown links."""

import re
import sys
from pathlib import Path

import yaml

SKILL_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)")
REFERENCE_LINK = re.compile(r"^\[[^]]+\]:\s*(?:\n\s*)?([^\s#]+)", re.MULTILINE)
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
USE_WHEN = re.compile(r"[.!?]\s+Use when\s+\S", re.DOTALL)
DISCOVERY_CONTRADICTION = re.compile(
    r"(?:"
    r"only when (?:the user )?explicitly invokes?"
    r"|use when explicitly invoked"
    r"|only when invoked as \$"
    r"|manual invocation by default"
    r"|explicit-only"
    r"|not an invocation"
    r")",
    re.IGNORECASE,
)


def has_capability_and_activation(description: str) -> bool:
    capability, separator, activation = description.partition("Use when")
    return bool(
        separator
        and USE_WHEN.search(description)
        and len(capability.strip(" .!?")) >= 10
        and len(activation.strip(" .!?")) >= 10
    )


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
        if not isinstance(metadata, dict):
            fail(f"{skill_md}: frontmatter must be a mapping")
            errors += 1
            continue
        if metadata.get("name") != skill.name or not NAME.fullmatch(skill.name):
            fail(f"{skill_md}: name must match its valid directory name")
            errors += 1
        description = metadata.get("description")
        if not isinstance(description, str) or not 1 <= len(description) <= 1024:
            fail(f"{skill_md}: description must be a 1-1024 character string")
            errors += 1
        elif not has_capability_and_activation(description):
            fail(
                f'{skill_md}: description must state a capability followed by "Use when..."'
            )
            errors += 1
        elif DISCOVERY_CONTRADICTION.search(description):
            fail(f"{skill_md}: description contradicts automatic discovery")
            errors += 1
        compatibility = metadata.get("compatibility")
        if "compatibility" in metadata and (
            not isinstance(compatibility, str) or not 1 <= len(compatibility) <= 500
        ):
            fail(f"{skill_md}: compatibility must be a 1-500 character string")
            errors += 1
        body = text.split("---", 2)[2]
        if DISCOVERY_CONTRADICTION.search(body):
            fail(f"{skill_md}: body contradicts automatic discovery")
            errors += 1
        openai_path = skill / "agents/openai.yaml"
        try:
            openai = yaml.safe_load(openai_path.read_text())
            interface = openai["interface"]
            if not all(
                isinstance(interface[field], str)
                for field in ("display_name", "short_description", "default_prompt")
            ):
                fail(f"{openai_path}: interface fields must be strings")
                errors += 1
                continue
            if f"${skill.name}" not in interface["default_prompt"]:
                fail(f"{openai_path}: default_prompt must name the skill")
                errors += 1
            policy = openai.get("policy", {})
            if not isinstance(policy, dict):
                fail(f"{openai_path}: policy must be a mapping")
                errors += 1
            elif "allow_implicit_invocation" in policy:
                fail(f"{openai_path}: allow_implicit_invocation is not permitted")
                errors += 1
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
