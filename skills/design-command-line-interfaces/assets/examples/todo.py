#!/usr/bin/env python3
"""todo: a small task list that follows the command-line conventions.

Shows: help on -h/--help for every level, concise usage when run bare,
stdout for data and stderr for messages, exit codes 0/1/2/130, --json,
color only on a terminal (NO_COLOR, TERM=dumb, --no-color), `-` for stdin,
--no-input and --force for non-interactive deletes, flag > environment >
default precedence, and a renamed subcommand kept as a warned alias.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path
from typing import Any

VERSION = "todo 1.4.0"
DOCS = "https://example.com/todo/docs"

EXAMPLES = """\
examples:
  todo add "write release notes"     add one task
  git log --format=%s | todo add -   add one task per input line
  todo list --json | jq '.[].title'  read tasks from a script
  todo remove 3 --force              delete without a prompt

docs: https://example.com/todo/docs
"""


GLOBAL_DEFAULTS = {"store": None, "quiet": False, "no_color": False, "no_input": False}


class UsageError(Exception):
    """Wrong invocation; exit 2."""


def color_enabled(args: argparse.Namespace, stream) -> bool:
    return (
        not args.no_color
        and not os.environ.get("NO_COLOR")
        and os.environ.get("TERM") != "dumb"
        and stream.isatty()
    )


def store_path(args: argparse.Namespace) -> Path:
    if args.store:
        return Path(args.store)
    if os.environ.get("TODO_STORE"):
        return Path(os.environ["TODO_STORE"])
    data = os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share"
    return Path(data) / "todo/tasks.json"


def load(path: Path) -> list[dict]:
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        raise RuntimeError(
            f"{path} is not valid JSON (line {error.lineno}); fix or move it, "
            "then run the command again"
        ) from error


def save(path: Path, tasks: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(tasks, indent=2) + "\n")
    tmp.replace(path)  # atomic: an interrupted run never leaves half a file


def cmd_add(args: argparse.Namespace) -> int:
    titles = [line.strip() for line in sys.stdin] if args.title == "-" else [args.title]
    titles = [t for t in titles if t]
    if not titles:
        raise UsageError("no task title given; pass TITLE, or `-` to read stdin")
    path = store_path(args)
    tasks = load(path)
    next_id = max((t["id"] for t in tasks), default=0) + 1
    for offset, title in enumerate(titles):
        tasks.append({"id": next_id + offset, "title": title})
    save(path, tasks)
    if not args.quiet:
        print(f"Added {len(titles)} task(s) to {path}", file=sys.stderr)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    tasks = load(store_path(args))
    if args.json:
        print(json.dumps(tasks, indent=2))
        return 0
    bold = color_enabled(args, sys.stdout)
    for task in tasks:
        num = f"\x1b[1m{task['id']}\x1b[0m" if bold else str(task["id"])
        print(f"{num}\t{task['title']}")
    if not tasks and not args.quiet:
        print("No tasks. Add one with: todo add TITLE", file=sys.stderr)
    return 0


def cmd_remove(args: argparse.Namespace) -> int:
    if args.renamed_from:
        print(
            f"warning: `todo {args.renamed_from}` is deprecated and will be removed "
            "in todo 2.0; use `todo remove`",
            file=sys.stderr,
        )
    path = store_path(args)
    tasks = load(path)
    match = [t for t in tasks if t["id"] == args.id]
    if not match:
        raise RuntimeError(f"no task with id {args.id}; run `todo list` to see ids")
    if not args.force:
        if args.no_input or not sys.stdin.isatty():
            raise UsageError(
                f"refusing to delete task {args.id} without confirmation; "
                "pass --force to delete without a prompt"
            )
        answer = input(f"Delete task {args.id} ({match[0]['title']!r})? [y/N] ")
        if answer.strip().lower() not in {"y", "yes"}:
            print("Nothing deleted.", file=sys.stderr)
            return 1
    save(path, [t for t in tasks if t["id"] != args.id])
    if not args.quiet:
        print(f"Deleted task {args.id}", file=sys.stderr)
    return 0


def parser() -> argparse.ArgumentParser:
    # Global flags work before or after the subcommand. SUPPRESS keeps a
    # subparser from overwriting a value given before the subcommand with
    # its own default. Defaults are applied after parsing (GLOBAL_DEFAULTS):
    # parents= shares Action objects, so set_defaults on one parser would
    # change them for every subparser too.
    common = argparse.ArgumentParser(add_help=False, argument_default=argparse.SUPPRESS)
    common.add_argument(
        "--store",
        metavar="FILE",
        help="task file (env TODO_STORE; default XDG data dir)",
    )
    common.add_argument(
        "-q", "--quiet", action="store_true", help="print only requested data"
    )
    common.add_argument("--no-color", action="store_true", help="disable color")
    common.add_argument("--no-input", action="store_true", help="never prompt")

    top = argparse.ArgumentParser(
        prog="todo",
        description="Keep a task list in a JSON file.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        parents=[common],
    )
    top.add_argument("--version", action="version", version=VERSION)
    subs = top.add_subparsers(dest="command", metavar="COMMAND")

    add = subs.add_parser(
        "add",
        parents=[common],
        help="add a task",
        description="Add a task. TITLE `-` reads one task per stdin line.",
    )
    add.add_argument("title", metavar="TITLE")
    add.set_defaults(run=cmd_add)

    lst = subs.add_parser(
        "list",
        parents=[common],
        help="list tasks",
        description="List tasks, one per line: ID<TAB>TITLE.",
    )
    lst.add_argument("--json", action="store_true", help="print tasks as JSON")
    lst.set_defaults(run=cmd_list)

    for name in ("remove", "rm"):
        # No help= for the old name: argparse prints help=SUPPRESS literally
        # as "==SUPPRESS==" in the command list instead of hiding it.
        extra: dict[str, Any] = {"help": "delete a task"} if name == "remove" else {}
        rem = subs.add_parser(
            name,
            parents=[common],
            **extra,
            description="Delete a task. Prompts on a terminal unless --force.",
        )
        rem.add_argument("id", type=int, metavar="ID")
        rem.add_argument(
            "-f", "--force", action="store_true", help="delete without a prompt"
        )
        rem.set_defaults(run=cmd_remove, renamed_from="rm" if name == "rm" else None)
    return top


def main(argv: list[str] | None = None) -> int:
    top = parser()
    args = top.parse_args(argv)
    for name, value in GLOBAL_DEFAULTS.items():
        vars(args).setdefault(name, value)
    if not args.command:
        top.print_usage(sys.stderr)
        print("Run `todo --help` for commands and examples.", file=sys.stderr)
        return 2
    try:
        return args.run(args)
    except UsageError as error:
        print(f"todo: {error}", file=sys.stderr)
        return 2
    except (RuntimeError, OSError) as error:
        print(f"todo: {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\ntodo: interrupted", file=sys.stderr)
        return 130
    except Exception:  # noqa: BLE001 - last resort: summarize, keep the trace
        with tempfile.NamedTemporaryFile(
            "w", prefix="todo-crash-", suffix=".log", delete=False
        ) as log:
            traceback.print_exc(file=log)
        print(
            f"todo: internal error ({VERSION}); details in {log.name}\n"
            f"Please report it with that file at {DOCS}/issues",
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
