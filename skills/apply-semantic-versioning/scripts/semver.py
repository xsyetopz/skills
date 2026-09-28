#!/usr/bin/env python3
"""Check, compare, sort, and bump Semantic Versioning 2.0.0 versions.

Spec: https://semver.org/spec/v2.0.0.html
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import subprocess
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

SPEC = "https://semver.org/spec/v2.0.0.html"
# The spec puts no limit on number size; Python 3.11+ caps int() at 4300
# digits by default.
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(0)
# Official regex from the spec (numbered capture groups). re.ASCII keeps \d
# from matching non-ASCII digits, which the grammar does not allow.
SEMVER_RE = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?"
    r"(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$",
    re.ASCII,
)
NUMERIC = re.compile(r"[0-9]+", re.ASCII)
IDENTIFIER = re.compile(r"[0-9A-Za-z-]+", re.ASCII)
MAX_LINES = 200
PARTS = ("major", "minor", "patch", "prerelease", "release")

EPILOG = f"""\
Commands:
  check VERSION... [--from-tags] [--json]
      Validate against the SemVer 2.0.0 grammar. --from-tags also checks
      every `git tag` in the current repository; a leading 'v' on a tag is
      accepted with a note, because tags are not versions. A bare version
      with a leading 'v' is invalid.
  compare A B
      Print '<', '=', or '>' by precedence (spec item 11). Build metadata
      is ignored, so 1.0.0+a = 1.0.0+b.
  sort VERSION... [--json]
      Print versions in ascending precedence, one per line. Versions that
      differ only in build metadata keep their input order.
  bump VERSION {{major,minor,patch,prerelease,release}} [--pre-id ID]
       [--build META]
      major/minor/patch increment that field, reset lower fields to 0, and
      drop pre-release; with --pre-id they start a train at -ID.1.
      prerelease on a final version bumps patch and adds -ID.1 (needs
      --pre-id); on a pre-release it increments the last numeric identifier
      or appends .1, or with a different --pre-id switches to -ID.1 if that
      raises precedence. release drops the pre-release. Existing build
      metadata is always dropped; --build attaches new metadata.

Exit status:
  0  success (check: every version valid)
  1  an invalid version, or a bump that would not raise precedence
  2  usage error: unknown command or option, bad --pre-id or --build,
     prerelease on a final version without --pre-id, git unavailable

Examples:
  python3 scripts/semver.py check 1.2.3 1.0.0-rc.1+sha.5114f85
  python3 scripts/semver.py check --from-tags --json
  python3 scripts/semver.py compare 1.0.0-beta.11 1.0.0-beta.2
  python3 scripts/semver.py sort 1.0.0 1.0.0-rc.1 1.0.0-alpha
  python3 scripts/semver.py bump 1.4.7 minor
  python3 scripts/semver.py bump 1.4.7 major --pre-id rc
  python3 scripts/semver.py bump 2.0.0-rc.1 prerelease
  python3 scripts/semver.py bump 2.0.0-rc.3 release --build sha.0a1b2c3

