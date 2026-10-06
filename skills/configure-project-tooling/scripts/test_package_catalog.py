"""Offline tests for package_catalog.py.

Registry access is replaced by stub fetchers (STUB below); nothing here touches
the network. The shipped catalog files are checked against schema.json with a
small validator that supports the schema keywords the schema actually uses.
"""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any
from unittest import mock

import package_catalog as pc

PACKAGES = pc.PACKAGES_DIR
SCHEMA = json.loads((PACKAGES / "schema.json").read_text(encoding="utf-8"))
VERIFIED = "2026-10-07"


def run(*args: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = pc.main(list(args))
    return code, out.getvalue(), err.getvalue()


def stub_fetcher(table: dict[str, dict[str, Any]]) -> pc.Fetcher:
    """STUB: returns canned facts per package name instead of calling a registry."""

    def fetch(name: str, _ctx: pc.Context) -> dict[str, Any]:
        if name == "boom":
            raise RuntimeError("stub failure")
        return table.get(name, {"missing": True})

    return fetch


def type_ok(value: Any, expected: str) -> bool:
    return {
        "string": isinstance(value, str),
        "null": value is None,
        "boolean": isinstance(value, bool),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "array": isinstance(value, list),
        "object": isinstance(value, dict),
    }[expected]


def validate(value: Any, schema: dict[str, Any], path: str = "row") -> list[str]:
    """Validate against type, enum, const, pattern, length, bounds, object and array keywords."""
    import re

    errors: list[str] = []
    if "const" in schema and value != schema["const"]:
        errors.append(f"{path}: expected {schema['const']!r}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} not in enum")
    if "type" in schema:
        types = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(type_ok(value, t) for t in types):
            return [*errors, f"{path}: {value!r} is not {types}"]
    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
        if len(value) > schema.get("maxLength", len(value)):
            errors.append(f"{path}: longer than {schema['maxLength']}")
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: shorter than {schema['minLength']}")
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value < schema.get("minimum", value)
    ):
        errors.append(f"{path}: below minimum")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        errors += [
            f"{path}: missing {k}" for k in schema.get("required", []) if k not in value
        ]
        if schema.get("additionalProperties") is False:
            errors += [f"{path}: unexpected key {k}" for k in value if k not in props]
        for key, sub in props.items():
            if key in value:
                errors += validate(value[key], sub, f"{path}.{key}")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            errors += validate(item, schema["items"], f"{path}[{i}]")
    for rule in schema.get("allOf", []):
        if not validate(value, rule["if"], path):
            errors += validate(value, rule["then"], path)
    return errors


class StatusTests(unittest.TestCase):
    def test_precedence_missing_over_everything(self) -> None:
        facts = {
            "missing": True,
            "deprecated": True,
            "archived": True,
            "released": "2000-01-01",
        }
        self.assertEqual(pc.derive_status(facts, VERIFIED), "missing")

    def test_deprecated_over_archived_and_stale(self) -> None:
        facts = {"deprecated": True, "archived": True, "released": "2000-01-01"}
        self.assertEqual(pc.derive_status(facts, VERIFIED), "deprecated")

    def test_archived_over_stale(self) -> None:
        facts = {"archived": True, "released": "2000-01-01"}
        self.assertEqual(pc.derive_status(facts, VERIFIED), "archived")

    def test_prerelease_below_archived_above_stale(self) -> None:
        facts = {"prerelease": True, "released": "2000-01-01"}
        self.assertEqual(pc.derive_status(facts, VERIFIED), "prerelease")
        self.assertEqual(
            pc.derive_status({**facts, "archived": True}, VERIFIED), "archived"
        )
        self.assertEqual(
            pc.derive_status({**facts, "deprecated": True}, VERIFIED), "deprecated"
        )

    def test_stale_boundary_is_730_days_exclusive(self) -> None:
        # 2026-10-07 minus 730 days is 2024-10-07.
        self.assertEqual(
            pc.derive_status({"released": "2024-10-07"}, VERIFIED), "active"
        )
        self.assertEqual(
            pc.derive_status({"released": "2024-10-06"}, VERIFIED), "stale"
        )

    def test_unknown_facts_do_not_demote(self) -> None:
        self.assertEqual(
            pc.derive_status({"archived": None, "released": None}, VERIFIED), "active"
        )


