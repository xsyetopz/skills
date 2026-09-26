#!/usr/bin/env python3
"""Standalone tests for check_plugin_xml.py (stdlib only)."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_plugin_xml import check, main

EXAMPLE = Path(__file__).resolve().parent.parent / "assets/examples/plugin"

VALID = """\
<idea-plugin>
  <id>com.acme.demo</id>
  <name>Demo</name>
  <vendor>Acme</vendor>
  <version>1.0.0</version>
  <description>Demo plugin.</description>
  <idea-version since-build="252" until-build="262.*"/>
  <depends>com.intellij.modules.platform</depends>
  <extensionPoints>
    <extensionPoint name="probe" interface="com.acme.demo.Probe"
                    dynamic="true"/>
  </extensionPoints>
  <extensions defaultExtensionNs="com.acme.demo">
    <probe implementation="com.acme.demo.DefaultProbe"/>
  </extensions>
  <actions>
    <group id="com.acme.demo.Group" text="Demo">
      <action id="com.acme.demo.Run" class="com.acme.demo.RunAction"
              text="Run"/>
    </group>
  </actions>
</idea-plugin>
"""


class CheckPluginXmlTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, text: str, name: str = "plugin.xml") -> Path:
        path = self.dir / name
        path.write_text(text, encoding="utf-8")
        return path

    def errors(self, text: str, patched: bool = True) -> list[str]:
        return check([self.write(text)], patched, []).errors

    def test_valid_descriptor_has_no_findings(self) -> None:
        report = check([self.write(VALID)], True, [])
        self.assertEqual([], report.errors)
        self.assertEqual([], report.warnings)

    def test_since_build_wildcard_is_rejected(self) -> None:
        text = VALID.replace('since-build="252"', 'since-build="252.*"')
        self.assertIn("since-build '252.*'", self.errors(text)[0])

    def test_until_before_since_is_rejected(self) -> None:
        text = VALID.replace('until-build="262.*"', 'until-build="251.*"')
        self.assertIn("until-build 251.* is before 252", self.errors(text)[0])

    def test_strict_until_build_before_since_is_rejected(self) -> None:
        text = VALID.replace('until-build="262.*"', 'strict-until-build="251.*"')
        self.assertIn("strict-until-build 251.* is before 252", self.errors(text)[0])

    def test_patchable_elements_are_errors_only_when_patched(self) -> None:
        text = VALID.replace("  <version>1.0.0</version>\n", "")
        self.assertIn("missing <version>", self.errors(text)[0])
        self.assertEqual([], self.errors(text, patched=False))

    def test_forbidden_id_prefix_and_product_word(self) -> None:
        text = VALID.replace("<id>com.acme.demo</id>", "<id>com.example.demo</id>")
        self.assertIn("prefix 'com.example' is rejected", self.errors(text)[0])
        text = VALID.replace("<id>com.acme.demo</id>", "<id>com.acme.pycharm</id>")
        self.assertIn("product word 'pycharm'", self.errors(text)[0])

    def test_duplicate_action_id_is_rejected(self) -> None:
        text = VALID.replace('id="com.acme.demo.Run"', 'id="com.acme.demo.Group"')
        self.assertIn("duplicate action/group id", self.errors(text)[0])

    def test_group_without_id_is_rejected(self) -> None:
        text = VALID.replace('<group id="com.acme.demo.Group"', "<group")
        self.assertIn("<group> without id", self.errors(text)[0])

    def test_action_without_text_needs_bundle(self) -> None:
        text = VALID.replace('\n              text="Run"', "")
        self.assertIn("no text and no resource bundle", self.errors(text)[0])
        bundled = text.replace("<actions>", '<actions resource-bundle="messages.B">')
        self.assertEqual([], self.errors(bundled))

    def test_optional_depends_needs_existing_config_file(self) -> None:
        dep = "<depends>com.intellij.modules.platform</depends>"
        text = VALID.replace(
            dep, dep + '\n<depends optional="true">com.intellij.modules.json</depends>'
        )
        self.assertIn("has no config-file", self.errors(text)[0])
        text = text.replace(
            'optional="true"',
            'optional="true" config-file="com.acme.demo-withJson.xml"',
        )
        self.assertIn("does not exist", self.errors(text)[0])
        self.write("<idea-plugin/>", "com.acme.demo-withJson.xml")
        self.assertEqual([], self.errors(text))

    def test_undeclared_own_extension_point_is_rejected(self) -> None:
        text = VALID.replace("<probe ", "<prob ")
        self.assertIn(
            "undeclared extension point com.acme.demo.prob", self.errors(text)[0]
        )

    def test_interface_point_requires_implementation(self) -> None:
        text = VALID.replace('implementation="com.acme.demo.DefaultProbe"', 'key="x"')
        self.assertIn("has no implementation attribute", self.errors(text)[0])

    def test_non_dynamic_point_is_a_warning(self) -> None:
        text = VALID.replace('\n                    dynamic="true"', "")
        report = check([self.write(text)], True, [])
        self.assertEqual([], report.errors)
        self.assertIn("is not dynamic", report.warnings[0])

    def test_unresolved_class_is_rejected_with_src_root(self) -> None:
        src = self.dir / "src"
        package = src / "com/acme/demo"
        package.mkdir(parents=True)
        (package / "Probes.kt").write_text(
            "package com.acme.demo\n\ninterface Probe\nclass DefaultProbe : Probe\n",
            encoding="utf-8",
        )
        text = VALID.replace(
            "</idea-plugin>",
            '<applicationListeners><listener class="com.acme.demo.RunAction" '
            'topic="org.jetbrains.kotlin.SomeTopic"/></applicationListeners>'
            "</idea-plugin>",
        )
        report = check([self.write(text)], True, [src])
        self.assertEqual(
            [
                f"ERROR {self.dir / 'plugin.xml'}: class com.acme.demo.RunAction "
                "has no source file"
            ],
            report.errors,
        )

    def test_bundled_example_descriptor_is_clean(self) -> None:
        main = EXAMPLE / "src/main"
        report = check(
            [main / "resources/META-INF/plugin.xml"],
            False,
            [main / "kotlin", main / "java"],
        )
        self.assertEqual([], report.errors)

    def test_json_report(self) -> None:
        text = VALID.replace("<vendor>Acme</vendor>", "")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plugin.xml"
            path.write_text(text)
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                status = main(["--json", str(path)])
        report = json.loads(out.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual(report["descriptors"], 1)
        self.assertEqual(report["errors"], len(report["findings"]))
        self.assertEqual(report["findings"][0]["level"], "error")
        self.assertEqual(report["findings"][0]["file"], str(path))
        self.assertIn("vendor", report["findings"][0]["message"])

    def test_unparsable_descriptor_is_input_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "plugin.xml"
            path.write_text("<idea-plugin>")
            err = io.StringIO()
            with contextlib.redirect_stderr(err):
                self.assertEqual(main([str(path)]), 2)
        self.assertIn("well-formed", err.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