Spec: {SPEC}
"""


class UsageError(Exception):
    """A command-line argument other than a version is invalid (exit 2)."""


@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    prerelease: tuple[str, ...] = ()
    build: tuple[str, ...] = ()

    def __str__(self) -> str:
        text = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            text += "-" + ".".join(self.prerelease)
        if self.build:
            text += "+" + ".".join(self.build)
        return text


def _identifier_problem(ident: str, *, kind: str, numeric_rule: bool) -> str:
    if not ident:
        return f"empty {kind} identifier"
    if not IDENTIFIER.fullmatch(ident):
        return f"{kind} identifier '{ident}' has a character outside [0-9A-Za-z-]"
    if numeric_rule and NUMERIC.fullmatch(ident) and len(ident) > 1 and ident[0] == "0":
        return f"numeric {kind} identifier '{ident}' has a leading zero"
    return ""


def diagnose(text: str) -> str:
    """Say why text is not a SemVer 2.0.0 version."""
    if text[:1] in ("v", "V") and SEMVER_RE.fullmatch(text[1:]):
        return (
            f"leading '{text[0]}' is not part of a version; the version is {text[1:]}"
        )
    rest, plus, build = text.partition("+")
    core, dash, pre = rest.partition("-")
    fields = core.split(".")
    if len(fields) != 3:
        return f"expected MAJOR.MINOR.PATCH, got {len(fields)} dot-separated part(s)"
    for name, field in zip(("major", "minor", "patch"), fields, strict=True):
        if not NUMERIC.fullmatch(field):
            return f"{name} '{field}' is not a number"
        if len(field) > 1 and field[0] == "0":
            return f"{name} '{field}' has a leading zero"
    if dash:
        if not pre:
            return "empty pre-release after '-'"
        for ident in pre.split("."):
            if problem := _identifier_problem(
                ident, kind="pre-release", numeric_rule=True
            ):
                return problem
    if plus:
        if not build:
            return "empty build metadata after '+'"
        for ident in build.split("."):
            if problem := _identifier_problem(ident, kind="build", numeric_rule=False):
                return problem
    return "does not match the SemVer 2.0.0 grammar"


def parse(text: str) -> Version:
    match = SEMVER_RE.fullmatch(text)
    if not match:
        raise ValueError(f"'{text}': {diagnose(text)}")
    major, minor, patch, pre, build = match.groups()
    return Version(
        int(major),
        int(minor),
        int(patch),
        tuple(pre.split(".")) if pre else (),
        tuple(build.split(".")) if build else (),
    )


def from_tag(tag: str) -> tuple[Version, str]:
    """Parse a Git tag; a leading 'v' is a tag convention, noted, not an error."""
    if tag.startswith("v") and SEMVER_RE.fullmatch(tag[1:]):
        return parse(tag[1:]), "leading 'v' is a tag prefix, not part of the version"
    return parse(tag), ""


def _compare_identifier(a: str, b: str) -> int:
    a_numeric, b_numeric = bool(NUMERIC.fullmatch(a)), bool(NUMERIC.fullmatch(b))
    if a_numeric and b_numeric:
        x, y = int(a), int(b)
        return (x > y) - (x < y)
    if a_numeric != b_numeric:
        return -1 if a_numeric else 1  # numeric < alphanumeric (11.4.3)
    return (a > b) - (a < b)  # ASCII order (11.4.2)


def compare(a: Version, b: Version) -> int:
    """Return -1, 0, or 1 by SemVer precedence; build metadata is ignored."""
    core_a, core_b = (a.major, a.minor, a.patch), (b.major, b.minor, b.patch)
    if core_a != core_b:
        return 1 if core_a > core_b else -1
    if not a.prerelease or not b.prerelease:
        # A pre-release has lower precedence than its normal version (11.3).
        return (not a.prerelease) - (not b.prerelease)
    for x, y in zip(a.prerelease, b.prerelease, strict=False):
        if result := _compare_identifier(x, y):
            return result
    # A larger set of identifiers wins when all preceding are equal (11.4.4).
    return (len(a.prerelease) > len(b.prerelease)) - (
        len(a.prerelease) < len(b.prerelease)
    )


def sort_versions(texts: Iterable[str]) -> list[Version]:
    # sorted() is stable, so build-only differences keep their input order.
    return sorted((parse(t) for t in texts), key=functools.cmp_to_key(compare))


def _identifiers(value: str, *, option: str, numeric_rule: bool) -> tuple[str, ...]:
    kind = "pre-release" if numeric_rule else "build"
    idents = tuple(value.split("."))
    for ident in idents:
        if problem := _identifier_problem(ident, kind=kind, numeric_rule=numeric_rule):
            raise UsageError(f"{option} '{value}': {problem}")
    return idents


def bump(version: Version, part: str, pre_id: str | None, build: str | None) -> Version:
    """Return the next version; raise ValueError if precedence would not rise."""
    pre = (
        _identifiers(pre_id, option="--pre-id", numeric_rule=True)
        if pre_id is not None
        else None
    )
    meta = (
        _identifiers(build, option="--build", numeric_rule=False)
        if build is not None
        else ()
    )
    major, minor, patch = version.major, version.minor, version.patch
    if part in ("major", "minor", "patch"):
        if part == "major":
            major, minor, patch = major + 1, 0, 0
        elif part == "minor":
            minor, patch = minor + 1, 0
        else:
            patch += 1
        return Version(major, minor, patch, (*pre, "1") if pre else (), meta)
    if part == "release":
        if not version.prerelease:
            raise ValueError(f"'{version}' has no pre-release to release")
        return Version(major, minor, patch, (), meta)
    if part != "prerelease":
        raise UsageError(f"part must be one of {', '.join(PARTS)}, got '{part}'")
    if not version.prerelease:
        if pre is None:
            raise UsageError(
                f"prerelease on final version '{version}' needs --pre-id (e.g. rc)"
            )
        return Version(major, minor, patch + 1, (*pre, "1"), meta)
    current = version.prerelease
    if pre is None or current[: len(pre)] == pre:
        numeric = [i for i, ident in enumerate(current) if NUMERIC.fullmatch(ident)]
        if numeric:
            last = numeric[-1]
            idents = (
                *current[:last],
                str(int(current[last]) + 1),
                *current[last + 1 :],
            )
        else:
            idents = (*current, "1")
        return Version(major, minor, patch, idents, meta)
    new = Version(major, minor, patch, (*pre, "1"), meta)
    if compare(new, version) <= 0:
        raise ValueError(
            f"'{new}' would have lower or equal precedence than '{version}'"
        )
    return new


def _record(text: str, version: Version | None, note: str, error: str) -> dict:
    if version is None:
        return {"version": text, "valid": False, "error": error}
    return {
        "version": text,
        "valid": True,
        "major": version.major,
        "minor": version.minor,
        "patch": version.patch,
        "prerelease": list(version.prerelease),
        "build": list(version.build),
        "notes": [note] if note else [],
    }


def _git_tags() -> list[str]:
    try:
        result = subprocess.run(
            ["git", "tag", "--list"], capture_output=True, text=True, check=False
        )
    except OSError as error:
        raise UsageError(f"--from-tags: cannot run git: {error}") from error
    if result.returncode:
        raise UsageError(f"--from-tags: git tag failed: {result.stderr.strip()}")
    return result.stdout.split()


def _print_bounded(lines: Sequence[str]) -> None:
    for line in lines[:MAX_LINES]:
        print(line)
    if len(lines) > MAX_LINES:
        print(f"... {len(lines) - MAX_LINES} more lines; use --json for all")


def cmd_check(args: argparse.Namespace) -> int:
    items: list[tuple[str, bool]] = [(v, False) for v in args.versions]
    if args.from_tags:
        items += [(t, True) for t in _git_tags()]
    elif not items:
        raise UsageError("check needs VERSION... or --from-tags")
    records = []
    for text, is_tag in items:
        try:
            version, note = from_tag(text) if is_tag else (parse(text), "")
            records.append(_record(text, version, note, ""))
        except ValueError as error:
            records.append(_record(text, None, "", str(error)))
    invalid = sum(not r["valid"] for r in records)
    if args.json:
        print(json.dumps(records, indent=2))
    else:
        lines = [
            f"PASS  {r['version']}" + (f"  ({r['notes'][0]})" if r["notes"] else "")
            if r["valid"]
            else f"FAIL  {r['version']}  - {r['error']}"
            for r in records
        ]
        _print_bounded([*lines, f"{len(records) - invalid}/{len(records)} valid"])
    return int(invalid > 0)


def cmd_compare(args: argparse.Namespace) -> int:
    result = compare(parse(args.a), parse(args.b))
    print("<=>"[result + 1])
    return 0


def cmd_sort(args: argparse.Namespace) -> int:
    ordered = [str(v) for v in sort_versions(args.versions)]
    if args.json:
        print(json.dumps(ordered))
    else:
        _print_bounded(ordered)
    return 0


def cmd_bump(args: argparse.Namespace) -> int:
    print(bump(parse(args.version), args.part, args.pre_id, args.build))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="semver.py",
        description=(
            "Check, compare, sort, and bump Semantic Versioning 2.0.0 "
            "versions. Standard library only; never prompts."
        ),
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="validate versions or git tags")
    check.add_argument("versions", nargs="*", metavar="VERSION")
    check.add_argument("--from-tags", action="store_true", help="also check git tags")
    check.add_argument("--json", action="store_true", help="print a JSON list")
    check.set_defaults(run=cmd_check)
    comp = sub.add_parser("compare", help="print <, =, or > by precedence")
    comp.add_argument("a", metavar="A")
    comp.add_argument("b", metavar="B")
    comp.set_defaults(run=cmd_compare)
    srt = sub.add_parser("sort", help="sort versions by precedence")
    srt.add_argument("versions", nargs="+", metavar="VERSION")
    srt.add_argument("--json", action="store_true", help="print a JSON list")
    srt.set_defaults(run=cmd_sort)
    bmp = sub.add_parser("bump", help="compute the next version")
    bmp.add_argument("version", metavar="VERSION")
    bmp.add_argument("part", choices=PARTS)
    bmp.add_argument(
        "--pre-id", metavar="ID", help="pre-release identifier(s), e.g. rc"
    )
    bmp.add_argument("--build", metavar="META", help="build metadata, e.g. sha.0a1b2c3")
    bmp.set_defaults(run=cmd_bump)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.run(args)
    except UsageError as error:
        print(f"semver.py: usage error: {error}", file=sys.stderr)
        return 2
    except ValueError as error:
        print(f"semver.py: {error}; see {SPEC}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
