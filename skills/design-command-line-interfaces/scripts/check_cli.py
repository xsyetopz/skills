#!/usr/bin/env python3
"""Probe a command-line program from outside and report convention breaks.

Runs the command several times with stdin, stdout, and stderr as pipes (as
in a script or CI) and checks what it prints and how it exits:

  help-long         `CMD --help` exits 0 and prints help to stdout
  help-short        `CMD -h` exits 0 and prints help to stdout
  help-usage        help output contains the word "usage" (warning)
  sub-help          `CMD SUB --help` exits 0 for each --sub SUB
  unknown-flag      an unknown flag exits non-zero, writes to stderr, not stdout
  stack-trace       no probe run prints a stack trace
  version           `CMD --version` exits 0 and prints to stdout (warning)
  ansi-when-piped   no ANSI escape sequences when output is not a terminal
  bare-noninteractive  bare `CMD` with stdin from /dev/null finishes in time
  bare-terminal     bare `CMD` with stdin on a terminal (pty) finishes in time
                    (warning; skipped where pty is unavailable)

Use --skip ID to disable a probe the program deliberately does not follow,
for example `--skip bare-terminal` for a program that is interactive by
default. Every probe runs with NO_COLOR unset and TERM=xterm-256color, so a
program that colors unconditionally is caught.

Usage: check_cli.py [--sub SUB]... [--skip ID]... [--timeout S] [--json]
                    [--strict] -- COMMAND [ARG...]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import select
import subprocess
import sys
import time
from dataclasses import asdict, dataclass

EPILOG = """\
Exit status:
  0  no errors (warnings allowed unless --strict)
  1  errors found, or warnings with --strict
  2  bad usage, or COMMAND could not be started

Example:
  check_cli.py --sub add --sub list -- python3 todo.py
