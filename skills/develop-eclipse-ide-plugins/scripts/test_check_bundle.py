#!/usr/bin/env python3
"""Standalone tests for check_bundle.py (stdlib only)."""

from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_bundle import Report, check_bundle, main  # noqa: E402

EXAMPLE = Path(__file__).resolve().parent.parent / "assets/examples/plugin"

MANIFEST = """\
Manifest-Version: 1.0
Bundle-ManifestVersion: 2
Bundle-SymbolicName: org.acme.demo;singleton:=true
Bundle-Version: 1.0.0.qualifier
Bundle-RequiredExecutionEnvironment: JavaSE-21
Require-Bundle: org.eclipse.ui,
 org.eclipse.core.runtime
"""

BUILD = """\
source.. = src/
output.. = bin/
bin.includes = META-INF/,\\
               .,\\
               plugin.xml,\\
               icons/
"""

PLUGIN = """\
<?xml version="1.0" encoding="UTF-8"?>
<plugin>
  <extension id="task" point="org.eclipse.core.resources.markers">
    <super type="org.eclipse.core.resources.taskmarker"/>
  </extension>
  <extension id="sub" point="org.eclipse.core.resources.markers">
    <super type="org.acme.demo.task"/>
  </extension>
  <extension point="org.eclipse.ui.commands">
    <command id="org.acme.demo.run" name="Run"/>
  </extension>
  <extension point="org.eclipse.core.expressions.definitions">
    <definition id="org.acme.demo.one"><count value="1"/></definition>
  </extension>
  <extension point="org.eclipse.ui.handlers">
    <handler commandId="org.acme.demo.run" class="org.acme.demo.Run">
      <enabledWhen><reference definitionId="org.acme.demo.one"/></enabledWhen>
    </handler>
  </extension>
  <extension point="org.eclipse.ui.menus">
    <menuContribution locationURI="menu:edit?after=additions">
      <command commandId="org.acme.demo.run" icon="icons/run.png"/>
      <command commandId="org.eclipse.ui.file.refresh"/>
    </menuContribution>
  </extension>
</plugin>
"""


class CheckBundleTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name) / "org.acme.demo"
        self.write("META-INF/MANIFEST.MF", MANIFEST)
        self.write("build.properties", BUILD)
        self.write("plugin.xml", PLUGIN)
        self.write("src/org/acme/demo/Run.java", "class Run {}\n")
        self.write("icons/run.png", "")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, name: str, text: str) -> None:
        path = self.dir / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def replace(self, name: str, old: str, new: str) -> None:
        path = self.dir / name
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new), encoding="utf-8")

    def report(self) -> Report:
        report = Report()
        check_bundle(self.dir, report)
        return report

    def rules(self) -> set[str]:
        report = self.report()
        found = set()
        for line in report.errors + report.warnings:
            found.add(line.split("[", 1)[1].split("]", 1)[0])
        return found

    def test_valid_bundle_is_clean(self) -> None:
        report = self.report()
        self.assertEqual([], report.errors + report.warnings)

    def test_example_bundles_are_clean(self) -> None:
        for name in ("org.acme.todos", "org.acme.todos.tests"):
            report = Report()
            check_bundle(EXAMPLE / name, report)
            self.assertEqual([], report.errors + report.warnings, name)

    def test_m001_line_over_72_bytes(self) -> None:
        self.replace(
            "META-INF/MANIFEST.MF",
            "Require-Bundle: org.eclipse.ui,",
            "Require-Bundle: org.eclipse.ui,org.eclipse.core.resources,"
            "org.eclipse.jface,",
        )
        self.assertEqual({"M001"}, self.rules())

    def test_m001_counts_utf8_bytes_not_characters(self) -> None:
        # 36 two-byte characters: 36 characters but 72 bytes + header.
        self.replace(
            "META-INF/MANIFEST.MF",
            "Manifest-Version: 1.0\n",
            "Manifest-Version: 1.0\nBundle-Name: " + "é" * 36 + "\n",
        )
        self.assertEqual({"M001"}, self.rules())

    def test_m002_missing_final_newline(self) -> None:
        self.replace(
            "META-INF/MANIFEST.MF",
            " org.eclipse.core.runtime\n",
            " org.eclipse.core.runtime",
        )
        self.assertEqual({"M002"}, self.rules())

    def test_m003_unindented_continuation(self) -> None:
        self.replace(
            "META-INF/MANIFEST.MF",
            "\n org.eclipse.core.runtime",
            "\norg.eclipse.core.runtime",
        )
        self.assertEqual({"M003"}, self.rules())

    def test_m004_two_space_continuation_warns(self) -> None:
        self.replace(
            "META-INF/MANIFEST.MF",
            "\n org.eclipse.core.runtime",
            "\n  org.eclipse.core.runtime",
        )
        report = self.report()
        self.assertEqual([], report.errors)
        self.assertEqual({"M004"}, self.rules())

    def test_m005_blank_line_in_main_section(self) -> None:
        self.replace(
            "META-INF/MANIFEST.MF", "Bundle-ManifestVersion", "\nBundle-ManifestVersion"
        )
        self.assertIn("M005", self.rules())

    def test_m006_manifest_version(self) -> None:
        self.replace(
            "META-INF/MANIFEST.MF",
            "Bundle-ManifestVersion: 2",
            "Bundle-ManifestVersion: 1",
        )
        self.assertEqual({"M006"}, self.rules())

    def test_m007_missing_symbolic_name(self) -> None:
        self.replace(
            "META-INF/MANIFEST.MF",
            "Bundle-SymbolicName: org.acme.demo;singleton:=true\n",
            "",
        )
        self.assertIn("M007", self.rules())

    def test_m008_bad_version(self) -> None:
        self.replace("META-INF/MANIFEST.MF", "1.0.0.qualifier", "1.0.0-SNAPSHOT")
        self.assertEqual({"M008"}, self.rules())

    def test_m009_extensions_need_singleton(self) -> None:
        self.replace("META-INF/MANIFEST.MF", ";singleton:=true", "")
        self.assertEqual({"M009"}, self.rules())

    def test_m009_not_needed_without_plugin_xml(self) -> None:
        self.replace("META-INF/MANIFEST.MF", ";singleton:=true", "")
        (self.dir / "plugin.xml").unlink()
        self.replace("build.properties", "               plugin.xml,\\\n", "")
        self.assertEqual(set(), self.rules())

    def test_m010_bree_and_osgi_ee(self) -> None:
        self.replace(
            "META-INF/MANIFEST.MF",
            "Require-Bundle",
            'Require-Capability: osgi.ee;filter:="(osgi.ee=JavaSE)"\nRequire-Bundle',
        )
        self.assertEqual({"M010"}, self.rules())

    def test_b001_missing_bin_includes(self) -> None:
        self.write("build.properties", "source.. = src/\n")
        self.assertEqual({"B001"}, self.rules())

    def test_b002_b003_b004_missing_entries(self) -> None:
        self.write("build.properties", "source.. = src/\nbin.includes = icons/\n")
        self.assertEqual({"B002", "B003", "B004"}, self.rules())

    def test_b005_comma_without_backslash(self) -> None:
        self.write(
            "build.properties",
            "source.. = src/\n"
            "bin.includes = META-INF/,\n"
            "               .,\n"
            "               plugin.xml,\n"
            "               icons/\n",
        )
        self.assertIn("B005", self.rules())

    def test_b006_sources_without_source_entry(self) -> None:
        self.replace("build.properties", "source.. = src/\n", "")
        self.assertEqual({"B006"}, self.rules())

    def test_b007_icon_not_packaged(self) -> None:
        self.replace("build.properties", ",\\\n               icons/", "")
        self.assertEqual({"B007"}, self.rules())

    def test_x001_malformed_xml(self) -> None:
        self.write("plugin.xml", "<plugin><extension></plugin>")
        self.assertEqual({"X001"}, self.rules())

    def test_x002_undeclared_own_command_is_error(self) -> None:
        self.replace(
            "plugin.xml",
            '<handler commandId="org.acme.demo.run"',
            '<handler commandId="org.acme.demo.runn"',
        )
        self.assertEqual({"X002"}, self.rules())
        self.assertEqual(1, len(self.report().errors))

    def test_x002_foreign_command_is_warning(self) -> None:
        self.replace(
            "plugin.xml",
            'commandId="org.eclipse.ui.file.refresh"',
            'commandId="com.other.cmd"',
        )
        report = self.report()
        self.assertEqual([], report.errors)
        self.assertEqual({"X002"}, self.rules())

    def test_x003_bad_location_uri(self) -> None:
        self.replace("plugin.xml", "menu:edit?after=additions", "edit/additions")
        self.assertEqual({"X003"}, self.rules())

    def test_x004_undeclared_definition(self) -> None:
        self.replace(
            "plugin.xml",
            'definitionId="org.acme.demo.one"',
            'definitionId="org.acme.demo.two"',
        )
        self.assertEqual({"X004"}, self.rules())

    def test_x005_class_without_source(self) -> None:
        self.replace(
            "plugin.xml", 'class="org.acme.demo.Run"', 'class="org.acme.demo.Missing"'
        )
        self.assertEqual({"X005"}, self.rules())

    def test_x006_duplicate_command(self) -> None:
        self.replace(
            "plugin.xml",
            '<command id="org.acme.demo.run" name="Run"/>',
            '<command id="org.acme.demo.run" name="Run"/>'
            '<command id="org.acme.demo.run" name="Again"/>',
        )
        self.assertEqual({"X006"}, self.rules())

    def test_x007_undeclared_marker_super_type(self) -> None:
        self.replace(
            "plugin.xml", 'type="org.acme.demo.task"', 'type="org.acme.demo.tsk"'
        )
        self.assertEqual({"X007"}, self.rules())

    def test_main_exit_codes(self) -> None:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(0, main([str(self.dir)]))
            self.replace("META-INF/MANIFEST.MF", ";singleton:=true", "")
            self.assertEqual(1, main([str(self.dir)]))
            self.assertEqual(2, main([str(self.dir / "missing")]))
            self.assertEqual(2, main([]))

    def test_main_json_report(self) -> None:
        self.replace("META-INF/MANIFEST.MF", ";singleton:=true", "")
        out = io.StringIO()
        with redirect_stdout(out):
            status = main(["--json", str(self.dir)])
        report = json.loads(out.getvalue())
        self.assertEqual(1, status)
        self.assertEqual((1, 0), (report["errors"], report["warnings"]))
        (finding,) = report["findings"]
        self.assertEqual(("error", "M009"), (finding["level"], finding["rule"]))
        self.assertTrue(finding["file"].endswith("MANIFEST.MF"), finding["file"])

    def test_main_help_documents_exit_status(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            self.assertEqual(0, main(["--help"]))
        self.assertIn("Exit status:", out.getvalue())
        self.assertIn("Examples:", out.getvalue())

    def test_copy_of_example_detects_removed_singleton(self) -> None:
        copy = Path(self.tmp.name) / "copy"
        shutil.copytree(EXAMPLE / "org.acme.todos", copy)
        manifest = copy / "META-INF/MANIFEST.MF"
        text = manifest.read_text(encoding="utf-8")
        manifest.write_text(text.replace(";singleton:=true", ""), "utf-8")
        report = Report()
        check_bundle(copy, report)
        self.assertEqual(1, len(report.errors))
        self.assertIn("[M009]", report.errors[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
