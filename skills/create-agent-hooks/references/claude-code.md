# Claude Code hooks

Claude Code only. Facts from the [hooks reference][ref], fetched 2026-09-25 against CLI 2.1.282.
Version notes such as "v2.1.214 or later" matter on older builds: check `claude --version`.

## Contents

- [Locations](#locations)
- [Matchers](#matchers)
- [Handlers and timeouts](#handlers-and-timeouts)
- [Exit codes and JSON output](#exit-codes-and-json-output)
- [PreToolUse decision](#pretooluse-decision)
- [Stop and SubagentStop](#stop-and-subagentstop)
- [Other events](#other-events)
- [Debugging](#debugging)

## Locations

Hooks nest as event, then matcher group, then handlers.

| File | Scope |
| --- | --- |
| `~/.claude/settings.json` | all projects on this machine |
| `.claude/settings.json` | the project, committed |
| `.claude/settings.local.json` | the project, not committed |
| managed policy settings | organization |
| plugin `hooks/hooks.json` | while the plugin is enabled |
| skill or subagent frontmatter | while it is active |

Entries from different levels merge. An identical handler in two files runs once. Cloud sessions do
not read `~/.claude/settings.json`.

## Matchers

- `"*"`, `""`, or no matcher matches everything.
- A value of only letters, digits, `_`, `-`, spaces, `,`, and `|` is an exact name or a list of
  exact names. Hyphens count from v2.1.195.
- Any other value is an unanchored JavaScript regex, so `Edit.*` also matches `NotebookEdit`. Anchor
  it: `^Edit$`.
- For conditions on arguments use the handler's `if` field, one permission-rule pattern such as
  `"Bash(git *)"`, or check in the script.

## Handlers and timeouts

Five handler types: `command`, `http`, `mcp_tool`, `prompt`, `agent`.

- A `command` handler with `args` runs in exec form, with no shell: `$`, spaces, and quotes in paths
  pass through verbatim. Without `args` it runs through `sh -c`. Use exec form for script paths:
  `"command": "python3"` (Windows: `"py"` with `"-3"` first in `args`),
  `"args": ["${CLAUDE_PROJECT_DIR}/g.py"]`.
- Timeouts are in seconds: 600 for command, http, and mcp_tool; 30 for prompt; 60 for agent.
  `SessionEnd` hooks share a 1.5 s budget.
- `async: true` runs in the background and cannot block. Never set it on a policy hook.

## Exit codes and JSON output

- Exit 0: success. Stdout that starts with `{` and ends with `}` is parsed as JSON.
- Exit 2: block on events that can block. Stderr becomes the reason. Even a JSON `"allow"` cannot
  override it.
- Any other exit, including 1 from an uncaught Python exception, is a non-blocking error and the
  action proceeds.
- On `UserPromptSubmit`, `UserPromptExpansion`, `SessionStart`, and `PostModelSwitch`, plain stdout
  is added to Claude's context.

## PreToolUse decision

`hookSpecificOutput` carries:

- `permissionDecision`: `allow`, `deny`, `ask`, or `defer`.
- `permissionDecisionReason`: shown to Claude for `deny`, to the user only for `ask`, and logged
  only for `allow` and `defer`.
- `updatedInput`, which replaces the whole input, and `additionalContext`.

With several hooks the precedence is deny, defer, ask, allow. Top-level `decision` and `reason` are
deprecated here. A hook with no opinion prints nothing, because `allow` skips the permission prompt.
A timed-out command hook does not block the call.

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
 "permissionDecision": "deny",
 "permissionDecisionReason": "Blocked: force push"}}
```

## Stop and SubagentStop

`{"decision": "block", "reason": "..."}` keeps Claude working, and `reason` is required. The input
includes `stop_hook_active`, `last_assistant_message`, and `background_tasks`. Claude Code caps
continuations at 8 in a row. When `background_tasks` is not empty and the session only waits for
them, blocking adds an empty turn.

## Other events

- `SessionStart` matchers: `startup`, `resume`, `clear`, `compact`, `fork`. Only `command` and
  `mcp_tool` handlers work. Plain stdout or `additionalContext` is added before the first prompt.
  Static text belongs in `CLAUDE.md`.
- `StopFailure` runs instead of `Stop` when the turn ends on an API error. Its output and exit code
  are ignored except `terminalSequence`, and a refusal (`stop_reason` `refusal`) is not an API
  error, so it never matches.
- `TaskCompleted` has no matcher. Exit 2 keeps the task from being marked completed, and stderr goes
  back to the model.
- `SubagentStart` cannot block and can return `additionalContext`. It fires again when `SendMessage`
  reaches a running subagent ([issue #80489][i80489]), so key injections by `agent_id`.

## Debugging

- `/hooks` is a read-only browser showing each hook's source file.
- `"disableAllHooks": true` disables hooks after precedence is applied, except managed hooks from a
  non-managed file. `claude --settings '{"disableAllHooks": true}'` does it for one run.
- `allowManagedHooksOnly` in managed settings blocks user, project, local, and plugin hooks.
- There is no per-hook switch: remove the entry with `scripts/merge_hooks.py --remove`.
- The file watcher picks up settings edits.

[ref]: https://code.claude.com/docs/en/hooks
[i80489]: https://github.com/anthropics/claude-code/issues/80489
