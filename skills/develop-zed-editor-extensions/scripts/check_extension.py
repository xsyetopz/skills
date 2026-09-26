"""Check a Zed extension directory before a dev install or registry PR.

Stdlib only (Python 3.11+ for tomllib). The rules mirror Zed v1.21.0's
extension manifest and language config parsers, the `zed-extension`
packaging CLI, and the zed-industries/extensions registry validation.

    python3 check_extension.py EXT_DIR [--registry] [--json]

Exit status: 0 when no errors, 1 when any error, 2 on bad usage.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

import tomllib

EPILOG = """\
Exit status:
  0  no errors (warnings alone do not fail)
  1  at least one error
  2  bad usage: EXT_DIR is not a directory

Output: one "ERROR|WARN PATH: message" line per finding, then "N errors,
N warnings". --json prints a list of {level, path, message}.

Examples:
  python3 scripts/check_extension.py my-extension
  python3 scripts/check_extension.py my-extension --registry
  python3 scripts/check_extension.py my-extension --json \\
    | jq '.[] | select(.level == "ERROR")'
"""
MANIFEST_KEYS = {
    "id",
    "name",
    "version",
    "schema_version",
    "description",
    "repository",
    "authors",
    "lib",
    "themes",
    "icon_themes",
    "languages",
    "grammars",
    "language_servers",
    "context_servers",
    "slash_commands",
    "snippets",
    "capabilities",
    "debug_adapters",
    "debug_locators",
    "language_model_providers",
}
SERVER_KEYS = {"name", "language", "languages", "language_ids", "code_action_kinds"}
QUERY_FILES = {
    "highlights.scm",
    "brackets.scm",
    "outline.scm",
    "indents.scm",
    "injections.scm",
    "overrides.scm",
    "redactions.scm",
    "runnables.scm",
    "debugger.scm",
    "textobjects.scm",
}
LANGUAGE_FILES = {"config.toml", "semantic_token_rules.json", "tasks.json"}
CAPABILITY_FIELDS = {
    "process:exec": {"command": str, "args": list},
    "download_file": {"host": str, "path": list},
    "npm:install": {"package": str},
}
REGEX_KEYS = (
    "first_line_pattern",
    "increase_indent_pattern",
    "decrease_indent_pattern",
)
STABLE_API_MAX = (0, 7)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ID_RE = re.compile(r"^[a-z0-9-]+$")
SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
REQ_RE = re.compile(r"^\s*[=^~]?\s*(\d+)\.(\d+)")

# Required phrases from src/lib/license.js in zed-industries/extensions: the
# full MIT list, a subset for the others. Registry CI remains authoritative.
LICENSES = {
    "MIT": [
        r"Copyright",
        r"Permission is hereby granted, free of charge, to any person "
        r"obtaining a copy",
        r"The above copyright notice and this permission notice shall be "
        r"included in all",
        r"THE SOFTWARE IS PROVIDED [\"“]AS IS[\"”], WITHOUT WARRANTY OF ANY "
        r"KIND, EXPRESS OR",
    ],
    "Apache-2.0": [
        r"Apache License",
        r"Version 2\.0, January 2004",
        r"http://www.apache.org/licenses/",
        r"TERMS AND CONDITIONS FOR USE, REPRODUCTION, AND DISTRIBUTION",
        r"1\. Definitions\.",
        r"4\. Redistribution\.",
        r"9\. Accepting Warranty or Additional Liability\.",
    ],
    "BSD": [
        r"Copyright",
        r"Redistribution and use in source and binary forms, with or without",
        r"1\. Redistributions of source code must retain the above copyright",
        r"2\. Redistributions in binary form must reproduce the above "
        r"copyright",
    ],
    "GPL-3.0": [
        r"GNU GENERAL PUBLIC LICENSE",
        r"Version 3, 29 June 2007",
        r"2\. Basic Permissions",
    ],
    "LGPL-3.0": [
        r"GNU LESSER GENERAL PUBLIC LICENSE",
        r"Version 3, 29 June 2007",
        r"1\. Exception to Section 3 of the GNU GPL",
    ],
    "Unlicense": [
        r"free and unencumbered software released into the public domain",
        r"For more information, please refer to\s+<?https?://unlicense\.org/?>?",
    ],
    "CC-BY-4.0": [
        r"Creative Commons Attribution 4\.0 International Public License",
        r"Section 1 -- Definitions",
    ],
    "Zlib": [
        r"Permission is granted to anyone to use this software for any purpose",
        r"3\. This notice may not be removed or altered from any source\s+"
        r"distribution",
    ],
}


@dataclass
class Finding:
    level: str
    path: str
    message: str


class Checker:
    def __init__(self, root: Path, registry: bool) -> None:
        self.root = root
        self.registry = registry
        self.findings: list[Finding] = []

    def error(self, path: Path | str, message: str) -> None:
        self.findings.append(Finding("ERROR", self._rel(path), message))

    def warn(self, path: Path | str, message: str) -> None:
        self.findings.append(Finding("WARN", self._rel(path), message))

    def _rel(self, path: Path | str) -> str:
        path = Path(path)
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)

    def load_toml(self, path: Path) -> dict | None:
        try:
            return tomllib.loads(path.read_text(encoding="utf-8"))
        except (OSError, tomllib.TOMLDecodeError) as error:
            self.error(path, f"cannot parse TOML: {error}")
            return None

    def run(self) -> list[Finding]:
        manifest_path = self.root / "extension.toml"
        if (self.root / "extension.json").exists():
            self.error("extension.json", "superseded format; use extension.toml")
        if not manifest_path.is_file():
            self.error(manifest_path, "missing extension.toml")
            return self.findings
        manifest = self.load_toml(manifest_path)
        if manifest is None:
            return self.findings
        self.check_manifest(manifest)
        language_names = self.check_languages(manifest)
        self.check_servers(manifest, language_names)
        self.check_rust(manifest)
        self.check_snippets(manifest)
        self.check_debug_adapters(manifest)
        self.check_capabilities(manifest)
        if self.registry:
            self.check_registry(manifest)
        return self.findings

    def check_manifest(self, manifest: dict) -> None:
        path = "extension.toml"
        for key, kind in (("id", str), ("name", str), ("version", str)):
            if not isinstance(manifest.get(key), kind):
                self.error(path, f"`{key}` is required and must be a string")
        if manifest.get("schema_version") != 1:
            self.error(path, "`schema_version` must be the integer 1")
        for key in sorted(set(manifest) - MANIFEST_KEYS):
            hint = ""
            if key.replace("-", "_") in MANIFEST_KEYS:
                hint = f"; did you mean `{key.replace('-', '_')}`?"
            self.error(path, f"unknown key `{key}` is ignored by Zed{hint}")
        if "slash_commands" in manifest:
            self.error(path, "slash commands were removed; use an MCP server")
        if "language_model_providers" in manifest:
            self.error(path, "language model providers are unsupported")
        for name, grammar in manifest.get("grammars", {}).items():
            where = f"extension.toml [grammars.{name}]"
            if not isinstance(grammar, dict):
                self.error(where, "must be a table")
                continue
            repository = grammar.get("repository")
            rev = grammar.get("rev", grammar.get("commit"))
            if not isinstance(repository, str):
                self.error(where, "`repository` is required")
            elif self.registry and repository.startswith("file://"):
                self.error(where, "file:// grammars work only for dev installs")
            if not isinstance(rev, str):
                self.error(where, "`rev` (or `commit`) is required")
            elif not SHA_RE.match(rev):
                self.error(where, f"pin a 40-character commit SHA, not {rev!r}")

    def check_languages(self, manifest: dict) -> dict[str, str]:
        names: dict[str, str] = {}
        grammars = set(manifest.get("grammars", {}))
        lang_root = self.root / "languages"
        if not lang_root.is_dir():
            return names
        snippet_files = {(self.root / p).resolve() for p in _snippet_paths(manifest)}
        for directory in sorted(p for p in lang_root.iterdir() if p.is_dir()):
            config_path = directory / "config.toml"
            if not config_path.is_file():
                self.warn(directory, "no config.toml; Zed skips this directory")
                continue
            config = self.load_toml(config_path)
            if config is None:
                continue
            name = config.get("name")
            if not isinstance(name, str) or not name:
                self.error(config_path, "`name` is required")
                continue
            if name in names:
                self.error(config_path, f"language {name!r} is defined twice")
            names[name] = str(directory)
            grammar = config.get("grammar")
            if not isinstance(grammar, str):
                self.error(config_path, "`grammar` is required")
            elif grammar not in grammars:
                self.error(
                    config_path,
                    f"grammar {grammar!r} is not in extension.toml [grammars]",
                )
            self.check_language_config(config_path, config)
            self.check_language_files(directory, config_path, snippet_files)
        return names

    def check_language_config(self, path: Path, config: dict) -> None:
        for suffix in config.get("path_suffixes", []):
            if any(ch in suffix for ch in "*?[]{}"):
                self.error(path, f"path_suffixes are literal, not globs: {suffix}")
        for key in REGEX_KEYS:
            pattern = config.get(key)
            if pattern is None:
                continue
            try:
                re.compile(pattern)
            except (re.error, TypeError) as error:
                self.warn(
                    path,
                    f"`{key}` does not compile ({error}); Zed uses "
                    "Rust regex syntax, so confirm it there",
                )
        tab_size = config.get("tab_size")
        if tab_size is not None and not (
            isinstance(tab_size, int) and 1 <= tab_size <= 128
        ):
            self.error(path, "`tab_size` must be an integer from 1 to 128")
        if "hard_tabs" in config and not isinstance(config["hard_tabs"], bool):
            self.error(path, "`hard_tabs` must be a boolean")
        overrides = path.parent / "overrides.scm"
        scopes = _override_scopes(overrides)
        referenced = [
            (f"brackets[{index}].not_in", scope)
            for index, pair in enumerate(config.get("brackets", []))
            for scope in pair.get("not_in", [])
        ]
        referenced += [(f"[overrides.{s}]", s) for s in config.get("overrides", {})]
        for index, pair in enumerate(config.get("brackets", [])):
            missing = [k for k in ("start", "end", "close", "newline") if k not in pair]
            if missing:
                self.error(path, f"brackets[{index}] lacks {', '.join(missing)}")
        for where, scope in referenced:
            if not overrides.is_file():
                self.warn(path, f"{where} {scope!r} has no effect: no overrides.scm")
            elif scope not in scopes:
                self.error(
                    path,
                    f"{where} {scope!r} has no capture in overrides.scm; "
                    "Zed fails to load the language",
                )

    def check_language_files(
        self, directory: Path, config_path: Path, snippet_files: set[Path]
    ) -> None:
        for file in sorted(directory.iterdir()):
            if file.name in LANGUAGE_FILES or file.name in QUERY_FILES:
                continue
            if file.resolve() in snippet_files:
                continue
            if file.suffix == ".scm":
                self.error(file, "query file name is not supported by Zed")
            else:
                self.error(file, "unsupported file in a language directory")

    def check_servers(self, manifest: dict, languages: dict[str, str]) -> None:
        for server_id, entry in manifest.get("language_servers", {}).items():
            where = f"extension.toml [language_servers.{server_id}]"
            for key in sorted(set(entry) - SERVER_KEYS):
                self.error(where, f"unknown key `{key}` is ignored by Zed")
            targets = entry.get("languages") or (
                [entry["language"]] if "language" in entry else []
            )
            if not targets:
                self.error(where, "set `languages` (or `language`)")
            for language in targets:
                if language not in languages:
                    self.warn(
                        where,
                        f"{language!r} is not defined here; it must equal "
                        "the `name` of a built-in or installed language exactly",
                    )

    def check_rust(self, manifest: dict) -> None:
        cargo = self.root / "Cargo.toml"
        needs_rust = any(
            manifest.get(key)
            for key in (
                "language_servers",
                "context_servers",
                "debug_adapters",
                "debug_locators",
            )
        )
        if not cargo.is_file():
            if needs_rust:
                self.error("Cargo.toml", "servers and debuggers need a Rust crate")
            return
        if not needs_rust:
            self.error(
                cargo, "Rust code without a server or debugger; remove the crate"
            )
        data = self.load_toml(cargo)
        if data is None:
            return
        crate_types = data.get("lib", {}).get("crate-type", [])
        if "cdylib" not in crate_types:
            self.error(cargo, '[lib] crate-type must include "cdylib"')
        dependency = data.get("dependencies", {}).get("zed_extension_api")
        if dependency is None:
            self.error(cargo, "missing dependency `zed_extension_api`")
            return
        if isinstance(dependency, dict):
            if "path" in dependency or "git" in dependency:
                self.warn(cargo, "zed_extension_api is not from crates.io")
                return
            dependency = dependency.get("version", "")
        renamed = any(
            isinstance(spec, dict) and spec.get("package") == "zed_extension_api"
            for spec in data.get("dependencies", {}).values()
        )
        if renamed:
            self.error(cargo, "do not rename zed_extension_api; the macro needs it")
        match = REQ_RE.match(str(dependency))
        if match is None:
            self.error(cargo, f"cannot read zed_extension_api {dependency!r}")
        elif (int(match[1]), int(match[2])) > STABLE_API_MAX:
            self.error(
                cargo,
                f"zed_extension_api {dependency} is newer than the 0.7 "
                "API that stable Zed accepts",
            )

    def check_snippets(self, manifest: dict) -> None:
        for relative in _snippet_paths(manifest):
            path = self.root / relative
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                self.error(path, f"cannot read snippets: {error}")
                continue
            if not isinstance(data, dict):
                self.error(path, "snippets file must be a JSON object")
                continue
            for name, snippet in data.items():
                body = snippet.get("body") if isinstance(snippet, dict) else None
                if not isinstance(body, (str, list)):
                    self.error(path, f"snippet {name!r} needs a string/list body")

    def check_debug_adapters(self, manifest: dict) -> None:
        for name, entry in manifest.get("debug_adapters", {}).items():
            relative = entry.get("schema_path") or (
                f"debug_adapter_schemas/{name}.json"
            )
            path = self.root / relative
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:
                self.error(path, f"debug adapter {name!r} schema: {error}")

    def check_capabilities(self, manifest: dict) -> None:
        for index, capability in enumerate(manifest.get("capabilities", [])):
            where = f"extension.toml capabilities[{index}]"
            fields = CAPABILITY_FIELDS.get(capability.get("kind"))
            if fields is None:
                self.error(where, f"unknown kind {capability.get('kind')!r}")
                continue
            for field, kind in fields.items():
                if not isinstance(capability.get(field), kind):
                    self.error(where, f"`{field}` must be a {kind.__name__}")

    def check_registry(self, manifest: dict) -> None:
        path = "extension.toml"
        ext_id = str(manifest.get("id", ""))
        name = str(manifest.get("name", "")).strip()
        if not ID_RE.match(ext_id):
            self.error(path, "id must use only lowercase letters, digits, '-'")
        if ext_id.startswith("zed-") or ext_id.endswith("-zed"):
            self.error(path, "id must not start with 'zed-' or end with '-zed'")
        if "extension" in ext_id:
            self.error(path, "id must not contain 'extension'")
        if name.startswith("Zed ") or name.endswith(" Zed"):
            self.error(path, "name must not start or end with 'Zed'")
        if "extension" in name.lower():
            self.error(path, "name must not contain 'extension'")
        if not SEMVER_RE.match(str(manifest.get("version", ""))):
            self.error(path, "version must be plain major.minor.patch")
        description = str(manifest.get("description") or "").strip()
        if len(description) <= len(name):
            self.error(path, "description must be longer than the name")
        if not any(str(a).strip() for a in manifest.get("authors", [])):
            self.error(path, "at least one author is required")
        repository = str(manifest.get("repository") or "")
        if not re.match(r"^[a-z][a-z0-9+.-]*://[^/\s]+", repository):
            self.error(path, "repository must be a URL with a host")
        self.check_license()
        self.check_features(manifest)

    def check_license(self) -> None:
        candidates = [
            p
            for p in self.root.iterdir()
            if p.is_file() and p.stem.lower().startswith(("license", "licence"))
        ]
        if not candidates:
            self.error("LICENSE", "no LICENSE/LICENCE file at the extension root")
            return
        for candidate in candidates:
            text = " ".join(candidate.read_text(errors="replace").split())
            if _license_kind(text):
                return
        self.error(candidates[0], "license text is not an accepted license")

    def check_features(self, manifest: dict) -> None:
        provides = _provides(self.root, manifest)
        if not provides:
            self.error("extension.toml", "extension provides no features")
        for feature in ("themes", "icon_themes"):
            if feature in provides and len(provides) > 1:
                self.error("extension.toml", f"{feature} cannot be mixed")
        servers = manifest.get("context_servers", {})
        if servers and (len(servers) > 1 or len(provides) > 1):
            self.error("extension.toml", "an MCP extension ships one server only")


def _snippet_paths(manifest: dict) -> list[str]:
    snippets = manifest.get("snippets")
    if snippets is None:
        return []
    return [snippets] if isinstance(snippets, str) else list(snippets)


def _override_scopes(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    text = re.sub(r";[^\n]*", "", path.read_text(encoding="utf-8"))
    names = re.findall(r"@([A-Za-z0-9_.\-]+)", text)
    return {n.removesuffix(".inclusive") for n in names if not n.startswith("_")}


def _license_kind(text: str) -> str | None:
    for kind, patterns in LICENSES.items():
        if all(re.search(p, text, re.IGNORECASE) for p in patterns):
            return kind
    return None


def _provides(root: Path, manifest: dict) -> set[str]:
    provides = {
        key
        for key in (
            "grammars",
            "language_servers",
            "context_servers",
            "debug_adapters",
        )
        if manifest.get(key)
    }
    for key, folder in (
        ("themes", "themes"),
        ("icon_themes", "icon_themes"),
        ("languages", "languages"),
    ):
        if manifest.get(key) or any((root / folder).glob("*")):
            provides.add(key)
    if manifest.get("snippets") or (root / "snippets.json").is_file():
        provides.add("snippets")
    return provides


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").split("\n")[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "extension_dir", type=Path, help="extension root holding extension.toml"
    )
    parser.add_argument(
        "--registry",
        action="store_true",
        help="also apply the zed-industries/extensions registry rules",
    )
    parser.add_argument(
        "--json", action="store_true", help="print the findings as a JSON list"
    )
    args = parser.parse_args(argv)
    if not args.extension_dir.is_dir():
        print(
            f"not a directory: {args.extension_dir}; "
            "pass the extension root that holds extension.toml",
            file=sys.stderr,
        )
        return 2
    findings = Checker(args.extension_dir.resolve(), args.registry).run()
    errors = sum(f.level == "ERROR" for f in findings)
    if args.json:
        print(json.dumps([asdict(f) for f in findings], indent=2))
    else:
        for finding in findings:
            print(f"{finding.level} {finding.path}: {finding.message}")
        print(f"{errors} errors, {len(findings) - errors} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
