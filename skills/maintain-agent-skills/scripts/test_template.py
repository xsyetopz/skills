import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class SkillTemplateTests(unittest.TestCase):
    def test_rendered_template_passes_reference_validator(self):
        # Arrange
        rendered = (ROOT / "assets/SKILL.template.md").read_text()
        rendered = rendered.replace("{skill-name}", "sample-skill")
        rendered = rendered.replace(
            "{State the recognizable user goal and nearest meaningful non-trigger.}",
            "Create a verified sample artifact, not a production starter.",
        )
        rendered = rendered.replace("{Action-oriented title}", "Create Sample")
        rendered = rendered.replace(
            "{State the outcome, required inputs, and invariants. Route conditional detail to\nfocused references.}",
            "Require the target path, create the sample, and return its path.",
        )
        rendered = rendered.replace(
            "{Name observable checks and the required completion evidence.}",
            "Open the artifact and verify its expected content.",
        )
        with tempfile.TemporaryDirectory() as temporary:
            skill = Path(temporary) / "sample-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text(rendered)
            result = subprocess.run(
                [
                    str(Path(sys.executable).with_name("skills-ref")),
                    "validate",
                    str(skill),
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
