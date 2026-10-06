"""Validate skill identities, OpenAI metadata, install bundles, and internal Markdown links."""

import re
import sys
from pathlib import Path

import tomllib
import yaml

SKILL_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)#]+)(?:#[^)]+)?\)")
REFERENCE_LINK = re.compile(r"^\[[^]]+\]:\s*(?:\n\s*)?([^\s#]+)", re.MULTILINE)
NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
FENCE = re.compile(r"^\s*(`{3,}|~{3,})")
BODY_MAX_LINES = 200
# Claude Code lists each skill as description + " - " + when_to_use and cuts
# the entry at 300 characters with "…" (seen in 2.1.283-2.1.289, in sessions
# listing 47-213 skills, on 2026-10-07).
# Text past the cut never reaches the model, so descriptions stay within it
# and when_to_use is rejected.
DESCRIPTION_MAX = 300
# Claude Code lists skills within 1% of the context window (about 8,000
# characters at 200k tokens), and Codex falls back to 8,000 characters. Users
# install one bundle at a time, so each bundle's listing must fit.
BUNDLE_MAX = 8000
BUNDLES = Path("bundles.toml")


def catalog_entry(name: str, description: str) -> str:
    return f"- {name}: {description} (file: skills/{name}/SKILL.md)"


def catalog_size(skills: dict[str, str]) -> int:
    return sum(len(catalog_entry(name, desc)) for name, desc in skills.items())


def outside_fences(text: str) -> str:
    """Drop fenced code blocks; examples inside them are not links."""
    kept: list[str] = []
    opener = ""
    for line in text.splitlines():
        fence = FENCE.match(line)
        if fence and not opener:
            opener = fence.group(1)
            continue
        if fence and opener:
            marker = fence.group(1)
            closes = marker[0] == opener[0] and len(marker) >= len(opener)
            if closes and not line.strip()[len(marker) :].strip():
                opener = ""
                continue
        if not opener:
            kept.append(line)
    return "\n".join(kept)


def read_frontmatter(text: str) -> tuple[dict, str]:
    """Split a SKILL.md into its frontmatter mapping and body; raise ValueError."""
    try:
        _, frontmatter, body = text.split("---", 2)
        metadata = yaml.safe_load(frontmatter)
    except (ValueError, yaml.YAMLError) as error:
        raise ValueError(f"invalid frontmatter: {error}") from error
    if not isinstance(metadata, dict):
        raise ValueError("frontmatter must be a mapping")
    return metadata, body


def fail(message: str) -> None:
    print(message, file=sys.stderr)


def main() -> int:
    errors = 0
    roots = sorted(Path("skills").glob("*/SKILL.md"))
    names = {path.parent.name for path in roots}
    listings: dict[str, str] = {}
    for skill_md in roots:
        skill = skill_md.parent
        text = skill_md.read_text()
        try:
            metadata, body = read_frontmatter(text)
        except ValueError as error:
            fail(f"{skill_md}: {error}")
            errors += 1
            continue
        body_lines = len(body.strip().splitlines())
        if body_lines > BODY_MAX_LINES:
            fail(
                f"{skill_md}: body has {body_lines} lines; maximum is {BODY_MAX_LINES}"
            )
            errors += 1
        if metadata.get("name") != skill.name or not NAME.fullmatch(skill.name):
            fail(f"{skill_md}: name must match its valid directory name")
            errors += 1
        description = metadata.get("description")
        if not isinstance(description, str) or not 1 <= len(description) <= 1024:
            fail(f"{skill_md}: description must be a 1-1024 character string")
            errors += 1
        elif len(description) > DESCRIPTION_MAX:
            fail(
                f"{skill_md}: description has {len(description)} characters; "
                f"maximum is {DESCRIPTION_MAX}"
            )
            errors += 1
        if "when_to_use" in metadata:
            fail(f"{skill_md}: when_to_use is not allowed; put it in description")
            errors += 1
        elif isinstance(description, str) and not metadata.get(
            "disable-model-invocation"
        ):
            listings[skill.name] = description
        compatibility = metadata.get("compatibility")
        if "compatibility" in metadata and (
            not isinstance(compatibility, str) or not 1 <= len(compatibility) <= 500
        ):
            fail(f"{skill_md}: compatibility must be a 1-500 character string")
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
            elif "allow_implicit_invocation" in policy and not isinstance(
                policy["allow_implicit_invocation"], bool
            ):
                fail(f"{openai_path}: allow_implicit_invocation must be a boolean")
                errors += 1
        except (OSError, KeyError, TypeError, ValueError, yaml.YAMLError) as error:
            fail(f"{openai_path}: invalid OpenAI metadata: {error}")
            errors += 1
        for markdown in skill.rglob("*.md"):
            if markdown.name.endswith(".template.md"):
                continue
            markdown_text = outside_fences(markdown.read_text())
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
    return int(errors > 0) | check_bundles(names, listings)


def check_bundles(names: set[str], listings: dict[str, str]) -> int:
    """Each skill sits in one bundle, and each bundle's listing fits its budget."""
    try:
        bundles = tomllib.loads(BUNDLES.read_text())["bundles"]
    except (OSError, KeyError, tomllib.TOMLDecodeError) as error:
        fail(f"{BUNDLES}: invalid bundle map: {error}")
        return 1
    errors = 0
    seen: dict[str, str] = {}
    for bundle, members in bundles.items():
        for name in members:
            if name not in names:
                fail(f"{BUNDLES}: {bundle} names unknown skill {name}")
                errors += 1
            elif name in seen:
                fail(f"{BUNDLES}: {name} is in both {seen[name]} and {bundle}")
                errors += 1
            seen[name] = bundle
        listed = {name: listings[name] for name in members if name in listings}
        total = catalog_size(listed)
        print(f"{bundle} listing: {total}/{BUNDLE_MAX} characters")
        if total > BUNDLE_MAX:
            fail(f"{bundle} listing has {total} characters; maximum is {BUNDLE_MAX}")
            errors += 1
    for name in sorted(names - seen.keys()):
        fail(f"{BUNDLES}: {name} is in no bundle")
        errors += 1
    return int(errors > 0)


if __name__ == "__main__":
    raise SystemExit(main())