class RowTests(unittest.TestCase):
    def test_row_has_exact_keys_in_order_and_all_traits(self) -> None:
        row = pc.make_row(
            "crates",
            "x",
            "testing",
            {"latest": "1.0.0", "traits": {"noStd": True}},
            VERIFIED,
        )
        self.assertEqual(tuple(row), pc.ROW_KEYS)
        self.assertEqual(
            row["traits"], {"msrv": None, "noStd": True, "procMacro": None}
        )
        self.assertEqual(row["advisories"], [])
        self.assertEqual(row["verified"], VERIFIED)

    def test_internal_fact_flags_do_not_leak(self) -> None:
        row = pc.make_row(
            "npm", "x", "testing", {"deprecated": True, "missing": False}, VERIFIED
        )
        self.assertNotIn("deprecated", row)
        self.assertNotIn("missing", row)

    def test_deprecation_trimmed_to_200(self) -> None:
        row = pc.make_row(
            "npm",
            "x",
            "testing",
            {"deprecated": True, "deprecation": "a  b\n" * 200},
            VERIFIED,
        )
        self.assertEqual(len(row["deprecation"]), 200)
        self.assertNotIn("\n", row["deprecation"])

    def test_missing_row_has_null_facts(self) -> None:
        row = pc.make_row("go", "gone", "testing", {"missing": True}, VERIFIED)
        self.assertEqual(row["status"], "missing")
        self.assertIsNone(row["latest"])
        self.assertEqual(row["traits"], {"goVersion": None, "cgo": None})

    def test_stub_rows_validate_against_schema(self) -> None:
        for eco in pc.ECOSYSTEMS:
            row = pc.make_row(
                eco,
                "x",
                "testing",
                {"latest": "1.0.0", "released": "2026-01-01"},
                VERIFIED,
            )
            self.assertEqual(validate(row, SCHEMA), [], eco)


class ParserTests(unittest.TestCase):
    def test_requirement_matching(self) -> None:
        self.assertTrue(pc.req_matches(">=1.2.3", "1.2.3"))
        self.assertFalse(pc.req_matches("<1.2.3", "1.2.3"))
        self.assertTrue(pc.req_matches(">=0.4.1, <0.5.0", "0.4.9"))
        self.assertFalse(pc.req_matches(">=0.4.1, <0.5.0", "0.5.0"))
        self.assertTrue(pc.req_matches("^1.2", "1.9.0"))
        self.assertFalse(pc.req_matches("^1.2", "2.0.0"))
        self.assertTrue(pc.req_matches("^0.2.3", "0.2.9"))
        self.assertFalse(pc.req_matches("^0.2.3", "0.3.0"))
        self.assertTrue(pc.req_matches("~1.2.3", "1.2.9"))
        self.assertFalse(pc.req_matches("~1.2.3", "1.3.0"))

    def test_rustsec_affecting_respects_patched_and_withdrawn(self) -> None:
        advisories = [
            {"id": "A", "patched": [">=1.0.0"], "unaffected": [], "withdrawn": None},
            {"id": "B", "patched": [">=2.0.0"], "unaffected": [], "withdrawn": None},
            {"id": "C", "patched": [], "unaffected": [], "withdrawn": "2024-01-01"},
            {"id": "D", "patched": [], "unaffected": ["<0.5.0"], "withdrawn": None},
        ]
        ids = [a["id"] for a in pc.rustsec_affecting(advisories, "1.5.0")]
        self.assertEqual(ids, ["B", "D"])

    def test_normalize_repo(self) -> None:
        cases = {
            "git+https://github.com/a/b.git": "https://github.com/a/b",
            "git@github.com:a/b.git": "https://github.com/a/b",
            "git://github.com/a/b.git": "https://github.com/a/b",
            "github:a/b": "https://github.com/a/b",
            "a/b": "https://github.com/a/b",
            "https://github.com/a/b/tree/main/packages/x": "https://github.com/a/b",
            "https://gitlab.com/a/b.git": "https://gitlab.com/a/b",
            "": None,
            "not a url": None,
        }
        for raw, expected in cases.items():
            self.assertEqual(pc.normalize_repo(raw), expected, raw)
        self.assertEqual(
            pc.normalize_repo({"type": "git", "url": "git+https://github.com/a/b.git"}),
            "https://github.com/a/b",
        )

    def test_npm_module_kind(self) -> None:
        self.assertEqual(pc.npm_module_kind({"type": "module"}), "esm")
        self.assertEqual(pc.npm_module_kind({}), "cjs")
        self.assertEqual(
            pc.npm_module_kind(
                {
                    "type": "module",
                    "exports": {".": {"import": "./a.js", "require": "./a.cjs"}},
                }
            ),
            "dual",
        )
        self.assertEqual(
            pc.npm_module_kind(
                {"exports": {".": {"import": "./a.mjs", "default": "./a.js"}}}
            ),
            "dual",
        )

    def test_gomod_parsing(self) -> None:
        text = (
            "// Deprecated: use example.com/new/v2 instead.\n"
            "//\n"
            "// More text.\n"
            "module example.com/old\n\n"
            "go 1.21\n\n"
            "require (\n"
            "\tgithub.com/a/b v1.0.0\n"
            "\tgithub.com/c/d v1.0.0 // indirect\n"
            ")\n"
            "require github.com/e/f v0.1.0\n"
            "retract v1.0.1\n"
        )
        parsed = pc.parse_gomod(text, "v1.0.1")
        self.assertEqual(parsed["go"], "1.21")
        self.assertEqual(parsed["deps"], 2)
        self.assertTrue(parsed["retracted"])
        self.assertTrue(
            parsed["deprecation"].startswith("Deprecated: use example.com/new/v2")
        )
        self.assertFalse(pc.parse_gomod(text, "v1.0.2")["retracted"])
        self.assertEqual(
            pc.named_replacement(
                "use example.com/new/v2 instead.", "example.com/old", pc.GO_REPLACEMENT
            ),
            "example.com/new/v2",
        )

    def test_gomod_without_deprecation(self) -> None:
        self.assertIsNone(
            pc.parse_gomod("module example.com/x\n\ngo 1.20\n", "v1.0.0")["deprecation"]
        )

    def test_go_vulnerability_ranges(self) -> None:
        doc = {
            "affected": [
                {
                    "package": {"name": "m"},
                    "ranges": [
                        {
                            "type": "SEMVER",
                            "events": [{"introduced": "0"}, {"fixed": "1.2.0"}],
                        }
                    ],
                }
            ]
        }
        self.assertTrue(pc.go_affected(doc, "m", "v1.1.9"))
        self.assertFalse(pc.go_affected(doc, "m", "v1.2.0"))
        self.assertFalse(pc.go_affected(doc, "other", "v1.1.9"))

    def test_version_helpers(self) -> None:
        self.assertEqual(
            pc.newest_stable(["1.0.0", "2.0.0-rc.1", "1.10.0", "1.9.0"]), "1.10.0"
        )
        self.assertIsNone(pc.newest_stable(["1.0.0-beta"]))
        self.assertEqual(pc.day("1900-01-01T00:00:00Z"), None)


