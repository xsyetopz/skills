"""Tests for check_cli.py (stdlib only; run directly)."""

from __future__ import annotations

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_cli as cc

# A well-behaved program: help on stdout, usage errors on stderr with exit 2.
GOOD = r"""
import sys
a = sys.argv[1:]
if a[:1] in (["--help"], ["-h"]) or a[1:2] == ["--help"]:
    print("usage: good [--help] COMMAND"); sys.exit(0)
if a == ["--version"]:
    print("good 1.0"); sys.exit(0)
if a and a[0].startswith("-"):
    print(f"good: unknown option {a[0]}", file=sys.stderr); sys.exit(2)
print("usage: good COMMAND", file=sys.stderr); sys.exit(2)
"""


def program(source: str) -> list[str]:
    return [sys.executable, "-c", source]


def probes(source: str, **kwargs) -> set[str]:
    found = cc.check(
        program(source), kwargs.get("subs", []), kwargs.get("skip", set()), 2.0
    )
    return {f.probe for f in found}


class CheckTests(unittest.TestCase):
    def test_well_behaved_program_is_clean(self) -> None:
        self.assertEqual(probes(GOOD, subs=["add"]), set())

    def test_unknown_flag_accepted_silently(self) -> None:
        source = GOOD.replace(
            'print(f"good: unknown option {a[0]}", file=sys.stderr); sys.exit(2)',
            'print(f"good: unknown option {a[0]}"); sys.exit(0)',
        )
        self.assertNotEqual(source, GOOD)
        self.assertEqual(probes(source), {"unknown-flag"})

    def test_help_on_stderr(self) -> None:
        source = GOOD.replace(
            'print("usage: good [--help] COMMAND")',
            'print("usage: good [--help] COMMAND", file=sys.stderr)',
        )
        self.assertIn("help-long", probes(source))

    def test_color_in_pipe(self) -> None:
        source = GOOD.replace('"good 1.0"', '"\\x1b[1mgood\\x1b[0m 1.0"')
        self.assertEqual(probes(source), {"ansi-when-piped"})

    def test_stack_trace(self) -> None:
        source = GOOD.replace(
            'print("usage: good COMMAND", file=sys.stderr); sys.exit(2)',
            "input()",
        )
        self.assertIn("stack-trace", probes(source, skip={"bare-terminal"}))

    def test_hang_without_input(self) -> None:
        source = GOOD.replace(
            'print("usage: good COMMAND", file=sys.stderr); sys.exit(2)',
            "import time; time.sleep(30)",
        )
        found = probes(source, skip={"bare-terminal"})
        self.assertIn("bare-noninteractive", found)

    def test_skip_removes_probe(self) -> None:
        source = GOOD.replace('"good 1.0"', '"\\x1b[1mgood\\x1b[0m 1.0"')
        self.assertEqual(probes(source, skip={"ansi-when-piped"}), set())

    def test_help_without_usage_line_warns(self) -> None:
        source = GOOD.replace('"usage: good [--help] COMMAND"', '"good: does things"')
        found = cc.check(program(source), [], set(), 2.0)
        self.assertEqual(
            {(f.probe, f.severity) for f in found}, {("help-usage", "warning")}
        )


class MainTests(unittest.TestCase):
    def test_exit_codes(self) -> None:
        with open(os.devnull, "w") as sink:
            stdout, stderr = sys.stdout, sys.stderr
            sys.stdout = sys.stderr = sink
            try:
                self.assertEqual(cc.main(["--", *program(GOOD)]), 0)
                bad = GOOD.replace('"good 1.0"', '"\\x1b[1mgood\\x1b[0m"')
                self.assertEqual(cc.main(["--", *program(bad)]), 1)
                self.assertEqual(cc.main(["--", "/nonexistent/cli-check"]), 2)
                with self.assertRaises(SystemExit) as usage:
                    cc.main([])
                self.assertEqual(usage.exception.code, 2)
            finally:
                sys.stdout, sys.stderr = stdout, stderr


if __name__ == "__main__":
    unittest.main()
