"""Boundary tests for the repository validator's limits."""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "validate_repository.py"
sys.path.insert(0, str(SCRIPT.parent))

from validate_repository import (  # noqa: E402
    BODY_MAX_LINES,
    BUNDLE_MAX,
    DESCRIPTION_MAX,
    WHEN_TO_USE_MAX,
    catalog_entry,
    catalog_size,
)


def write_skill(
    root: Path, name: str, description: str, body_lines: int, extra: str = ""
) -> None:
    skill = root / "skills" / name
    (skill / "agents").mkdir(parents=True)
    body = "\n".join(f"line {i}" for i in range(body_lines))
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n{extra}---\n\n{body}\n"
    )
    (skill / "agents/openai.yaml").write_text(
        "interface:\n"
        f"  display_name: {name}\n"
        "  short_description: A short description for tests\n"
        f"  default_prompt: Use ${name} here.\n"
    )


def write_bundles(root: Path, bundles: dict[str, list[str]]) -> None:
    lines = ["[bundles]"]
    lines += [
        f"{key} = {members!r}".replace("'", '"') for key, members in bundles.items()
    ]
    (root / "bundles.toml").write_text("\n".join(lines) + "\n")


def bundle_all(root: Path) -> None:
    names = sorted(path.name for path in (root / "skills").iterdir())
    write_bundles(root, {"all": names})


def run(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


class CatalogSizeTest(unittest.TestCase):
    def test_entry_matches_codex_rendering(self) -> None:
        self.assertEqual(
            catalog_entry("a-b", "Does x."),
            "- a-b: Does x. (file: skills/a-b/SKILL.md)",
        )

    def test_size_sums_entries(self) -> None:
        skills = {"a": "x", "bb": "yy"}
        expected = len(catalog_entry("a", "x")) + len(catalog_entry("bb", "yy"))
        self.assertEqual(catalog_size(skills), expected)


class LimitsTest(unittest.TestCase):
    def check(
        self, description: str, body_lines: int, extra: str = ""
    ) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root, "demo-skill", description, body_lines, extra)
            bundle_all(root)
            return run(root)

    def test_body_at_limit_passes(self) -> None:
        result = self.check("Does a thing.", BODY_MAX_LINES)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_body_over_limit_fails(self) -> None:
        result = self.check("Does a thing.", BODY_MAX_LINES + 1)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"maximum is {BODY_MAX_LINES}", result.stderr)

    def test_description_at_limit_passes(self) -> None:
        result = self.check("x" * DESCRIPTION_MAX, 10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_description_over_limit_fails(self) -> None:
        result = self.check("x" * (DESCRIPTION_MAX + 1), 10)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"maximum is {DESCRIPTION_MAX}", result.stderr)

    def test_when_to_use_at_limit_passes(self) -> None:
        result = self.check(
            "Does a thing.", 10, f"when_to_use: {'x' * WHEN_TO_USE_MAX}\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_when_to_use_over_limit_fails(self) -> None:
        extra = f"when_to_use: {'x' * (WHEN_TO_USE_MAX + 1)}\n"
        result = self.check("Does a thing.", 10, extra)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"at most {WHEN_TO_USE_MAX}", result.stderr)

    def test_bundle_over_budget_fails(self) -> None:
        overhead = len(catalog_entry("s-00", ""))
        count = BUNDLE_MAX // (overhead + DESCRIPTION_MAX) + 1
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(count):
                write_skill(root, f"s-{i:02d}", "x" * DESCRIPTION_MAX, 5)
            bundle_all(root)
            result = run(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"maximum is {BUNDLE_MAX}", result.stderr)

    def test_bundle_at_budget_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            overhead = len(catalog_entry("s-00", ""))
            remaining = BUNDLE_MAX
            i = 0
            while remaining > overhead:
                size = min(DESCRIPTION_MAX, remaining - overhead)
                write_skill(root, f"s-{i:02d}", "x" * size, 5)
                remaining -= overhead + size
                i += 1
            bundle_all(root)
            result = run(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"all listing: {BUNDLE_MAX - remaining}/", result.stdout)

    def test_split_bundles_each_fit(self) -> None:
        overhead = len(catalog_entry("s-00", ""))
        count = BUNDLE_MAX // (overhead + DESCRIPTION_MAX) + 1
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            names = [f"s-{i:02d}" for i in range(count)]
            for name in names:
                write_skill(root, name, "x" * DESCRIPTION_MAX, 5)
            write_bundles(root, {"a": names[:2], "b": names[2:]})
            result = run(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_manual_skill_costs_no_listing(self) -> None:
        overhead = len(catalog_entry("s-00", ""))
        count = BUNDLE_MAX // (overhead + DESCRIPTION_MAX) + 1
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(count):
                write_skill(
                    root,
                    f"s-{i:02d}",
                    "x" * DESCRIPTION_MAX,
                    5,
                    "disable-model-invocation: true\n" if i == 0 else "",
                )
            bundle_all(root)
            result = run(root)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unbundled_and_unknown_skills_fail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root, "demo-skill", "Does a thing.", 5)
            write_bundles(root, {"all": ["ghost-skill"]})
            result = run(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("unknown skill ghost-skill", result.stderr)
        self.assertIn("demo-skill is in no bundle", result.stderr)

    def test_skill_in_two_bundles_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root, "demo-skill", "Does a thing.", 5)
            write_bundles(root, {"a": ["demo-skill"], "b": ["demo-skill"]})
            result = run(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn("demo-skill is in both a and b", result.stderr)


if __name__ == "__main__":
    unittest.main()
