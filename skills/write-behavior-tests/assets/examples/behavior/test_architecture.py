"""An agreed dependency rule, checked from imports: production code
(subjects.py) must not import test code. Class names stay free to change."""

import ast
import shutil
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEST_MODULES = {"harness", "variants", "run_matrix"}


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[0])
    return names


def violations(path: Path) -> set[str]:
    return {
        name
        for name in imported_modules(path)
        if name in TEST_MODULES or name.startswith(("test_", "weak_"))
    }


class ArchitectureTests(unittest.TestCase):
    def test_production_code_does_not_import_tests(self):
        self.assertEqual(violations(HERE / "subjects.py"), set())

    def test_rule_detects_a_forbidden_import(self):
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory)
        probe = directory / "probe_violation.py"
        probe.write_text("from harness import impl\nimport os\n", encoding="utf-8")
        self.assertEqual(violations(probe), {"harness"})


if __name__ == "__main__":
    unittest.main()
