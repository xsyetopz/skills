#!/usr/bin/env python3
"""Compare resolved packages between an npm package-lock.json and bun.lock.

Extracts {package name: resolved version or workspace/file source} from
each file and prints packages that were added, removed, or changed. Use it
after `bun install` migrates a package-lock.json, before deleting the old
lockfile.

Supported inputs:
  package-lock.json  lockfileVersion 2 or 3 ("packages" map)
  bun.lock           text lockfile (JSON with trailing commas)

Graphs where a package is installed at more than one version
(node_modules/a/node_modules/b) or under a workspace folder
(packages/x/node_modules/b) are rejected with exit status 2: one name then
maps to several versions and a per-name diff would hide changes.

Usage: compare_lockfiles.py OLD NEW [--json]
Exit status: 0 same resolutions, 1 differences, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


def load_json_with_trailing_commas(text: str) -> dict:
    return json.loads(re.sub(r",(\s*[}\]])", r"\1", text))


def npm_packages(data: dict) -> dict[str, str]:
    packages: dict[str, str] = {}
    for path, entry in data.get("packages", {}).items():
        if "node_modules/" not in path:
            continue  # the root or a workspace folder, listed again as a link
        if not path.startswith("node_modules/") or path.count("node_modules/") > 1:
            raise ValueError(
                f"nested install {path!r}: this script compares flat graphs "
                "only; compare `bun pm ls --all` output instead"
            )
        name = path.removeprefix("node_modules/")
        if entry.get("link"):
            packages[name] = f"link:{entry.get('resolved', '')}"
        else:
            packages[name] = entry.get("version", "")
    return packages


def bun_packages(data: dict) -> dict[str, str]:
    packages: dict[str, str] = {}
    for name, entry in data.get("packages", {}).items():
        spec = entry[0] if isinstance(entry, list) and entry else ""
        _, _, source = spec.rpartition("@")
        if source.startswith("workspace:"):
            packages[name] = "link:" + source.removeprefix("workspace:")
        elif source.startswith("file:"):
            packages[name] = "link:" + source.removeprefix("file:").removeprefix("./")
        else:
            packages[name] = source
    return packages


def load(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    if path.name == "bun.lock":
        return bun_packages(load_json_with_trailing_commas(text))
    return npm_packages(json.loads(text))


EPILOG = """\
Exit status:
  0  both lockfiles resolve every package the same way
  1  packages were added, removed, or changed
  2  unreadable input: missing file, unsupported lockfile, or a package
     installed at several versions or under a workspace folder

Output: "same=N added=N removed=N changed=N", then "+ name version",
"- name version", and "~ name old -> new" lines. --json prints {"added":
{NAME: VERSION}, "removed": {...}, "changed": {NAME: [OLD, NEW]}, "same": N}.

Examples:
  git show HEAD:package-lock.json > /tmp/package-lock.json
  python3 scripts/compare_lockfiles.py /tmp/package-lock.json bun.lock
  python3 scripts/compare_lockfiles.py package-lock.json bun.lock --json \\
    | jq '.changed'
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("old", help="the npm package-lock.json (v2 or v3)")
    parser.add_argument("new", help="the migrated bun.lock (text lockfile)")
    parser.add_argument("--json", action="store_true", help="print a JSON report")
    args = parser.parse_args(argv)
    try:
        old, new = load(Path(args.old)), load(Path(args.new))
    except (OSError, ValueError) as error:
        print(
            f"error: {error}; expected OLD to be package-lock.json (lockfileVersion "
            "2 or 3) and NEW to be a text bun.lock",
            file=sys.stderr,
        )
        return 2
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(n for n in set(old) & set(new) if old[n] != new[n])
    report = {
        "added": {n: new[n] for n in added},
        "removed": {n: old[n] for n in removed},
        "changed": {n: [old[n], new[n]] for n in changed},
        "same": len(set(old) & set(new)) - len(changed),
    }
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(
            f"same={report['same']} added={len(added)} "
            f"removed={len(removed)} changed={len(changed)}"
        )
        for name in added:
            print(f"  + {name} {new[name]}")
        for name in removed:
            print(f"  - {name} {old[name]}")
        for name in changed:
            print(f"  ~ {name} {old[name]} -> {new[name]}")
    return 1 if added or removed or changed else 0


if __name__ == "__main__":
    raise SystemExit(main())
