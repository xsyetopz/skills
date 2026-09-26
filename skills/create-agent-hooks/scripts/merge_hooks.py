#!/usr/bin/env python3
"""Add or remove exactly one hook handler in a host's configuration file.

Everything else in the file (other events, other handlers, other
settings such as permissions) is kept as it was. Adding an entry that is
already present changes nothing, and removing it again restores the
original content, so the same command line is both install and rollback.

Layouts:
  claude, codex, gemini   hooks.EVENT = [{"matcher": M, "hooks": [HANDLER]}]
  cursor, copilot         {"version": 1, "hooks": {"EVENT": [HANDLER]}}
                          (a matcher, if any, sits inside HANDLER)
  vscode                  {"hooks": {"EVENT": [HANDLER]}}

Usage:
  merge_hooks.py FILE --host HOST --event EVENT --handler JSON
                 [--matcher M] [--remove] [--dry-run]
Exit status: 0 written (or nothing to do), 1 --remove found no such
entry, 2 bad input.
"""

from __future__ import annotations

import argparse
import copy
import difflib
import json
import sys
from pathlib import Path

NESTED = {"claude", "codex", "gemini"}
VERSIONED = {"cursor", "copilot"}
EPILOG = """\
Exit status:
  0  written, previewed with --dry-run, or already present (nothing to do)
  1  --remove found no such entry (the file is left as it was)
  2  bad input: --handler or FILE is not a JSON object, or FILE's hooks
     do not have the host's layout (nothing is written)

Output: "added to FILE", "removed from FILE", or "already present; nothing
to do". --dry-run writes nothing and prints a unified diff instead (empty
when nothing would change). --json prints one object instead of the text:
{"file", "action": "add"|"remove", "changed", "written", "diff"}; "diff"
is the unified diff text ("" when unchanged). Running the same add twice
changes nothing the second time; --remove with the same arguments undoes it.

Examples:
  python3 scripts/merge_hooks.py .claude/settings.json --host claude \\
      --event PreToolUse --matcher Bash \\
      --handler '{"type":"command","command":"python3 .agent-hooks/guard.py"}' \\
      --dry-run
  python3 scripts/merge_hooks.py .cursor/hooks.json --host cursor \\
      --event preToolUse --handler '{"command":"./hooks/guard.sh"}' --remove
"""


def add(
    config: dict, host: str, event: str, matcher: str | None, handler: dict
) -> bool:
    hooks = config.setdefault("hooks", {})
    entries = hooks.setdefault(event, [])
    if host not in NESTED:
        entry = dict(handler, **({"matcher": matcher} if matcher else {}))
        if entry in entries:
            return False
        entries.append(entry)
        return True
    for group in entries:
        if group.get("matcher") == matcher:
            if handler in group.setdefault("hooks", []):
                return False
            group["hooks"].append(handler)
            return True
    group: dict = {"matcher": matcher} if matcher is not None else {}
    group["hooks"] = [handler]
    entries.append(group)
    return True


def remove(
    config: dict, host: str, event: str, matcher: str | None, handler: dict
) -> bool:
    entries = config.get("hooks", {}).get(event, [])
    removed = False
    if host not in NESTED:
        entry = dict(handler, **({"matcher": matcher} if matcher else {}))
        if entry in entries:
            entries.remove(entry)
            removed = True
    else:
        for group in list(entries):
            if group.get("matcher") == matcher and handler in group.get("hooks", []):
                group["hooks"].remove(handler)
                removed = True
                if not group["hooks"]:
                    entries.remove(group)
    if removed and not entries:
        del config["hooks"][event]
    if removed and not config["hooks"]:
        del config["hooks"]  # the add created it; leave no empty object
    return removed


def shape_error(config: dict, host: str, event: str, matcher: str | None) -> str | None:
    """Describe why add/remove cannot edit this layout, or None.

    Groups for other matchers are left alone, whatever their "hooks" holds.
    """
    hooks = config.get("hooks", {})
    if not isinstance(hooks, dict):
        return '"hooks" must be an object'
    entries = hooks.get(event, [])
    if not isinstance(entries, list):
        return f"hooks.{event} must be a list"
    if host in NESTED:
        for index, group in enumerate(entries):
            if not isinstance(group, dict):
                return f"hooks.{event}[{index}] must be an object"
            if group.get("matcher") == matcher and not isinstance(
                group.get("hooks", []), list
            ):
                return f"hooks.{event}[{index}].hooks must be a list"
    return None


def render(config: dict) -> str:
    return json.dumps(config, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", type=Path, help="host configuration file")
    parser.add_argument(
        "--host", required=True, choices=sorted(NESTED | VERSIONED | {"vscode"})
    )
    parser.add_argument(
        "--event", required=True, help="event name, as the host spells it"
    )
    parser.add_argument("--handler", required=True, help="handler as JSON")
    parser.add_argument("--matcher", help="matcher for the entry (default: none)")
    parser.add_argument("--remove", action="store_true", help="roll the entry back")
    parser.add_argument(
        "--dry-run", action="store_true", help="print a diff; write nothing"
    )
    parser.add_argument(
        "--json", action="store_true", help="print one JSON result on stdout"
    )
    args = parser.parse_args(argv)
    try:
        handler = json.loads(args.handler)
    except ValueError as error:
        print(f"error: --handler is not valid JSON: {error}", file=sys.stderr)
        return 2
    try:
        before_text = (
            args.file.read_text(encoding="utf-8") if args.file.exists() else ""
        )
        config = json.loads(before_text) if before_text.strip() else {}
    except (OSError, ValueError) as error:
        print(f"error: {args.file}: {error}", file=sys.stderr)
        return 2
    if not isinstance(handler, dict):
        print("error: --handler must be a JSON object", file=sys.stderr)
        return 2
    if not isinstance(config, dict):
        print(f"error: {args.file} must contain a JSON object", file=sys.stderr)
        return 2
    problem = shape_error(config, args.host, args.event, args.matcher)
    if problem:
        print(f"error: {args.file}: {problem}", file=sys.stderr)
        return 2
    updated = copy.deepcopy(config)
    if args.host in VERSIONED:
        updated.setdefault("version", 1)
    action = "remove" if args.remove else "add"
    if args.remove:
        changed = remove(updated, args.host, args.event, args.matcher, handler)
    else:
        changed = add(updated, args.host, args.event, args.matcher, handler)
    after_text = render(updated)
    diff = "".join(
        difflib.unified_diff(
            before_text.splitlines(True),
            after_text.splitlines(True),
            str(args.file),
            f"{args.file} (updated)",
        )
    )
    written = False

    def report() -> None:
        if args.json:
            result = {
                "file": str(args.file),
                "action": action,
                "changed": changed,
                "written": written,
                "diff": diff if changed else "",
            }
            print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.remove and not changed:
        print("no matching entry to remove", file=sys.stderr)
        report()
        return 1
    if not changed and before_text:
        if args.json:
            report()
        else:
            print("already present; nothing to do")
        return 0
    if args.dry_run:
        if args.json:
            report()
        else:
            sys.stdout.write(diff)
        return 0
    args.file.parent.mkdir(parents=True, exist_ok=True)
    args.file.write_text(after_text, encoding="utf-8")
    written = True
    if args.json:
        report()
    else:
        print(f"{'removed from' if args.remove else 'added to'} {args.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
