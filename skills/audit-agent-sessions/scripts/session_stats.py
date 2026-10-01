#!/usr/bin/env python3
"""Count tokens, estimated cost, and repeated work in Claude Code transcripts.

PATH is a transcript file (`<session>.jsonl`) or a directory searched
recursively for `*.jsonl`, such as `~/.claude/projects/<project>/`. Files
under a `subagents/` directory count as subagent work; all others count as
the main conversation. Set-aside `*.orphaned-*.jsonl` copies are skipped.

The transcript line format is undocumented and may change. This script reads
only these fields: `type`, `message.id`, `message.model`, `message.usage`,
`message.content[]` tool calls (`name`, `id`, `input`) and tool results
(`tool_use_id`, `content`), and `toolUseResult.stdout`/`stderr`.

It prints counts, paths, and only the program name of repeated commands. It
never prints message text or command output.

  tokens      input, cache writes (5m, 1h), cache reads, and output per model
              and per main or subagent, counted once per `message.id`
  cost        tokens times the prices in the `--prices FILE` JSON (standard
              rates only); without the flag, tokens only and no cost
  commands    Bash commands run more than once in one transcript with
              identical output
  reads       Read calls repeating an earlier Read of the same path, offset,
              and limit in one transcript, with no Edit, MultiEdit, Write,
              or NotebookEdit of that path in between (Bash edits are not
              seen)

`--prices FILE` holds a JSON object mapping a model id (matched by longest
prefix) to per-million-token prices, for example:

  {"my-model": {"input": 1.0, "output": 5.0, "cache_write": 1.25,
                "cache_read": 0.10}}

Cache writes of both lifetimes use `cache_write`. Take the prices from the
provider's current price page; this script carries none.

Usage: session_stats.py PATH [--json] [--top N] [--prices FILE]
Exit status: 0 success, 2 bad input.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

PRICE_FIELDS = ("input", "cache_write", "cache_read", "output")
TOKEN_FIELDS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output")
EDIT_TOOLS = {"Edit", "MultiEdit", "Write", "NotebookEdit"}
UNPARSED = "(unparsed)"
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
SAFE_WORD = re.compile(r"[\w./+:@%-]+")


def program_name(command: str) -> str:
    """First shell word that is not `export`, `env` or its options, or NAME=value.

    A bare `export X=1` or `env` names itself. Anything that shlex cannot
    split, or a result with shell syntax left in it (as from `$(...)`), gives
    `(unparsed)`, so part of an assignment value is never returned.
    """
    try:
        words = shlex.split(command.replace("\\\n", " "))
    except ValueError:
        return UNPARSED
    lead = ""
    index = 0
    while index < len(words):
        word = words[index]
        if ASSIGNMENT.match(word):
            index += 1
        elif word in ("export", "env"):
            lead = lead or word
            index += 1
        elif lead == "env" and word.startswith("-"):
            index += 2 if word in ("-u", "-C", "-S") else 1
        else:
            return word if SAFE_WORD.fullmatch(word) else UNPARSED
    return lead


def load_prices(path: Path) -> dict[str, dict[str, float]]:
    """Read a model-id to per-million-token price mapping; raise ValueError."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot read prices from {path}: {exc}") from exc
    if not isinstance(data, dict) or not data:
        raise ValueError(f"{path} must hold a JSON object of model ids to prices")
    for model, price in data.items():
        if not isinstance(price, dict) or any(
            isinstance(price.get(f), bool) or not isinstance(price.get(f), (int, float))
            for f in PRICE_FIELDS
        ):
            raise ValueError(
                f"{path}: {model!r} needs numeric {', '.join(PRICE_FIELDS)}"
            )
    return data


def price_for(
    model: str, prices: dict[str, dict[str, float]]
) -> dict[str, float] | None:
    matches = [prefix for prefix in prices if model.startswith(prefix)]
    return prices[max(matches, key=len)] if matches else None


