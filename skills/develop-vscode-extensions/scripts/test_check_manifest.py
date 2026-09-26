"""Tests for check_manifest.py. Run: python test_check_manifest.py"""

from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from typing import Any, Callable

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import check_manifest  # noqa: E402

FIXTURE = HERE.parent / "assets/examples/extension"
BASE: dict[str, Any] = json.loads((FIXTURE / "package.json").read_text())


def run(
    mutate: Callable[[dict[str, Any]], None] | None = None,
    *,
    source: str | None = None,
    built: bool = False,
    pre_release: bool = False,
) -> list[str]:
    manifest = copy.deepcopy(BASE)
    if mutate:
        mutate(manifest)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "package.json"
        path.write_text(json.dumps(manifest))
        sources: list[Path] = []
        if source is not None:
            (Path(tmp) / "src").mkdir()
            (Path(tmp) / "src/extension.ts").write_text(source)
            sources.append(Path(tmp) / "src")
        report = check_manifest.check(path, sources, built, pre_release)
    return report.lines


def rules(lines: list[str]) -> set[str]:
    return {line.split()[0] for line in lines}


def setting(m: dict[str, Any], key: str, schema: dict[str, Any]) -> None:
    m["contributes"]["configuration"]["properties"][key] = schema


class FixtureIsClean(unittest.TestCase):
    def test_fixture_has_no_findings(self) -> None:
        self.assertEqual(run(source=_fixture_sources()), [])


def _fixture_sources() -> str:
    return "\n".join(p.read_text() for p in sorted((FIXTURE / "src").rglob("*.ts")))


class EachRuleFires(unittest.TestCase):
    def assertRule(self, rule: str, lines: list[str]) -> None:
        self.assertIn(rule, rules(lines), lines)

    def test_m001_missing_publisher(self) -> None:
        self.assertRule("M001", run(lambda m: m.pop("publisher")))

    def test_m001_missing_engines(self) -> None:
        self.assertRule("M001", run(lambda m: m.pop("engines")))

    def test_m002_star_engine(self) -> None:
        self.assertRule("M002", run(lambda m: m["engines"].update(vscode="*")))

    def test_m003_uppercase_name(self) -> None:
        self.assertRule("M003", run(lambda m: m.update(name="Todo Owner")))

    def test_m004_semver_prerelease_tag(self) -> None:
        self.assertRule("M004", run(lambda m: m.update(version="1.0.0-rc.1")))

    def test_m005_too_many_keywords(self) -> None:
        words = [f"k{i}" for i in range(31)]
        self.assertRule("M005", run(lambda m: m.update(keywords=words)))

    def test_m006_svg_icon(self) -> None:
        self.assertRule("M006", run(lambda m: m.update(icon="icon.svg")))

    def test_m007_unknown_category(self) -> None:
        self.assertRule("M007", run(lambda m: m.update(categories=["Tools"])))

    def test_m008_setting_prefix(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            setting(m, "todoOwner.enable.fast", {"type": "boolean"})

        self.assertRule("M008", run(mutate))

    def test_m009_unknown_scope(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            setting(m, "todoOwner.x", {"type": "string", "scope": "user"})

        self.assertRule("M009", run(mutate))

    def test_m010_ref_in_schema(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            setting(m, "todoOwner.x", {"$ref": "#/definitions/x"})

        self.assertRule("M010", run(mutate))

    def test_m011_limited_without_description(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            m["capabilities"]["untrustedWorkspaces"].pop("description")

        self.assertRule("M011", run(mutate))

    def test_m011_bad_supported_value(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            m["capabilities"]["untrustedWorkspaces"]["supported"] = "partial"

        self.assertRule("M011", run(mutate))

    def test_m012_restricted_setting_not_declared(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            trust = m["capabilities"]["untrustedWorkspaces"]
            trust["restrictedConfigurations"] = ["todoOwner.missing"]

        self.assertRule("M012", run(mutate))

    def test_m013_virtual_without_description(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            m["capabilities"]["virtualWorkspaces"] = {"supported": "limited"}

        self.assertRule("M013", run(mutate))

    def test_m014_menu_references_unknown_command(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            palette = m["contributes"]["menus"]["commandPalette"]
            palette.append({"command": "todoOwner.typo", "when": "true"})

        self.assertRule("M014", run(mutate))

    def test_m015_contributed_but_not_registered(self) -> None:
        source = _fixture_sources().replace('"todoOwner.showLog"', '"x"')
        self.assertRule("M015", run(source=source))

    def test_m016_old_floor_needs_on_command(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            m["engines"]["vscode"] = "^1.73.0"
            m["devDependencies"]["@types/vscode"] = "1.73.1"

        self.assertRule("M016", run(mutate))

    def test_m016_satisfied_by_explicit_events(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            m["engines"]["vscode"] = "^1.73.0"
            m["devDependencies"]["@types/vscode"] = "1.73.1"
            m["activationEvents"] = [
                f"onCommand:{c['command']}" for c in m["contributes"]["commands"]
            ]

        self.assertNotIn("M016", rules(run(mutate)))

    def test_m017_star_activation_is_a_warning(self) -> None:
        lines = run(lambda m: m.update(activationEvents=["*"]))
        self.assertIn(
            "M017 warning: `*` activates at startup; use a specific event", lines
        )

    def test_m018_missing_bundle(self) -> None:
        self.assertRule("M018", run(built=True))

    def test_m019_pre_release_needs_1_63(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            m["engines"]["vscode"] = "^1.60.0"
            m["devDependencies"]["@types/vscode"] = "1.60.0"

        self.assertRule("M019", run(mutate, pre_release=True))

    def test_m020_types_newer_than_engine(self) -> None:
        def mutate(m: dict[str, Any]) -> None:
            m["devDependencies"]["@types/vscode"] = "^1.138.0"

        self.assertRule("M020", run(mutate))

    def test_m021_missing_trust_declaration_warns(self) -> None:
        lines = run(lambda m: m["capabilities"].pop("untrustedWorkspaces"))
        self.assertIn("M021", rules(lines))


class CommandLine(unittest.TestCase):
    def test_exit_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            good = Path(tmp) / "package.json"
            good.write_text(json.dumps(BASE))
            bad = Path(tmp) / "bad.json"
            bad.write_text(json.dumps({**BASE, "version": "1.0"}))
            broken = Path(tmp) / "broken.json"
            broken.write_text("{")
            out = io.StringIO()
            with redirect_stdout(out):
                self.assertEqual(check_manifest.main([str(good)]), 0)
                self.assertEqual(check_manifest.main([str(bad)]), 1)
            self.assertIn("0 error(s), 0 warning(s)", out.getvalue())
            self.assertIn("M004 error", out.getvalue())
            with redirect_stdout(io.StringIO()):
                self.assertEqual(check_manifest.main([str(broken)]), 2)

    def test_json_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "package.json"
            bad.write_text(json.dumps({**BASE, "version": "1.0"}))
            out = io.StringIO()
            with redirect_stdout(out):
                status = check_manifest.main([str(bad), "--json"])
        report = json.loads(out.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(report["errors"], 1)
        self.assertEqual(report["warnings"], 0)
        (finding,) = report["findings"]
        self.assertEqual((finding["rule"], finding["level"]), ("M004", "error"))
        self.assertEqual(finding["source"], check_manifest.RULES["M004"])
        self.assertIn("1.0", finding["message"])

    def test_every_rule_has_a_source(self) -> None:
        for rule, url in check_manifest.RULES.items():
            self.assertTrue(url.startswith("https://"), rule)


if __name__ == "__main__":
    unittest.main()
