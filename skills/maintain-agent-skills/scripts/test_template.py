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
            "{What this skill does and the concrete activation boundary.}",
            "Create a verified sample artifact when explicitly requested.",
        )
        rendered = rendered.replace("{Action-oriented title}", "Create Sample")
        rendered = rendered.replace(
            "{State the operating rule and required inputs.}",
            "Require the target path before writing the sample.",
        )
        rendered = rendered.replace(
            "{Inspect the relevant evidence.}", "Inspect the target."
        )
        rendered = rendered.replace(
            "{Perform the smallest coherent change or analysis.}", "Create the sample."
        )
        rendered = rendered.replace(
            "{Produce the requested artifact or decision.}", "Return its path."
        )
        rendered = rendered.replace(
            "{Name observable checks and the required completion evidence.}",
            "Open the artifact and verify its expected content.",
        )
        with tempfile.TemporaryDirectory() as temporary:
            skill = Path(temporary) / "sample-skill"
            skill.mkdir()
            (skill / "SKILL.md").write_text(rendered)
            # Act
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
            # Assert
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