def token_cost(counts: Counter[str], price: dict[str, float]) -> float:
    cache_write = counts["cache_write_5m"] + counts["cache_write_1h"]
    return round(
        (
            counts["input"] * price["input"]
            + cache_write * price["cache_write"]
            + counts["cache_read"] * price["cache_read"]
            + counts["output"] * price["output"]
        )
        / 1e6,
        4,
    )


def usage_tokens(usage: dict[str, Any]) -> dict[str, int]:
    split = usage.get("cache_creation") or {}
    write_5m = split.get("ephemeral_5m_input_tokens")
    write_1h = split.get("ephemeral_1h_input_tokens")
    if write_5m is None and write_1h is None:
        write_5m, write_1h = usage.get("cache_creation_input_tokens") or 0, 0
    return {
        "input": usage.get("input_tokens") or 0,
        "cache_write_5m": write_5m or 0,
        "cache_write_1h": write_1h or 0,
        "cache_read": usage.get("cache_read_input_tokens") or 0,
        "output": usage.get("output_tokens") or 0,
    }


def result_text(row: dict[str, Any], block: dict[str, Any]) -> str:
    extra = row.get("toolUseResult")
    if isinstance(extra, dict) and ("stdout" in extra or "stderr" in extra):
        return f"{extra.get('stdout', '')}\0{extra.get('stderr', '')}"
    return json.dumps(block.get("content"), sort_keys=True)


def transcript_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(p for p in path.rglob("*.jsonl") if ".orphaned-" not in p.name)


