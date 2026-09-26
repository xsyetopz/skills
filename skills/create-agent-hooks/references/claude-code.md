# Claude Code hooks

Facts from the [Claude Code hooks reference][ref], fetched on
2026-09-25, with the installed CLI at 2.1.282. The docs' version notes,
such as "v2.1.214 or later", matter on older builds; check with
`claude --version`.

## Contents

- Locations and merging
- Matcher rules
- Handler types and exec form
- Exit codes and JSON output
- PreToolUse decision
- Stop and SubagentStop decision
- SessionStart context
- Inspecting, disabling, and managed hooks

## Locations and merging

**Definition.** Hooks live in settings files, nested in three levels:
event, then matcher group, then handlers.

| File | Scope |
| --- | --- |
| `~/.claude/settings.json` | all projects on this machine |
| `.claude/settings.json` | the project, committed |
| `.claude/settings.local.json` | the project, not committed |
| managed policy settings | organization |
| plugin `hooks/hooks.json` | while the plugin is enabled |
| skill or subagent frontmatter | while the skill or subagent is active |

Entries from different levels merge rather than replace each other.
An identical handler defined in two settings files runs once.

**Use when.**

- Use project `.claude/settings.json` for hooks the team shares.
- Use `.claude/settings.local.json` for personal experiments.

**Do not use when.** The hook must reach cloud sessions from your
local `~/.claude/settings.json`, which cloud sessions do not read.

**Example.** [`assets/config/claude/.claude/settings.json`][asset]
wires `session_context.py`, `guard_shell.py`, and `stop_gate.py`. Run
from the skill root:

```sh
jq -r '.hooks | to_entries[]
  | "\(.key): \(.value[0].hooks[0].args[0])"' \
  assets/config/claude/.claude/settings.json
```

```text
SessionStart: ${CLAUDE_PROJECT_DIR}/.agent-hooks/session_context.py
PreToolUse: ${CLAUDE_PROJECT_DIR}/.agent-hooks/guard_shell.py
Stop: ${CLAUDE_PROJECT_DIR}/.agent-hooks/stop_gate.py
```

**Cost removed.** Overwritten user settings. Merge with
`merge_hooks.py` instead of copying the asset over an existing file.

**Verify.**

1. Run `check_hook_config.py .claude/settings.json --host claude
   --project .` and get `0 error(s)`.
1. In Claude Code, `/hooks` lists the entry with source
   `Project Settings`. Not run here.

## Matcher rules

**Definition.** How Claude Code reads a `matcher`:

- `"*"`, `""`, or no matcher matches everything.
- A value made only of letters, digits, `_`, `-`, spaces, `,` and `|`
  is an exact name or a list of exact names.
- Any other value is an unanchored JavaScript regex.

So `Edit.*` also matches `NotebookEdit`. Hyphens count as exact-match
characters only from v2.1.195.

**Use when.** Every tool or lifecycle matcher.

**Do not use when.** You need several conditions on the arguments. Use
the handler's `if` field, which takes one permission-rule pattern such
as `"Bash(git *)"`, or check inside the script.

**Example.** `"Edit|Write"` matches exactly those two tools. When the
value contains a regex character and must match a whole name, anchor
it: `"^Edit$"`. How the unanchored JavaScript regexes `Edit.*` and
`^Edit$` treat `Edit` and `NotebookEdit`, run with `node`:

```js
// Regex matchers are unanchored: they match anywhere in the tool name.
for (const matcher of ["Edit.*", "^Edit$"]) {
  const re = new RegExp(matcher);
  console.log(matcher, ["Edit", "NotebookEdit"].map((t) => re.test(t)));
}
```

```text
Edit.* [ true, true ]
^Edit$ [ true, false ]
```

**Cost removed.** Hooks that fire on the wrong tools, or on none.
`check_hook_config.py` compiles regex matchers and reports syntax
errors.

**Verify.**

1. In a scratch session, trigger the matching tool and one near-miss
   tool. Only the first appears in the debug log. Not run here.

## Handler types and exec form

**Definition.** Five handler types: `command`, `http`, `mcp_tool`,
`prompt`, `agent`. A `command` handler with `args` runs in exec form,
with no shell. Without `args` it runs in shell form (`sh -c`).
Timeouts are in seconds:

- 600 for command, http, and mcp_tool handlers;
- 30 for prompt handlers, and 60 for agent handlers;
- `SessionEnd` hooks share a 1.5 s budget.

**Use when.**

- Prefer exec form for any script path, especially with
  `${CLAUDE_PROJECT_DIR}`.
- Switch to shell form only when you need pipes or `&&`.

**Do not use when.** Setting `async: true` on a policy hook. Async
hooks run in the background and cannot block.

**Example.**

```json
{
  "type": "command",
  "command": "python3",
  "args": [
    "${CLAUDE_PROJECT_DIR}/.agent-hooks/guard_shell.py",
    "--host",
    "claude"
  ],
  "timeout": 10
}
```

**Cost removed.** Quoting bugs. In exec form, `$`, spaces, and quotes
in paths pass through verbatim.

**Verify.**

1. `check_hook_config.py` resolves `${CLAUDE_PROJECT_DIR}` and confirms
   that the script exists.

## Exit codes and JSON output

**Definition.** The meaning of each exit code:

- Exit 0: success. Stdout that starts with `{` and ends with `}` is
  parsed as JSON.