class StubHttp(pc.Http):
    """STUB: serves canned bodies by URL; any other URL answers 404."""

    def __init__(self, bodies: dict[str, Any]) -> None:
        super().__init__()
        self.bodies = bodies

    def get(self, url: str, **_kwargs: Any) -> tuple[int, bytes]:
        body = self.bodies.get(url)
        if body is None:
            return 404, b""
        raw = body if isinstance(body, bytes) else json.dumps(body).encode()
        return 200, raw


def stub_context(bodies: dict[str, Any]) -> pc.Context:
    ctx = pc.Context(http=StubHttp(bodies), verified=VERIFIED)
    ctx.github_token = None
    return ctx


class PrereleaseFetchTests(unittest.TestCase):
    def test_npm_prerelease_only_keeps_deprecation(self) -> None:
        packument = {
            "dist-tags": {"latest": "1.0.0-rc.0"},
            "versions": {
                "1.0.0-beta.1": {},
                "1.0.0-rc.0": {
                    "deprecated": "renamed",
                    "repository": "github:a/b",
                },
            },
        }
        ctx = stub_context({"https://registry.npmjs.org/pkg": packument})
        facts = pc.fetch_npm("pkg", ctx)
        self.assertIsNone(facts["latest"])
        row = pc.make_row("npm", "pkg", "utilities", facts, VERIFIED)
        self.assertEqual(row["status"], "deprecated")
        self.assertEqual(row["repository"], "https://github.com/a/b")
        plain = {**packument, "versions": {"1.0.0-rc.0": {}}}
        ctx = stub_context({"https://registry.npmjs.org/pkg": plain})
        row = pc.make_row("npm", "pkg", "utilities", pc.fetch_npm("pkg", ctx), VERIFIED)
        self.assertEqual(row["status"], "prerelease")

    def test_nuget_repository_falls_back_to_nuspec(self) -> None:
        base = "https://api.nuget.org/v3"
        entry = {
            "@id": f"{base}/catalog0/pkg.1.0.0.json",
            "version": "1.0.0",
            "published": "2026-01-01T00:00:00Z",
            "projectUrl": "",
        }
        index = {"items": [{"items": [{"catalogEntry": entry}]}]}
        nuspec = b'<package><metadata><repository type="git" url="https://github.com/a/b" /></metadata></package>'
        ctx = stub_context(
            {
                f"{base}/registration5-gz-semver2/pkg/index.json": index,
                f"{base}/catalog0/pkg.1.0.0.json": {"repository": ""},
                f"{base}-flatcontainer/pkg/1.0.0/pkg.nuspec": nuspec,
            }
        )
        self.assertEqual(
            pc.fetch_nuget("pkg", ctx)["repository"], "https://github.com/a/b"
        )

    def test_nuget_without_stable_version_is_prerelease(self) -> None:
        base = "https://api.nuget.org/v3"
        entry = {"version": "1.0.0-beta1", "@id": f"{base}/c.json"}
        index = {"items": [{"items": [{"catalogEntry": entry}]}]}
        ctx = stub_context({f"{base}/registration5-gz-semver2/pkg/index.json": index})
        row = pc.make_row(
            "nuget", "pkg", "utilities", pc.fetch_nuget("pkg", ctx), VERIFIED
        )
        self.assertEqual(row["status"], "prerelease")
        self.assertIsNone(row["latest"])


class CatalogCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        (self.dir / "schema.json").write_text(
            (PACKAGES / "schema.json").read_text(encoding="utf-8"), encoding="utf-8"
        )
        self.facts = {
            "alpha": {"latest": "1.0.0", "released": "2026-09-01", "downloads": 10},
            "bravo": {"latest": "2.0.0", "released": "2026-09-01", "downloads": 500},
            "old": {"latest": "0.1.0", "released": "2020-01-01", "downloads": 9000},
            "dead": {
                "latest": "1.0.0",
                "released": "2026-01-01",
                "deprecated": True,
                "downloads": 99999,
            },
        }
        rows = [
            pc.make_row("npm", n, d, f, VERIFIED)
            for n, d, f in [
                ("old", "logging", self.facts["old"]),
                ("bravo", "logging", self.facts["bravo"]),
                ("alpha", "logging", self.facts["alpha"]),
                ("dead", "testing", self.facts["dead"]),
            ]
        ]
        pc.write_rows(self.dir, "npm", rows)

    def query(self, *args: str) -> tuple[int, str, str]:
        return run("--catalog-dir", str(self.dir), "query", *args)

    def test_write_sorts_by_domain_then_name(self) -> None:
        names = [
            json.loads(line)["name"]
            for line in (self.dir / "npm.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        self.assertEqual(names, ["alpha", "bravo", "old", "dead"])

    def test_query_sorts_active_first_then_downloads(self) -> None:
        _, out, _ = self.query("--json")
        self.assertEqual(
            [json.loads(line)["name"] for line in out.splitlines()],
            ["bravo", "alpha", "dead", "old"],
        )

    def test_query_filters(self) -> None:
        _, out, _ = self.query("--json", "--domain", "logging", "--status", "active")
        self.assertEqual(
            {json.loads(line)["name"] for line in out.splitlines()}, {"alpha", "bravo"}
        )
        _, out, _ = self.query("--json", "--name", "ALP")
        self.assertEqual(
            [json.loads(line)["name"] for line in out.splitlines()], ["alpha"]
        )
        _, out, _ = self.query("--json", "--ecosystem", "go")
        self.assertEqual(out, "")

    def test_table_is_aligned_and_limited(self) -> None:
        _, out, _ = self.query("--ecosystem", "npm", "--limit", "2")
        lines = out.splitlines()
        self.assertEqual(
            lines[0].split(),
            ["name", "domain", "status", "latest", "released", "downloads"],
        )
        self.assertEqual(len(lines), 4)  # header, 2 rows, "more" footer
        self.assertIn("2 more", lines[-1])
        self.assertEqual(lines[1].index("logging"), lines[2].index("logging"))

    def test_domains_counts(self) -> None:
        _, out, _ = run("--catalog-dir", str(self.dir), "domains")
        self.assertEqual(
            [line.split() for line in out.splitlines()],
            [["logging", "3"], ["testing", "1"]],
        )

    def test_refresh_rewrites_in_place_and_keeps_failed_rows(self) -> None:
        table = {
            "alpha": {"latest": "1.1.0", "released": "2026-10-01"},
            "bravo": {"missing": True},
            "old": {},
            "dead": {},
        }
        with mock.patch.dict(pc.FETCHERS, {"npm": stub_fetcher(table)}):
            code, _, _ = run(
                "--catalog-dir", str(self.dir), "refresh", "--ecosystem", "npm"
            )
        self.assertEqual(code, 0)
        rows = {r["name"]: r for r in pc.load_rows(self.dir, "npm")}
        self.assertEqual(rows["alpha"]["latest"], "1.1.0")
        self.assertEqual(rows["bravo"]["status"], "missing")
        self.assertEqual(rows["old"]["domain"], "logging")
        self.assertIsNone(rows["old"]["latest"])
        table["boom"] = {}
        pc.write_rows(
            self.dir,
            "npm",
            [
                *rows.values(),
                pc.make_row("npm", "boom", "testing", {"latest": "9.9.9"}, VERIFIED),
            ],
        )
        with mock.patch.dict(pc.FETCHERS, {"npm": stub_fetcher(table)}):
            code, _, err = run(
                "--catalog-dir", str(self.dir), "refresh", "--ecosystem", "npm"
            )
        self.assertEqual(code, 1)
        self.assertIn("boom", err)
        self.assertEqual(
            {r["name"]: r for r in pc.load_rows(self.dir, "npm")}["boom"]["latest"],
            "9.9.9",
        )

    def test_refresh_limit_touches_only_first_rows(self) -> None:
        table = {"alpha": {"latest": "7.7.7"}, "bravo": {"latest": "8.8.8"}}
        with mock.patch.dict(pc.FETCHERS, {"npm": stub_fetcher(table)}):
            run(
                "--catalog-dir",
                str(self.dir),
                "refresh",
                "--ecosystem",
                "npm",
                "--limit",
                "1",
            )
        rows = {r["name"]: r for r in pc.load_rows(self.dir, "npm")}
        self.assertEqual(rows["alpha"]["latest"], "7.7.7")
        self.assertEqual(rows["bravo"]["latest"], "2.0.0")

    def test_add_inserts_one_row_and_rejects_bad_input(self) -> None:
        table = {"charlie": {"latest": "3.0.0", "released": "2026-10-01"}}
        with mock.patch.dict(pc.FETCHERS, {"npm": stub_fetcher(table)}):
            code, _, _ = run(
                "--catalog-dir",
                str(self.dir),
                "add",
                "--ecosystem",
                "npm",
                "--name",
                "charlie",
                "--domain",
                "text",
            )
            self.assertEqual(code, 0)
            self.assertEqual(
                run(
                    "--catalog-dir",
                    str(self.dir),
                    "add",
                    "--ecosystem",
                    "npm",
                    "--name",
                    "charlie",
                    "--domain",
                    "text",
                )[0],
                1,
            )
            self.assertEqual(
                run(
                    "--catalog-dir",
                    str(self.dir),
                    "add",
                    "--ecosystem",
                    "npm",
                    "--name",
                    "d",
                    "--domain",
                    "nope",
                )[0],
                2,
            )
        rows = pc.load_rows(self.dir, "npm")
        self.assertEqual(len(rows), 5)
        self.assertEqual(
            [r["name"] for r in rows if r["domain"] == "text"], ["charlie"]
        )


class ShippedCatalogTests(unittest.TestCase):
    def test_schema_domains_are_unique_lowercase_kebab(self) -> None:
        domains = SCHEMA["properties"]["domain"]["enum"]
        self.assertEqual(len(domains), len(set(domains)))
        self.assertTrue(25 <= len(domains) <= 45)
        for domain in domains:
            self.assertRegex(domain, r"^[a-z]+(-[a-z]+)*$")

    def test_every_file_exists_and_is_small(self) -> None:
        for eco in pc.ECOSYSTEMS:
            path = PACKAGES / pc.FILES[eco]
            self.assertTrue(path.exists(), path)
            self.assertLess(path.stat().st_size, 400 * 1024, path)

    def test_every_row_validates_sorted_unique(self) -> None:
        for eco in pc.ECOSYSTEMS:
            rows = pc.load_rows(PACKAGES, eco)
            self.assertTrue(rows, eco)
            self.assertEqual(
                rows, pc.sort_rows(rows), f"{eco} is not sorted by (domain, name)"
            )
            self.assertEqual(
                len({r["name"] for r in rows}), len(rows), f"{eco} has duplicates"
            )
            for row in rows:
                self.assertEqual(tuple(row), pc.ROW_KEYS, row["name"])
                self.assertEqual(row["ecosystem"], eco)
                self.assertEqual(validate(row, SCHEMA), [], row["name"])
                self.assertEqual(
                    row["status"],
                    pc.derive_status(_facts_from_row(row), row["verified"]),
                    row["name"],
                )


def _facts_from_row(row: dict[str, Any]) -> dict[str, Any]:
    """Facts that decide status, rebuilt from a stored row."""
    deprecated = row["status"] == "deprecated"
    return {
        "missing": row["status"] == "missing",
        "deprecated": deprecated,
        "prerelease": row["status"] == "prerelease",
        "archived": row["archived"],
        "released": row["released"],
    }


if __name__ == "__main__":
    unittest.main()