def scan(
    paths: list[Path], top: int, prices: dict[str, dict[str, float]] | None
) -> dict[str, Any]:
    tokens: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    seen_ids: set[str] = set()
    repeated_commands: list[dict[str, Any]] = []
    repeated_reads: list[dict[str, Any]] = []
    bad_lines = 0
    nonstandard_rows = 0

    for path in paths:
        scope = "subagent" if "subagents" in path.parts else "main"
        commands: dict[str, str] = {}
        runs: Counter[tuple[str, str]] = Counter()
        read_keys: dict[str, set[tuple[Any, Any]]] = defaultdict(set)
        rereads: Counter[str] = Counter()
        with path.open(encoding="utf-8", errors="replace") as handle:
            for line in handle:
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    bad_lines += 1
                    continue
                if not isinstance(row, dict):
                    bad_lines += 1
                    continue
                message = row.get("message")
                if not isinstance(message, dict):
                    continue
                content = message.get("content")
                blocks = content if isinstance(content, list) else []
                if row.get("type") == "assistant":
                    msg_id = message.get("id")
                    usage = message.get("usage")
                    if isinstance(usage, dict) and msg_id not in seen_ids:
                        if msg_id:
                            seen_ids.add(msg_id)
                        model = str(message.get("model") or "unknown")
                        tokens[(model, scope)].update(usage_tokens(usage))
                        if usage.get("speed") not in (None, "standard") or (
                            usage.get("inference_geo") == "us"
                        ):
                            nonstandard_rows += 1
                    for block in blocks:
                        if (
                            not isinstance(block, dict)
                            or block.get("type") != "tool_use"
                        ):
                            continue
                        name = block.get("name")
                        args = block.get("input") or {}
                        if name == "Bash" and "command" in args:
                            commands[str(block.get("id"))] = str(args["command"])
                        elif name == "Read" and "file_path" in args:
                            key = (args.get("offset"), args.get("limit"))
                            file_path = str(args["file_path"])
                            if key in read_keys[file_path]:
                                rereads[file_path] += 1
                            read_keys[file_path].add(key)
                        elif name in EDIT_TOOLS:
                            target = args.get("file_path") or args.get("notebook_path")
                            read_keys.pop(str(target), None)
                elif row.get("type") == "user":
                    for block in blocks:
                        if (
                            not isinstance(block, dict)
                            or block.get("type") != "tool_result"
                        ):
                            continue
                        command = commands.get(str(block.get("tool_use_id")))
                        if command is not None:
                            digest = hashlib.sha256(
                                result_text(row, block).encode()
                            ).hexdigest()
                            runs[(command, digest)] += 1
        for (command, _), count in runs.items():
            if count > 1:
                head = program_name(command) or "(none)"
                repeated_commands.append(
                    {"transcript": str(path), "command_head": head, "runs": count}
                )
        for file_path, count in rereads.items():
            repeated_reads.append(
                {"transcript": str(path), "path": file_path, "rereads": count}
            )

    rows = []
    unpriced: set[str] = set()
    for (model, scope), counts in sorted(tokens.items()):
        cost = None
        if prices is not None:
            price = price_for(model, prices)
            if price is None:
                if any(counts.values()):
                    unpriced.add(model)
            else:
                cost = token_cost(counts, price)
        rows.append(
            {"model": model, "scope": scope, **{f: counts[f] for f in TOKEN_FIELDS}}
            | {"cost_usd": cost}
        )
    repeated_commands.sort(key=lambda r: -r["runs"])
    repeated_reads.sort(key=lambda r: -r["rereads"])
    return {
        "transcripts": len(paths),
        "bad_lines": bad_lines,
        "nonstandard_rate_rows": nonstandard_rows,
        "unpriced_models": sorted(unpriced),
        "tokens": rows,
        "total_cost_usd": (
            None if prices is None else round(sum(r["cost_usd"] or 0 for r in rows), 4)
        ),
        "repeated_commands_total": sum(r["runs"] - 1 for r in repeated_commands),
        "repeated_commands": repeated_commands[:top],
        "repeated_reads_total": sum(r["rereads"] for r in repeated_reads),
        "repeated_reads": repeated_reads[:top],
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"transcripts: {report['transcripts']}  bad lines: {report['bad_lines']}")
    priced = report["total_cost_usd"] is not None
    header = ("model", "scope", *TOKEN_FIELDS, *(("cost_usd",) if priced else ()))
    print("\t".join(header))
    for row in report["tokens"]:
        print("\t".join(str(row[h]) for h in header))
    if priced:
        print(f"estimated total: ${report['total_cost_usd']}")
    else:
        print("cost: not computed; pass --prices FILE to price tokens")
    if report["unpriced_models"]:
        print("not priced: " + ", ".join(report["unpriced_models"]))
    if report["nonstandard_rate_rows"]:
        print(
            f"{report['nonstandard_rate_rows']} rows used fast mode or US-only "
            "inference; their cost is understated"
        )
    print(
        f"repeated commands with identical output: {report['repeated_commands_total']}"
    )
    for row in report["repeated_commands"]:
        print(f"  {row['runs']}x  {row['command_head']}  {row['transcript']}")
    print(f"re-reads of an unchanged file: {report['repeated_reads_total']}")
    for row in report["repeated_reads"]:
        print(f"  {row['rereads']}x  {row['path']}  {row['transcript']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("path", type=Path, help="transcript file or directory")
    parser.add_argument("--json", action="store_true", help="print one JSON object")
    parser.add_argument(
        "--top", type=int, default=10, help="rows per repeat list (default 10)"
    )
    parser.add_argument(
        "--prices",
        type=Path,
        metavar="FILE",
        help="JSON: model id -> input, output, cache_write, cache_read "
        "USD per million tokens (default: report tokens only)",
    )
    args = parser.parse_args(argv)
    if not args.path.exists():
        print(
            f"error: {args.path} does not exist; pass a directory such as "
            "~/.claude/projects/<project>/ or a <session>.jsonl file",
            file=sys.stderr,
        )
        return 2
    paths = transcript_files(args.path)
    if not paths:
        print(f"error: no *.jsonl transcripts under {args.path}", file=sys.stderr)
        return 2
    prices = None
    if args.prices is not None:
        try:
            prices = load_prices(args.prices)
        except ValueError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
    report = scan(paths, args.top, prices)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
