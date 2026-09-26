#!/usr/bin/env python3
"""Check an agent hook configuration file against its host's documented rules.

Checks (errors unless marked warning):
  - the file is a JSON object with a "hooks" object (and version 1 for
    Cursor and Copilot files);
  - every event name exists for that host (catches invented or
    wrong-case names such as Cursor "PreToolUse" or Codex "BeforeTool");
  - handler types the host supports; Codex skips prompt/agent (warning);
  - matchers compile as regular expressions; a matcher on an event that
    ignores it (warning); Gemini lifecycle matchers are exact strings, so
    "a|b" never matches (warning);
  - timeout units: Gemini uses milliseconds, so a value below 100 is
    probably seconds (warning); Codex SessionEnd/Interrupt allow <= 3 s;
  - every script path in a command exists under --project, after
    replacing ${CLAUDE_PROJECT_DIR}, $GEMINI_PROJECT_DIR, and
    $(git rev-parse --show-toplevel).

Event lists come from the hosts' hook references (fetched 2026-09-25):
code.claude.com/docs/en/hooks, developers.openai.com/codex/hooks,
geminicli.com/docs/hooks/reference, cursor.com/docs/hooks,
docs.github.com/en/copilot/reference/hooks-reference,
code.visualstudio.com/docs/agent-customization/hooks.

Usage: check_hook_config.py FILE --host HOST [--project DIR] [--json]
Exit status: 0 no errors (warnings allowed), 1 errors, 2 unreadable input.
"""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path

EVENTS = {
    "claude": {
        "SessionStart",
        "Setup",
        "InstructionsLoaded",
        "UserPromptSubmit",
        "UserPromptExpansion",
        "MessageDisplay",
        "PreToolUse",
        "PermissionRequest",
        "PostToolUse",
        "PostToolUseFailure",
        "PostToolBatch",
        "PermissionDenied",
        "Notification",
        "SubagentStart",
        "SubagentStop",
        "TaskCreated",
        "TaskCompleted",
        "Stop",
        "StopFailure",
        "TeammateIdle",
        "ConfigChange",
        "CwdChanged",
        "DirectoryAdded",
        "FileChanged",
        "WorktreeCreate",
        "WorktreeRemove",
        "PreCompact",
        "PostCompact",
        "PreModelSwitch",
        "PostModelSwitch",
        "SessionEnd",
        "Elicitation",
        "ElicitationResult",
    },
    "codex": {
        "SessionStart",
        "SessionEnd",
        "SubagentStart",
        "PreToolUse",
        "PermissionRequest",
        "PostToolUse",
        "PreCompact",
        "PostCompact",
        "UserPromptSubmit",
        "SubagentStop",
        "Stop",
        "Interrupt",
    },
    "gemini": {
        "BeforeTool",
        "AfterTool",
        "BeforeAgent",
        "AfterAgent",
        "BeforeModel",
        "BeforeToolSelection",
        "AfterModel",
        "SessionStart",
        "SessionEnd",
        "Notification",
        "PreCompress",
    },
    "cursor": {
        "preToolUse",
        "postToolUse",
        "postToolUseFailure",
        "subagentStart",
        "subagentStop",
        "beforeShellExecution",
        "beforeMCPExecution",
        "afterShellExecution",
        "afterMCPExecution",
        "afterFileEdit",
        "beforeReadFile",
        "beforeTabFileRead",
        "afterTabFileEdit",
        "beforeSubmitPrompt",
        "afterAgentResponse",
        "afterAgentThought",
        "stop",
        "sessionStart",
        "sessionEnd",
        "preCompact",
        "workspaceOpen",
    },
    "copilot": {
        "sessionStart",
        "sessionEnd",
        "userPromptSubmitted",
        "userPromptTransformed",
        "preToolUse",
        "postToolUse",
        "postToolUseFailure",
        "agentStop",
        "subagentStart",
        "subagentStop",
        "errorOccurred",
        "preCompact",
        "permissionRequest",
        "notification",
        "SessionStart",
        "SessionEnd",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PostToolUseFailure",
        "Stop",
        "SubagentStop",
        "ErrorOccurred",
        "PreCompact",
    },
    "vscode": {
        "SessionStart",
        "UserPromptSubmit",
        "PreToolUse",
        "PostToolUse",
        "PreCompact",
        "SubagentStart",
        "SubagentStop",
        "Stop",
    },
}
HANDLER_TYPES = {
    "claude": {"command", "http", "mcp_tool", "prompt", "agent"},
    "codex": {"command", "mcp_tool", "prompt", "agent"},
    "gemini": {"command"},
    "cursor": {"command", "prompt"},
    "copilot": {"command", "http", "prompt"},
    "vscode": {"command"},
}
NESTED = {"claude", "codex", "gemini"}  # event -> [{matcher, hooks: [...]}]
MATCHER_IGNORED = {
    "codex": {"UserPromptSubmit", "Stop", "Interrupt"},
    "copilot": {
        "sessionStart",
        "sessionEnd",
        "userPromptSubmitted",
        "agentStop",
        "errorOccurred",
    },
}
GEMINI_LIFECYCLE = {"SessionStart", "SessionEnd", "Notification", "PreCompress"}
SCRIPT = re.compile(r"[^\s\"']+\.(?:py|sh|js|cjs|mjs|ts)\b")
PLACEHOLDERS = (
    "${CLAUDE_PROJECT_DIR}",
    "$CLAUDE_PROJECT_DIR",
    "$GEMINI_PROJECT_DIR",
    "${GEMINI_PROJECT_DIR}",
    "$(git rev-parse --show-toplevel)",
)
EPILOG = """\
Exit status:
  0  no errors (warnings allowed)
  1  at least one error
  2  the file is unreadable, not JSON, or its hooks are not the host's
     list/object layout (the message names the bad entry)

Output: one "FILE: error|warning: EVENT: message" line per problem, then
"N error(s), M warning(s)". --json prints a JSON list of {"severity",
"message"} objects instead, with no summary line.

Examples:
  python3 scripts/check_hook_config.py .claude/settings.json --host claude \\
      --project .
  python3 scripts/check_hook_config.py .cursor/hooks.json --host cursor --json
"""


