"""Tests for check_layers.py (stdlib only; run directly)."""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_layers

RULES = {
    "layers": {"core": ["app/core.py"], "io": ["app/io/"], "pkg": ["app/__init__.py"]},
    "allowed": {"core": [], "io": ["core"], "pkg": []},
}


def project(files: dict[str, str]) -> Path:
    root = Path(tempfile.mkdtemp())
    for name, text in {
        "app/__init__.py": "",
        "app/io/__init__.py": "",
        **files,
    }.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
    return root


class LayerTests(unittest.TestCase):
    def test_allowed_direction_passes(self) -> None:
        root = project(
            {"app/core.py": "X = 1\n", "app/io/db.py": "from app.core import X\n"}
        )
        self.assertEqual(check_layers.check(RULES, root), [])

    def test_forbidden_direction_is_reported_with_line(self) -> None:
        root = project(
            {"app/core.py": "\nimport app.io.db\n", "app/io/db.py": "Y = 2\n"}
        )
        problems = check_layers.check(RULES, root)
        self.assertEqual(len(problems), 1)
        self.assertIn("app/core.py:2: core imports io", problems[0])

    def test_unassigned_file_is_reported(self) -> None:
        root = project({"app/core.py": "", "app/stray.py": ""})
        self.assertIn("app/stray.py: in no layer", check_layers.check(RULES, root))

    def test_cycle_is_reported(self) -> None:
        root = project(
            {
                "app/core.py": "",
                "app/io/a.py": "import app.io.b\n",
                "app/io/b.py": "import app.io.a\n",
            }
        )
        problems = check_layers.check(RULES, root)
        self.assertTrue(any(p.startswith("import cycle") for p in problems), problems)

    def test_third_party_imports_are_ignored(self) -> None:
        root = project({"app/core.py": "import json\nimport sqlite3\n"})
        self.assertEqual(check_layers.check(RULES, root), [])


class MainTests(unittest.TestCase):
    def run_main(self, root: Path, rules: object, *flags: str) -> tuple[int, str, str]:
        (root / "layers.json").write_text(json.dumps(rules))
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            status = check_layers.main([str(root / "layers.json"), *flags])
        return status, out.getvalue(), err.getvalue()

    def test_json_lists_structured_violations(self) -> None:
        root = project(
            {"app/core.py": "\nimport app.io.db\n", "app/io/db.py": "", "app/x.py": ""}
        )
        status, out, _ = self.run_main(root, RULES, "--json")
        self.assertEqual(status, 1)
        report = json.loads(out)
        self.assertEqual(report["count"], 2)
        self.assertIn({"kind": "unassigned", "file": "app/x.py"}, report["violations"])
        self.assertIn(
            {
                "kind": "direction",
                "file": "app/core.py",
                "line": 2,
                "layer": "core",
                "imports_layer": "io",
                "target": "app/io/db.py",
                "allowed": [],
            },
            report["violations"],
        )

    def test_json_cycle_lists_files(self) -> None:
        root = project(
            {
                "app/core.py": "",
                "app/io/a.py": "import app.io.b\n",
                "app/io/b.py": "import app.io.a\n",
            }
        )
        report = json.loads(self.run_main(root, RULES, "--json")[1])
        cycles = [v for v in report["violations"] if v["kind"] == "cycle"]
        self.assertEqual(cycles[0]["files"][0], cycles[0]["files"][-1])

    def test_text_output_ends_with_count(self) -> None:
        root = project({"app/core.py": ""})
        status, out, _ = self.run_main(root, RULES)
        self.assertEqual((status, out), (0, "0 violation(s)\n"))

    def test_rules_without_layers_is_input_error(self) -> None:
        root = project({"app/core.py": ""})
        status, _, err = self.run_main(root, {"allowed": {}})
        self.assertEqual(status, 2)
        self.assertIn('needs a "layers" object', err)

    def test_unparsable_source_is_input_error(self) -> None:
        root = project({"app/core.py": "def broken(:\n"})
        status, _, err = self.run_main(root, RULES)
        self.assertEqual(status, 2)
        self.assertIn("cannot parse", err)


if __name__ == "__main__":
    unittest.main()
