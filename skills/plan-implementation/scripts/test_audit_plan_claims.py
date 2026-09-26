"""Tests for audit_plan_claims.py (stdlib only; run directly)."""

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

import audit_plan_claims as apc


def repo_with_files(root: Path) -> Path:
    (root / "src").mkdir()
    (root / "src" / "config.py").write_text("")
    (root / "tests").mkdir()
    (root / "tests" / "test_config.py").write_text("")
    (root / "package.json").write_text(json.dumps({"scripts": {"lint": "x"}}))
    (root / "Makefile").write_text("build:\n\techo build\n")
    return root


class AuditTests(unittest.TestCase):
    def statuses(self, plan: str) -> dict[str, str]:
        with tempfile.TemporaryDirectory() as tmp:
            repo = repo_with_files(Path(tmp))
            return {c.text: c.status for c in apc.audit(plan, repo)}

    def test_existing_and_missing_paths(self) -> None:
        result = self.statuses(
            "- T1 [files: src/config.py, src/missing.py] Edit `src/config.py`.\n"
        )
        self.assertEqual(result["src/config.py"], "ok")
        self.assertEqual(result["src/missing.py"], "missing")

    def test_new_file_marker(self) -> None:
        result = self.statuses("- T2 Create `src/new_module.py` with the parser.\n")
        self.assertEqual(result["src/new_module.py"], "ok")

    def test_package_scripts_make_targets_and_test_modules(self) -> None:
        plan = (
            "  Verify: `npm run lint`\n"
            "  Verify: `npm run typecheck`\n"
            "  Verify: `make build`\n"
            "  Verify: `make deploy`\n"
            "  Verify: `python3 -m unittest tests.test_config`\n"
            "  Verify: `python3 -m unittest tests.test_absent`\n"
        )
        result = self.statuses(plan)
        self.assertEqual(result["npm run lint"], "ok")
        self.assertEqual(result["npm run typecheck"], "missing")
        self.assertEqual(result["make build"], "ok")
        self.assertEqual(result["make deploy"], "missing")
        self.assertEqual(result["python3 -m unittest tests.test_config"], "ok")
        self.assertEqual(result["python3 -m unittest tests.test_absent"], "missing")

    def test_fenced_commands_and_unknown_program(self) -> None:
        plan = "```sh\n# comment\nnot-a-real-tool-xyz --check\n```\n"
        result = self.statuses(plan)
        self.assertEqual(result["not-a-real-tool-xyz --check"], "missing")

    def test_unittest_discover_option_values_are_not_modules(self) -> None:
        plan = (
            "  Verify: `python3 -m unittest discover -s tests -t .`\n"
            "  Verify: `python3 -m pip install -e .`\n"
            "  Verify: `python3 -m pytest -p no:cacheprovider tests/test_config.py`\n"
        )
        result = self.statuses(plan)
        self.assertEqual(result["python3 -m unittest discover -s tests -t ."], "ok")
        self.assertEqual(result["python3 -m pip install -e ."], "ok")
        self.assertEqual(
            result["python3 -m pytest -p no:cacheprovider tests/test_config.py"],
            "ok",
        )

    def test_discover_start_directory_must_exist(self) -> None:
        plan = (
            "  Verify: `python3 -m unittest discover -s tests -t .`\n"
            "  Verify: `python3 -m unittest discover -s missing_dir`\n"
            "  Verify: `python3 -m unittest discover missing_positional`\n"
            "  Verify: `python3 -m unittest discover -v`\n"
        )
        result = self.statuses(plan)
        self.assertEqual(result["python3 -m unittest discover -s tests -t ."], "ok")
        self.assertEqual(
            result["python3 -m unittest discover -s missing_dir"], "missing"
        )
        self.assertEqual(
            result["python3 -m unittest discover missing_positional"], "missing"
        )
        self.assertEqual(result["python3 -m unittest discover -v"], "ok")

    def test_invalid_package_json_is_unknown_not_a_crash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = repo_with_files(Path(tmp))
            (repo / "package.json").write_text("{not json")
            (claim,) = apc.audit("  Verify: `npm run lint`\n", repo)
        self.assertEqual(
            (claim.status, claim.detail),
            ("unknown", "package.json is not a JSON object"),
        )

    def test_dotted_test_names_resolve_to_module_files(self) -> None:
        plan = (
            "  Verify: `python3 -m unittest tests.test_config.ConfigTests.test_x`\n"
            "  Verify: `python3 -m unittest -k slow tests.test_absent.Case`\n"
            "  Verify: `python3 -m pytest tests/test_config.py::test_x`\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = repo_with_files(Path(tmp))
            claims = {c.text: c for c in apc.audit(plan, repo)}
        name = "python3 -m unittest tests.test_config.ConfigTests.test_x"
        self.assertEqual(claims[name].status, "ok")
        absent = claims["python3 -m unittest -k slow tests.test_absent.Case"]
        self.assertEqual(absent.status, "missing")
        self.assertEqual(absent.detail, "test module tests.test_absent.Case")
        pytest_node = "python3 -m pytest tests/test_config.py::test_x"
        self.assertEqual(claims[pytest_node].status, "ok")

    def test_each_path_is_reported_once(self) -> None:
        plan = (
            "- T1 [files: src/config.py] Edit `src/config.py`.\n"
            "- T2 Edit `src/config.py` again.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = repo_with_files(Path(tmp))
            paths = [c for c in apc.audit(plan, repo) if c.kind == "path"]
        self.assertEqual([(c.text, c.line) for c in paths], [("src/config.py", 1)])

    def test_path_created_by_one_task_and_used_by_another(self) -> None:
        plan = (
            "- T1 Create `src/new_module.py` with the parser.\n"
            "- T2 Call the parser from `src/new_module.py`.\n"
        )
        with tempfile.TemporaryDirectory() as tmp:
            repo = repo_with_files(Path(tmp))
            claims = apc.audit(plan, repo)
        self.assertEqual(
            [(c.text, c.status, c.detail) for c in claims],
            [("src/new_module.py", "ok", "marked new")],
        )

    def test_json_output_and_exit_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "repo").mkdir()
            repo = repo_with_files(root / "repo")
            plan = root / "plan.md"
            plan.write_text("- T1 [files: src/config.py, src/gone.py] Edit.\n")
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = apc.main([str(plan), str(repo), "--json"])
        self.assertEqual(status, 1)
        self.assertEqual(
            json.loads(out.getvalue()),
            [
                {"kind": "path", "text": "src/config.py", "line": 1,
                 "status": "ok", "detail": ""},
                {"kind": "path", "text": "src/gone.py", "line": 1,
                 "status": "missing", "detail": "not in repo"},
            ],
        )  # fmt: skip

    def test_bad_repo_is_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            plan = Path(tmp) / "plan.md"
            plan.write_text("x\n")
            self.assertEqual(apc.main([str(plan), "/nonexistent-dir"]), 2)


if __name__ == "__main__":
    unittest.main()