def handlers(host: str, hooks: dict) -> list[tuple[str, str | None, dict]]:
    """Flatten to (event, matcher, handler) triples."""
    found: list[tuple[str, str | None, dict]] = []
    for event, entries in hooks.items():
        if not isinstance(entries, list):
            raise ValueError(f"hooks.{event} must be a list")
        for index, entry in enumerate(entries):
            where = f"hooks.{event}[{index}]"
            if not isinstance(entry, dict):
                raise ValueError(f"{where} must be an object")
            if host not in NESTED:
                found.append((event, entry.get("matcher"), entry))
                continue
            group = entry.get("hooks", [])
            if not isinstance(group, list):
                raise ValueError(f"{where}.hooks must be a list")
            for position, handler in enumerate(group):
                if not isinstance(handler, dict):
                    raise ValueError(f"{where}.hooks[{position}] must be an object")
                found.append((event, entry.get("matcher"), handler))
    return found


def command_strings(handler: dict) -> list[tuple[str, str]]:
    """Return (key, text) for each command-like field of a handler."""
    keys = ("command", "bash", "exec", "windows", "powershell", "linux", "osx")
    parts = [(k, handler[k]) for k in keys if isinstance(handler.get(k), str)]
    parts += [("args", a) for a in handler.get("args", []) if isinstance(a, str)]
    return parts


