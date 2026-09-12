import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("check_justfiles.py")
EXAMPLE = Path(__file__).parents[1] / "assets/example.just"


class JustfileCheckTests(unittest.TestCase):
    def run_check(self, *paths: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(SCRIPT), *(str(path) for path in paths)],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_accepts_modern_environment_functions(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "justfile"
            path.write_text(
                'value := env("VALUE", "fallback")\n\ndefault:\n'
                "    @printf '%s\\n' \"{{ value }}\"\n"
            )
            result = self.run_check(path)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_rejects_each_deprecated_environment_function(self):
        for function in ("env_var", "env_var_or_default"):
            with (
                self.subTest(function=function),
                tempfile.TemporaryDirectory() as temporary,
            ):
                path = Path(temporary) / "deprecated.just"
                arguments = '"VALUE"' if function == "env_var" else '"VALUE", "x"'
                path.write_text(
                    f"value := {function}({arguments})\n\ndefault:\n"
                    "    @printf '%s\\n' \"{{ value }}\"\n"
                )
                result = self.run_check(path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(f"deprecated {function}()", result.stderr)

    def test_reports_invalid_just_syntax(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "justfile"
            path.write_text("default\n")
            result = self.run_check(path)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("just --fmt --check failed", result.stderr)

    def test_example_runs_without_side_effects(self):
        environment = {**os.environ, "XDG_CACHE_HOME": "/tmp/just-skill-cache"}
        result = subprocess.run(
            ["just", "--justfile", str(EXAMPLE)],
            capture_output=True,
            text=True,
            check=False,
            env=environment,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "/tmp/just-skill-cache\n")


if __name__ == "__main__":
    raise SystemExit(unittest.main())
