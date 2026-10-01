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
    CATALOG_MAX,
    DESCRIPTION_MAX,
    catalog_entry,
    catalog_size,
)


def write_skill(root: Path, name: str, description: str, body_lines: int) -> None:
    skill = root / "skills" / name
    (skill / "agents").mkdir(parents=True)
    body = "\n".join(f"line {i}" for i in range(body_lines))
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n"
    )
    (skill / "agents/openai.yaml").write_text(
        "interface:\n"
        f"  display_name: {name}\n"
        "  short_description: A short description for tests\n"
        f"  default_prompt: Use ${name} here.\n"
    )


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
    def check(self, description: str, body_lines: int) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_skill(root, "demo-skill", description, body_lines)
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

    def test_catalog_over_budget_fails(self) -> None:
        overhead = len(catalog_entry("s-00", ""))
        count = CATALOG_MAX // (overhead + DESCRIPTION_MAX) + 1
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for i in range(count):
                write_skill(root, f"s-{i:02d}", "x" * DESCRIPTION_MAX, 5)
            result = run(root)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"maximum is {CATALOG_MAX}", result.stderr)

    def test_catalog_at_budget_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            overhead = len(catalog_entry("s-00", ""))
            remaining = CATALOG_MAX
            i = 0
            while remaining > overhead:
                size = min(DESCRIPTION_MAX, remaining - overhead)
                write_skill(root, f"s-{i:02d}", "x" * size, 5)
                remaining -= overhead + size
                i += 1
            result = run(root)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(f"catalog listing: {CATALOG_MAX - remaining}/", result.stdout)


if __name__ == "__main__":
    unittest.main()