"""

UNKNOWN_FLAG = "--no-such-flag-for-cli-check"
ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
TRACE = re.compile(
    r"Traceback \(most recent call last\)"  # Python
    r"|^goroutine \d+ \[running\]"  # Go
    r"|^panicked at |thread '.*' panicked"  # Rust
    r"|^\s+at .+\(.+:\d+:\d+\)$"  # Node, Deno, Bun
    r"|^\s+at [\w$.]+\(\w+\.java:\d+\)$",  # JVM
    re.MULTILINE,
)
PROBES = (
    "help-long",
    "help-short",
    "help-usage",
    "sub-help",
    "unknown-flag",
    "stack-trace",
    "version",
    "ansi-when-piped",
    "bare-noninteractive",
    "bare-terminal",
)


@dataclass
class Finding:
    probe: str
    severity: str  # "error" or "warning"
    message: str


@dataclass
class Run:
    args: list[str]
    code: int | None  # None: timed out and killed
    out: str
    err: str


def environment() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in {"NO_COLOR", "CI"}}
    env["TERM"] = "xterm-256color"
    return env


def run(command: list[str], extra: list[str], timeout: float) -> Run:
    args = [*command, *extra]
    try:
        done = subprocess.run(
            args,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            env=environment(),
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        return Run(args, None, _text(error.stdout), _text(error.stderr))
    return Run(args, done.returncode, done.stdout, done.stderr)


def _text(data: bytes | str | None) -> str:
    if isinstance(data, bytes):
        return data.decode(errors="replace")
    return data or ""


def run_on_pty(command: list[str], timeout: float) -> Run | None:
    """Run bare COMMAND with stdin on a pseudo-terminal; None if unsupported."""
    try:
        import pty
    except ImportError:
        return None
    leader, follower = pty.openpty()
    try:
        proc = subprocess.Popen(
            command,
            stdin=follower,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment(),
        )
    finally:
        os.close(follower)
    deadline = time.monotonic() + timeout
    try:
        while proc.poll() is None and time.monotonic() < deadline:
            # Drain the terminal so a program that echoes cannot block on it.
            ready, _, _ = select.select([leader], [], [], 0.05)
            if ready:
                try:
                    os.read(leader, 4096)
                except OSError:
                    break
        if proc.poll() is None:
            proc.kill()
            out, err = proc.communicate()
            return Run(command, None, _text(out), _text(err))
        out, err = proc.communicate()
        return Run(command, proc.returncode, _text(out), _text(err))
    finally:
        os.close(leader)


def show(result: Run) -> str:
    return " ".join(result.args)


def check_help(result: Run, probe: str) -> list[Finding]:
    if result.code is None:
        return [Finding(probe, "error", f"`{show(result)}` did not finish")]
    if result.code != 0:
        return [
            Finding(probe, "error", f"`{show(result)}` exited {result.code}, not 0")
        ]
    if not result.out.strip():
        where = "stderr" if result.err.strip() else "nowhere"
        return [
            Finding(
                probe, "error", f"`{show(result)}` printed help to {where}, not stdout"
            )
        ]
    if "usage" not in result.out.lower():
        return [
            Finding(
                "help-usage",
                "warning",
                f"`{show(result)}` output has no usage line; is it help at all?",
            )
        ]
    return []


def check_unknown_flag(result: Run) -> list[Finding]:
    found: list[Finding] = []
    label = f"`{show(result)}`"
    if result.code is None:
        return [Finding("unknown-flag", "error", f"{label} did not finish")]
    if result.code == 0:
        found.append(Finding("unknown-flag", "error", f"{label} exited 0"))
    if not result.err.strip():
        found.append(
            Finding("unknown-flag", "error", f"{label} wrote nothing to stderr")
        )
    if result.out.strip():
        found.append(
            Finding("unknown-flag", "error", f"{label} wrote the error to stdout")
        )
    return found


def check(
    command: list[str], subs: list[str], skip: set[str], timeout: float
) -> list[Finding]:
    found: list[Finding] = []
    runs: list[Run] = []

    def probe(extra: list[str]) -> Run:
        result = run(command, extra, timeout)
        runs.append(result)
        return result

    if "help-long" not in skip:
        found += check_help(probe(["--help"]), "help-long")
    if "help-short" not in skip:
        found += check_help(probe(["-h"]), "help-short")
    if "sub-help" not in skip:
        for sub in subs:
            found += check_help(probe([sub, "--help"]), "sub-help")
    if "unknown-flag" not in skip:
        found += check_unknown_flag(probe([UNKNOWN_FLAG]))
    if "version" not in skip:
        ver = probe(["--version"])
        if ver.code != 0 or not ver.out.strip():
            found.append(
                Finding(
                    "version",
                    "warning",
                    f"`{show(ver)}` exited {ver.code} with stdout "
                    f"{'empty' if not ver.out.strip() else 'set'}",
                )
            )
    if "bare-noninteractive" not in skip:
        bare = probe([])
        if bare.code is None:
            found.append(
                Finding(
                    "bare-noninteractive",
                    "error",
                    f"`{show(bare)}` with stdin from /dev/null did not finish "
                    f"in {timeout:g}s (waiting for a prompt or input?)",
                )
            )
    if "stack-trace" not in skip:
        for result in runs:
            if TRACE.search(result.out + result.err):
                found.append(
                    Finding(
                        "stack-trace",
                        "error",
                        f"`{show(result)}` printed a stack trace",
                    )
                )
    if "ansi-when-piped" not in skip:
        for result in runs:
            if ANSI.search(result.out) or ANSI.search(result.err):
                found.append(
                    Finding(
                        "ansi-when-piped",
                        "error",
                        f"`{show(result)}` printed ANSI escapes to a pipe",
                    )
                )
    if "bare-terminal" not in skip:
        tty = run_on_pty(command, timeout)
        if tty is not None and tty.code is None:
            found.append(
                Finding(
                    "bare-terminal",
                    "warning",
                    f"`{show(tty)}` with stdin on a terminal did not finish in "
                    f"{timeout:g}s; show usage instead of waiting for input",
                )
            )
    return [f for f in found if f.probe not in skip]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="check_cli.py",
        description="Probe a command-line program and report convention breaks.",
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--sub",
        action="append",
        default=[],
        metavar="SUB",
        help="subcommand whose --help to check (repeatable)",
    )
    parser.add_argument(
        "--skip",
        action="append",
        default=[],
        choices=PROBES,
        metavar="ID",
        help="probe to skip (repeatable)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        metavar="S",
        help="seconds per run before it counts as hung (default 5)",
    )
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    parser.add_argument("--strict", action="store_true", help="exit 1 on warnings too")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- COMMAND [ARG...]")
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("missing COMMAND; put it after --")
    try:
        found = check(command, args.sub, set(args.skip), args.timeout)
    except OSError as error:
        print(
            f"check_cli.py: cannot run {command[0]}: {error.strerror}", file=sys.stderr
        )
        return 2
    if args.json:
        print(json.dumps([asdict(f) for f in found], indent=2))
    else:
        for f in found:
            print(f"{f.severity.upper():7} {f.probe}: {f.message}", flush=True)
        errors = sum(f.severity == "error" for f in found)
        print(f"{errors} error(s), {len(found) - errors} warning(s)", file=sys.stderr)
    failing = [f for f in found if args.strict or f.severity == "error"]
    return 1 if failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
