"""Tests for layout_smells.py (stdlib only; run directly)."""

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

import layout_smells


def run(argv: list[str]) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            status = layout_smells.main(argv)
        except SystemExit as error:
            status = error.code
    return int(status or 0), out.getvalue()


class WordTests(unittest.TestCase):
    def test_separators_and_camel_case(self) -> None:
        self.assertEqual(
            layout_smells.words("cart-item_price.x y"),
            ("cart", "item", "price", "x", "y"),
        )
        self.assertEqual(layout_smells.words("HTTPServer"), ("http", "server"))
        self.assertEqual(layout_smells.words("apiV2"), ("api", "v", "2"))
        self.assertEqual(layout_smells.words("cart-item2"), ("cart", "item", "2"))

    def test_go_build_suffixes_are_stripped(self) -> None:
        stem = layout_smells.stem_of
        self.assertEqual(stem(Path("poll_linux.go")), "poll")
        self.assertEqual(stem(Path("poll_linux_amd64.go")), "poll")
        self.assertEqual(stem(Path("poll_arm64.go")), "poll")
        self.assertEqual(stem(Path("poll_linux.py")), "poll_linux")
        self.assertEqual(stem(Path("linux.go")), "linux")


class LayoutTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def touch(self, *names: str) -> None:
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("x\n")

    def findings(self, *extra: str) -> list[tuple[str, str, str]]:
        _, out = run([str(self.root), "--json", *extra])
        prefix = self.root.as_posix() + "/"
        return [
            (f["kind"], f["path"].removeprefix(prefix), f["detail"])
            for f in json.loads(out)["findings"]
        ]

    def kinds(self, *extra: str) -> list[tuple[str, str]]:
        return [(kind, path) for kind, path, _ in self.findings(*extra)]

    def test_nested_prefix_groups(self) -> None:
        names = (
            "cart",
            "cart-item",
            "cart-item2",
            "cart-item-price",
            "cart-item-price2",
        )
        self.touch(*(f"checkout/{n}.ts" for n in names))
        groups = [d for k, _, d in self.findings() if k == "prefix-group"]
        self.assertEqual(len(groups), 2)
        self.assertTrue(groups[0].startswith('prefix "cart" shared by 5 names'))
        self.assertTrue(groups[1].startswith('prefix "cart-item" shared by 4 names'))

    def test_prefix_group_reports_only_longest_prefix_for_same_names(self) -> None:
        self.touch(
            "billing/invoice-line-tax.py",
            "billing/invoice-line-total.py",
            "billing/invoice-line-discount.py",
        )
        details = [d for k, _, d in self.findings() if k == "prefix-group"]
        self.assertEqual(len(details), 1)
        self.assertIn('prefix "invoice-line" shared by 3', details[0])

    def test_prefix_group_counts_distinct_stems(self) -> None:
        self.touch("w/widget.ts", "w/widget.css", "w/widget.html", "w/widget.spec.ts")
        self.assertEqual(self.kinds(), [])
        self.touch("w/other-a.ts", "w/other-b.ts")
        self.assertEqual(self.kinds(), [])
        self.assertEqual(self.kinds("--min-group", "2"), [("prefix-group", "w")])

    def test_numbered_siblings(self) -> None:
        self.touch("a/file1.py", "a/file2.py", "a/handler.go", "a/handler_v2.go")
        self.touch("a/api.ts", "a/apiV2.ts")
        self.assertEqual(
            self.kinds(),
            [
                ("numbered-sibling", "a/apiV2.ts"),
                ("numbered-sibling", "a/file1.py"),
                ("numbered-sibling", "a/file2.py"),
                ("numbered-sibling", "a/handler_v2.go"),
            ],
        )

    def test_lone_number_is_not_a_sibling(self) -> None:
        self.touch("a/sha256.py", "a/http2.go", "a/page1.ts", "a/page1.css")
        self.assertEqual(self.kinds(), [])

    def test_leftover_markers_and_backup_suffixes(self) -> None:
        self.touch(
            "a/parser_old.py",
            "a/report-final2.ts",
            "a/Copy of notes.txt",
            "a/main.c~",
            "a/main.c.orig",
            "a/main.c.bak",
        )
        found = {path: detail for _, path, detail in self.findings()}
        self.assertEqual(len(found), 6)
        self.assertIn('"old"', found["a/parser_old.py"])
        self.assertIn('"final"', found["a/report-final2.ts"])
        self.assertIn('"copy of"', found["a/Copy of notes.txt"])
        self.assertIn("backup suffix", found["a/main.c~"])

    def test_generic_files_and_directories(self) -> None:
        self.touch(
            "src/utils.py", "src/helpers.ts", "src/common_types.go", "src/misc/x.py"
        )
        self.touch("src/user_types.ts")
        self.assertEqual(
            self.kinds(),
            [
                ("generic-name", "src/common_types.go"),
                ("generic-name", "src/helpers.ts"),
                ("generic-name", "src/misc"),
                ("generic-name", "src/utils.py"),
            ],
        )

    def test_conventional_and_feature_names_are_not_findings(self) -> None:
        self.touch("crate/src/lib.rs", "app/lib/x.rb", "ops/db_backup.py")
        self.touch("ops/cache_temp.go", "core/base.py", "core/task_manager.py")
        self.assertEqual(self.kinds(), [])

    def test_stutter_but_not_exact_match(self) -> None:
        self.touch("http/http_server.go", "billing/billingService.ts")
        self.touch("hero-list/hero-list.component.ts", "widget/widget.go")
        self.assertEqual(
            self.kinds(),
            [
                ("stutter", "billing/billingService.ts"),
                ("stutter", "http/http_server.go"),
            ],
        )

    def test_go_os_suffixes_are_one_concept(self) -> None:
        self.touch(
            "net/poll_linux.go", "net/poll_darwin.go", "net/poll_windows_amd64.go"
        )
        self.assertEqual(self.kinds("--min-group", "2"), [])

    def test_crowded_dir_only_with_max_files(self) -> None:
        self.touch("a/one.py", "a/two.py", "a/three.py", "a/test_four.py")
        self.assertEqual(self.kinds(), [])
        self.assertEqual(self.kinds("--max-files", "2"), [("crowded-dir", "a")])
        self.assertEqual(self.kinds("--max-files", "3"), [])
        self.assertEqual(self.kinds("--max-files", "3", "--include-tests"), [])

    def test_deep_path_only_with_max_depth(self) -> None:
        self.touch("a/b/c/deep.py", "a/shallow.py")
        self.assertEqual(self.kinds(), [])
        self.assertEqual(
            self.kinds("--max-depth", "2"), [("deep-path", "a/b/c/deep.py")]
        )
        self.assertEqual(self.kinds("--max-depth", "3"), [])

    def test_test_files_skipped_by_default(self) -> None:
        self.touch("a/utils_test.go", "tests/helpers.py", "a/common.spec.ts")
        self.assertEqual(self.kinds(), [])
        self.assertEqual(
            self.kinds("--include-tests"),
            [
                ("generic-name", "a/common.spec.ts"),
                ("generic-name", "tests/helpers.py"),
            ],
        )

    def test_exclude_glob(self) -> None:
        self.touch("gen/utils.py")
        self.assertEqual(self.kinds("--exclude", "*/gen/*"), [])

    def test_text_output_and_exit_codes(self) -> None:
        self.touch("a/fine.py")
        self.assertEqual(run([str(self.root)]), (0, "findings: 0\n"))
        self.touch("a/utils.py")
        status, out = run([str(self.root)])
        self.assertEqual(status, 1)
        lines = out.splitlines()
        self.assertTrue(lines[0].startswith("generic-name "))
        self.assertTrue(
            lines[0].endswith(
                'a/utils.py: "utils" says nothing about what the file holds'
            )
        )
        self.assertEqual(lines[-1], "findings: 1 (generic-name 1)")

    def test_json_shape(self) -> None:
        self.touch("a/utils.py")
        status, out = run([str(self.root), "--json"])
        report = json.loads(out)
        self.assertEqual(status, 1)
        self.assertEqual(set(report), {"findings", "summary"})
        self.assertEqual(set(report["findings"][0]), {"kind", "path", "detail"})
        self.assertEqual(report["summary"]["generic-name"], 1)
        self.assertEqual(set(report["summary"]), set(layout_smells.KINDS))

    def test_missing_path_and_bad_values_exit_two(self) -> None:
        self.assertEqual(run([str(self.root / "missing")])[0], 2)
        for option in ("--min-group", "--max-files", "--max-depth"):
            self.assertEqual(run([str(self.root), option, "0"])[0], 2)


if __name__ == "__main__":
    unittest.main()
