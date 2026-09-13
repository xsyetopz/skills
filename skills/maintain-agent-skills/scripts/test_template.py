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
            "{State the observable outcome, required inputs and non-obvious constraints.}",
            "Require the target path, create the sample, and return its path.",
        )
        rendered = rendered.replace(
            "{If workflows need different context, link each resource with its loading\ncondition. Omit this paragraph for a self-contained skill.}",
            "",
        )
        rendered = rendered.replace(
            "{State proportionate completion evidence and what remains unverified when a\nrequired check cannot run. Keep only sections that help this task.}",
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