- Exit 2: block, on events that can block. Stderr becomes the reason.
  Even a JSON `"allow"` cannot override it.
- Any other exit: a non-blocking error, and the action proceeds.

On `UserPromptSubmit`, `UserPromptExpansion`, `SessionStart`, and
`PostModelSwitch`, plain stdout is added to Claude's context.

**Use when.** Choosing how a handler reports its result.

**Do not use when.** Enforcing a policy with `exit 1`. Exit 1 is
non-blocking.

**Example.** The docs' minimal blocker:

```bash
input=$(cat)
command=$(jq -r '.tool_input.command' <<<"$input")
if [[ "$command" == rm* ]]; then
  echo "Blocked: rm commands are not allowed" >&2
  exit 2
fi
exit 0
```

**Cost removed.** Policies that do not block, such as a handler whose
Python exception exits 1.

**Verify.**

1. The handler's error path returns 2, as
   `test_invalid_input_blocks_with_exit_2` shows for `guard_shell.py`.

## PreToolUse decision

**Definition.** `hookSpecificOutput` carries these fields:

- `permissionDecision`: `allow`, `deny`, `ask`, or `defer`;
- `permissionDecisionReason`: shown to Claude for `deny`;
- `updatedInput`, which replaces the whole input;
- `additionalContext`.

When several hooks answer, the precedence is deny, then defer, then
ask, then allow. The top-level `decision`/`reason` fields are
deprecated for this event.

**Use when.** Blocking, forcing a prompt, or rewriting a tool call.

**Do not use when.**

- The hook has no opinion. Print nothing: `allow` skips the
  permission prompt.
- The command hook can time out. A timed-out command hook does not
  block the tool call.

**Example.** The `guard_shell.py --host claude` output for the fixture:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse",
 "permissionDecision": "deny",
 "permissionDecisionReason":
   "Blocked by guard_shell (force push): git push --force origin main"}}
```

**Cost removed.** Destructive commands reaching the shell, as a second
layer behind permission rules.

**Verify.**

1. `test_denies_force_push_in_each_host_shape` passes for `claude`.
1. In a scratch repository, ask Claude to force push and confirm that
   the deny reason appears. Not run here: it needs a model session.

## Stop and SubagentStop decision

**Definition.** `{"decision": "block", "reason": "..."}` keeps Claude
working; `reason` is required. The alternative,
`hookSpecificOutput.additionalContext`, continues the turn as feedback
instead of as an error. The input includes `stop_hook_active`,
`last_assistant_message`, and `background_tasks`. Claude Code caps
continuations at 8 in a row.

**Use when.** Completion requires a check, such as tests or lint.

**Do not use when.** `background_tasks` is not empty and the session
is only waiting for them. Blocking then adds an empty turn.

**Example.** `stop_gate.py --check "python3 -m unittest -q"`, wired in
the Claude asset with `timeout: 180`. A failing check on the Codex Stop
fixture (Claude Code shares its decision shape), from the skill root:

```sh
python3 assets/handlers/stop_gate.py --check false \
  < assets/fixtures/codex-stop.json | jq -r '.decision, .reason'
```

```text
block
`false` failed with exit 1. Fix the failures before finishing:
```

**Cost removed.** Turns that end with failing tests.

**Verify.**

1. The `StopGateTests` in `test_handlers.py` pass.

## SessionStart context

**Definition.** Matchers: `startup`, `resume`, `clear`, `compact`,
`fork`. Only `command` and `mcp_tool` handlers are supported. Plain
stdout, or `hookSpecificOutput.additionalContext`, is added before the
first prompt. JSON can also set `sessionTitle`, `watchPaths`, and
`reloadSkills`.

**Use when.** The facts change per session, such as the branch or
open issues.

**Do not use when.** The content is static. Put it in `CLAUDE.md`.

**Example.** `session_context.py` returns the branch and changed files.
In a new repository with one untracked file, from the skill root:

```sh
git -c init.defaultBranch=main init -q demo && touch demo/new.txt
printf '{"hook_event_name": "SessionStart", "cwd": "demo"}' |
  python3 assets/handlers/session_context.py |
  jq -r '.hookSpecificOutput.additionalContext'
rm -rf demo
```

```text
Branch: main
Changed files: 1
- new.txt
```

**Cost removed.** A first turn spent on discovery.

**Verify.**

1. `SessionContextTests` pass.

## Inspecting, disabling, and managed hooks

**Definition.**

- `/hooks` is a read-only browser that shows each hook's source file.
- `"disableAllHooks": true` disables hooks after settings precedence
  is applied. It cannot disable managed hooks from a non-managed file.
- `allowManagedHooksOnly` in managed settings blocks user, project,
  local, and plugin hooks.
- Edits to settings files are picked up by the file watcher.

**Use when.**

- Debugging which hook ran.
- Turning off all hooks for one run with
  `--settings '{"disableAllHooks": true}'`.

**Do not use when.** You need to disable one hook. There is no
per-hook switch, so remove its entry with `merge_hooks.py --remove`.

**Example.**

```sh
claude --settings '{"disableAllHooks": true}'
```

**Cost removed.** Deleting whole files to silence one hook.

**Verify.**

1. After `--remove`, `/hooks` no longer lists the entry. Not run here.

[ref]: https://code.claude.com/docs/en/hooks
[asset]: ../assets/config/claude/.claude/settings.json
