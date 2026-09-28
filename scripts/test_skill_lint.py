"""Tests for skill_lint.py findings on small skill trees."""

from __future__ import annotations

import argparse
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import skill_lint

FRONTMATTER = (
    "---\nname: demo\ndescription: >-\n  Does demo work. Use\n  when testing.\n---\n"
)


def lint(files: dict[str, str]) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "demo"
        for rel, text in files.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
        args = argparse.Namespace(
            max_lines=500,
            max_body_tokens=5000,
            headroom=0.1,
            max_ref_tokens=10000,
            toc_lines=100,
            allow=["agents"],
        )
        report = skill_lint.lint(root, args)
        return report.errors + report.warnings


class SkillLintTest(unittest.TestCase):
    def test_clean_skill_has_no_findings(self):
        findings = lint(
            {
                "SKILL.md": FRONTMATTER + "Run `scripts/run.py`.\n",
                "scripts/run.py": "import argparse\nif __name__ == '__main__':\n    pass\n",
            }
        )
        self.assertEqual(findings, [])

    def test_claude_skill_dir_path_counts_as_reference(self):
        findings = lint(
            {
                "SKILL.md": FRONTMATTER
                + "Run `${CLAUDE_SKILL_DIR}/scripts/run.sh --help`.\n"
                "Also `${CLAUDE_SKILL_DIR}/scripts/gone.sh`.\n",
                "scripts/run.sh": "#!/bin/sh\n# --help prints usage\n",
            }
        )
        self.assertEqual(
            findings, ["[spec] SKILL.md:8: 'scripts/gone.sh' does not exist"]
        )

    def test_plugin_root_path_is_not_checked(self):
        findings = lint(
            {"SKILL.md": FRONTMATTER + "Run `${CLAUDE_PLUGIN_ROOT}/scripts/x.sh`.\n"}
        )
        self.assertEqual(findings, [])

    def test_python_prompt_is_a_call_not_a_word(self):
        findings = lint(
            {
                "SKILL.md": FRONTMATTER + "Run `scripts/ask.py`.\n",
                "scripts/ask.py": '"""Exit 2 on invalid input (bad JSON)."""\n'
                "import argparse\n"
                "name = input('name? ')\n"
                "ok = input('again? ')  # skill-lint: allow-interactive\n"
                "if __name__ == '__main__':\n    pass\n",
            }
        )
        self.assertEqual(len(findings), 1)
        self.assertIn("scripts/ask.py:3: interactive input", findings[0])

    def test_tests_and_imported_modules_need_no_help_or_reference(self):
        findings = lint(
            {
                "SKILL.md": FRONTMATTER + "Run `scripts/main.py`.\n",
                "scripts/main.py": "import argparse\nimport helper\n"
                "if __name__ == '__main__':\n    pass\n",
                "scripts/helper.py": "VALUE = 1\n",
                "scripts/test_main.py": "import unittest\n"
                "if __name__ == '__main__':\n    unittest.main()\n",
            }
        )
        self.assertEqual(findings, [])

    def test_example_project_files_are_reached_through_its_harness(self):
        findings = lint(
            {
                "SKILL.md": FRONTMATTER + "Run `assets/examples/verify.sh`.\n",
                "assets/examples/verify.sh": "#!/bin/sh\n",
                "assets/examples/app/main.go": "package main\n",
                "assets/other/unused.txt": "x\n",
            }
        )
        self.assertEqual(len(findings), 1)
        self.assertIn("assets/other/unused.txt: not referenced", findings[0])

    def test_nested_reference_is_an_error_but_linked_asset_is_not(self):
        findings = lint(
            {
                "SKILL.md": FRONTMATTER + "See [a](references/a.md).\n",
                "references/a.md": "See [b](b.md) and [ex](../assets/example.md).\n",
                "references/b.md": "B\n",
                "assets/example.md": "Example\n",
            }
        )
        self.assertEqual(len(findings), 1)
        self.assertIn("references/a.md:1: links to 'b.md'", findings[0])

    def test_root_auxiliary_doc_is_an_error_but_example_readme_is_not(self):
        findings = lint(
            {
                "SKILL.md": FRONTMATTER + "Run `assets/examples/app/build.sh`.\n",
                "README.md": "Human docs\n",
                "assets/examples/app/build.sh": "#!/bin/sh\n",
                "assets/examples/app/README.md": "Example project docs\n",
            }
        )
        aux = [f for f in findings if "auxiliary docs" in f]
        self.assertEqual(len(aux), 1)
        self.assertIn("] README.md: auxiliary docs", aux[0])

    def test_junk_file_is_an_error(self):
        findings = lint(
            {
                "SKILL.md": FRONTMATTER,
                "scripts/__pycache__/x.cpython-314.pyc": "",
            }
        )
        self.assertTrue(any("build, OS, editor" in f for f in findings), findings)

    def test_description_without_when_to_use_warns(self):
        findings = lint({"SKILL.md": "---\nname: demo\ndescription: Does work.\n---\n"})
        self.assertEqual(
            findings,
            [
                "[spec] description should say when to use the skill, not just what it does"
            ],
        )


if __name__ == "__main__":
    unittest.main()