def script_paths(text: str, project: Path, windows: bool = False) -> list[Path]:
    for placeholder in PLACEHOLDERS:
        text = text.replace(placeholder, str(project))
    if windows:  # backslashes are separators, not shell escapes
        tokens = text.split()
    else:
        try:
            tokens = shlex.split(text)
        except ValueError:
            tokens = text.split()
    paths = []
    for token in tokens:
        for match in SCRIPT.finditer(token):
            path = Path(match.group(0).replace("\\", "/"))
            paths.append(path if path.is_absolute() else project / path)
    return paths


def check(config: object, host: str, project: Path | None) -> list[tuple[str, str]]:
    problems: list[tuple[str, str]] = []

    def error(message: str) -> None:
        problems.append(("error", message))

    def warn(message: str) -> None:
        problems.append(("warning", message))

    if not isinstance(config, dict) or not isinstance(config.get("hooks"), dict):
        return [("error", 'expected an object with a "hooks" object')]
    if host in {"cursor", "copilot"} and config.get("version") != 1:
        error(f'{host} hook files need "version": 1')
    if host == "vscode" and "version" in config:
        warn("a numeric version makes VS Code read this as a Copilot file")
    for event, matcher, handler in handlers(host, config["hooks"]):
        where = f"{event}"
        if event not in EVENTS[host]:
            close = [e for e in EVENTS[host] if e.lower() == event.lower()]
            hint = f" (did you mean {close[0]}?)" if close else ""
            error(f"{where}: unknown {host} event{hint}")
        kind = handler.get("type", "command")
        if not isinstance(kind, str) or kind not in HANDLER_TYPES[host]:
            error(f"{where}: handler type {kind!r} not supported by {host}")
        elif host == "codex" and kind in {"prompt", "agent"}:
            warn(f"{where}: codex parses {kind} handlers but skips them")
        if matcher is not None and not isinstance(matcher, str):
            error(f"{where}: matcher must be a string, got {json.dumps(matcher)}")
        elif matcher not in (None, "", "*"):
            if event in MATCHER_IGNORED.get(host, set()):
                warn(f"{where}: {host} ignores matcher on this event")
            if host == "gemini" and event in GEMINI_LIFECYCLE and "|" in matcher:
                warn(f"{where}: exact-string matcher {matcher!r} never matches")
            try:
                re.compile(matcher)
            except re.error as exc:
                error(f"{where}: matcher {matcher!r} is not a regex: {exc}")
        timeout = handler.get("timeoutSec", handler.get("timeout"))
        if isinstance(timeout, (int, float)):
            if host == "gemini" and timeout < 100:
                warn(f"{where}: gemini timeout is milliseconds; {timeout} ms")
            if host == "codex" and event in {"SessionEnd", "Interrupt"} and timeout > 3:
                error(f"{where}: codex allows at most 3 s for {event}")
        if kind == "command" and not command_strings(handler):
            error(f"{where}: command handler has no command")
        if project is not None:
            for key, text in command_strings(handler):
                windows = key in {"windows", "powershell"}
                for path in script_paths(text, project, windows):
                    if not path.exists():
                        error(f"{where}: script not found: {path}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(__doc__ or "").splitlines()[0],
        epilog=EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("file", help="hook configuration JSON file")
    parser.add_argument("--host", required=True, choices=sorted(EVENTS))
    parser.add_argument(
        "--project", type=Path, help="project root; also check script paths exist"
    )
    parser.add_argument("--json", action="store_true", help="print a JSON list")
    args = parser.parse_args(argv)
    try:
        config = json.loads(Path(args.file).read_text(encoding="utf-8"))
        problems = check(config, args.host, args.project)
    except (OSError, ValueError, AttributeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps([{"severity": s, "message": m} for s, m in problems]))
    else:
        for severity, message in problems:
            print(f"{args.file}: {severity}: {message}")
        errors = sum(s == "error" for s, _ in problems)
        print(f"{errors} error(s), {len(problems) - errors} warning(s)")
    return 1 if any(s == "error" for s, _ in problems) else 0


if __name__ == "__main__":
    raise SystemExit(main())
