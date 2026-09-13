import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "scripts/validate_repository.py"


class RepositoryValidatorTests(unittest.TestCase):
    def validate(
        self,
        description="Create a sample artifact. Use when a sample is requested.",
        *,
        body="Apply the sample workflow.\n",
        policy="",
        compatibility="",
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skill = root / "skills/sample-skill"
            (skill / "agents").mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\n"
                "name: sample-skill\n"
                f"description: {description}\n"
                f"{compatibility}"
                "---\n\n"
                f"{body}"
            )
            (skill / "agents/openai.yaml").write_text(
                "interface:\n"
                '  display_name: "Sample Skill"\n'
                '  short_description: "Create a sample"\n'
                '  default_prompt: "Use $sample-skill to create a sample."\n'
                f"{policy}"
            )
            return subprocess.run(
                [sys.executable, str(VALIDATOR)],
                cwd=root,
                text=True,
                capture_output=True,
                check=False,
            )

    def test_valid_description_and_omitted_policy_pass(self):
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_concise_natural_description_passes(self):
        result = self.validate("Create a verified sample artifact.")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_boolean_invocation_policy_passes(self):
        result = self.validate(policy="policy:\n  allow_implicit_invocation: false\n")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_non_boolean_invocation_policy_is_rejected(self):
        result = self.validate(policy='policy:\n  allow_implicit_invocation: "false"\n')
        self.assertEqual(result.returncode, 1)
        self.assertIn("allow_implicit_invocation must be a boolean", result.stderr)

    def test_malformed_description_is_rejected(self):
        for description in ('""', "3"):
            with self.subTest(description=description):
                result = self.validate(description)
                self.assertEqual(result.returncode, 1)
                self.assertIn("description must be", result.stderr)

    def test_invalid_compatibility_values_are_rejected(self):
        for compatibility in (
            'compatibility: ""\n',
            "compatibility: 3\n",
            f"compatibility: {'x' * 501}\n",
        ):
            with self.subTest(compatibility=compatibility[:30]):
                result = self.validate(compatibility=compatibility)
                self.assertEqual(result.returncode, 1)
                self.assertIn("compatibility must be", result.stderr)


if __name__ == "__main__":
    unittest.main()
