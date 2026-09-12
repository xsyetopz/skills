import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDLER = ROOT / "assets/shared/observe.py"


class HookAssetTests(unittest.TestCase):
    def test_json_configurations_are_objects(self):
        # Arrange
        paths = sorted((ROOT / "assets").glob("*/hooks.json")) + sorted(
            (ROOT / "assets").glob("*/settings.json")
        )
        # Act
        configurations = [json.loads(path.read_text()) for path in paths]
        # Assert
        self.assertEqual(len(configurations), 6)
        self.assertTrue(
            all(isinstance(value.get("hooks"), dict) for value in configurations)
        )

    def test_handler_accepts_every_provider_fixture(self):
        # Arrange
        fixtures = sorted((ROOT / "assets/fixtures").glob("*.json"))
        # Act
        results = [
            subprocess.run(
                [sys.executable, str(HANDLER)],
                input=path.read_text(),
                text=True,
                capture_output=True,
                check=False,
            )
            for path in fixtures
        ]
        # Assert
        self.assertEqual(len(results), 6)
        self.assertTrue(all(result.returncode == 0 for result in results))
        self.assertTrue(all(json.loads(result.stdout) == {} for result in results))
        self.assertTrue(all(not result.stderr for result in results))

    def test_handler_rejects_non_object_without_stdout(self):
        # Arrange
        invalid = "[]"
        # Act
        result = subprocess.run(
            [sys.executable, str(HANDLER)],
            input=invalid,
            text=True,
            capture_output=True,
            check=False,
        )
        # Assert
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")
        self.assertIn("expected a JSON object", result.stderr)


if __name__ == "__main__":
    unittest.main()
