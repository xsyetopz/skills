# Gemini CLI and Cursor hooks

Facts from the [Gemini CLI hooks overview][gemini] and
[reference][gemini-ref], and from the [Cursor hooks docs][cursor], all
fetched on 2026-09-25. Neither host is installed here, so host runs are
"Not run". `verify.sh` checks the handlers and configurations.

## Contents

- Gemini: settings layers and handler fields
- Gemini: BeforeTool and AfterTool decisions
- Gemini: agent and lifecycle events
- Gemini: trust and management
- Cursor: configuration levels and working directory
- Cursor: preToolUse decision and failure policy
- Cursor: stop follow-ups

## Gemini: settings layers and handler fields

**Definition.** Hooks live under `hooks` in `settings.json`. The layers
are, from highest precedence:

1. `.gemini/settings.json` (project)
1. `~/.gemini/settings.json` (user)
1. `/etc/gemini-cli/settings.json` (system)
1. extensions

A matcher group can set `sequential: true`. Handlers support only
`type: "command"`, plus the fields `name`, `timeout` (in
**milliseconds**, default 60000), and `description`. The environment
is sanitized and provides `GEMINI_PROJECT_DIR`, `GEMINI_SESSION_ID`,
`GEMINI_CWD`, and `CLAUDE_PROJECT_DIR` as an alias.

**Use when.** Wiring any Gemini hook.

**Do not use when.** Copying Claude's `timeout: 10`, which Gemini reads
as 10 ms.

**Example.** [`assets/config/gemini/.gemini/settings.json`][g-asset]:

```json
{"matcher": "run_shell_command",
 "hooks": [{"name": "guard-shell", "type": "command",
            "command": "CMD", "timeout": 10000}]}
```

`CMD` is, on one line:
`python3 "$GEMINI_PROJECT_DIR/.agent-hooks/guard_shell.py" --host gemini`.

**Cost removed.** Hooks killed after a few milliseconds.
`check_hook_config.py` warns when a Gemini timeout is below 100.

**Verify.**

1. `check_hook_config.py .gemini/settings.json --host gemini --project .`
   reports no errors and no timeout warning.

## Gemini: BeforeTool and AfterTool decisions

**Definition.** Stdout must be exactly one JSON object, with no other
text.

- `BeforeTool`: `{"decision": "deny", "reason": R}` blocks the tool;
  the agent gets R as a tool error, and the turn continues.
  `hookSpecificOutput.tool_input` merges into the arguments.
  `continue: false` stops the whole loop.
- `AfterTool`: `deny` replaces the result with R.
  `additionalContext` appends text.
  `tailToolCallRequest` runs another tool after this one.

Exit 2 blocks, with stderr as the reason. Other exit codes are only
warnings. Tool matchers are regexes over tool names such as
`run_shell_command`, `read_file`, and `mcp_<server>_<tool>`.

**Use when.** Guarding or rewriting tool calls.

**Do not use when.** Printing logs to stdout. They break the JSON, so
log to stderr.

**Example.** `guard_shell.py --host gemini` prints
`{"decision": "deny", "reason": "Blocked by guard_shell (force push): ..."}`,
or `{}` to allow. On the Gemini fixture, and then with the command
replaced by `npm test`, from the skill root:

```sh
python3 assets/handlers/guard_shell.py --host gemini \
  < assets/fixtures/gemini-beforetool.json | jq .
sed 's/git push --force origin main/npm test/' \
  assets/fixtures/gemini-beforetool.json |
  python3 assets/handlers/guard_shell.py --host gemini
```

```text
{
  "decision": "deny",
  "reason": "Blocked by guard_shell (force push): git push --force origin main"
}
{}
```

**Cost removed.** Parse failures from stray prints.

**Verify.**

1. `GuardTests` pass for `gemini`. The benign path prints exactly `{}`.

## Gemini: agent and lifecycle events

**Definition.**

- `BeforeAgent` fires on a submitted prompt. It can add context, or
  deny the turn, which discards the message.
- `AfterAgent` can deny the response, which forces a retry with the
  reason as a new prompt. It passes `stop_hook_active`.
- `SessionStart` (sources `startup`, `resume`, `clear`), `SessionEnd`,
  `Notification`, and `PreCompress` are advisory. Their `continue` and
  `decision` fields are ignored.
- Lifecycle matchers are exact strings.

**Use when.** Checking prompts (`BeforeAgent`) or completion
(`AfterAgent`).

**Do not use when.**

- Placing a blocking policy in `SessionStart`, which cannot block.
- Relying on regex alternation in a lifecycle matcher. `startup|resume`
  is an exact string that never matches, so omit the matcher.

**Example.** The warning from the checker:

```text
warning: SessionStart: exact-string matcher 'startup|resume' never matches
```

**Cost removed.** Session hooks that never fire.

**Verify.**

1. `test_gemini_lifecycle_matcher_and_millisecond_timeout` passes.

## Gemini: trust and management

**Definition.** Gemini fingerprints project hooks. A changed name or
command, for example after `git pull`, makes a new, untrusted hook, and
Gemini warns the user before it runs. Management commands:

- `/hooks panel`
- `/hooks enable-all` and `/hooks disable-all`
- `/hooks enable <name>` and `/hooks disable <name>`

**Use when.** Rolling out or debugging hooks.

**Do not use when.** Expecting a renamed hook to keep its trust. It
needs approval again.

**Example.** Give each hook a stable `name` (`guard-shell`) so that
`/hooks disable guard-shell` works. The name in
[`assets/config/gemini/.gemini/settings.json`][g-asset], read from the
skill root:

```sh
jq '.hooks.BeforeTool[].hooks[] | {name, description}' \
  assets/config/gemini/.gemini/settings.json
```

```json
{
  "name": "guard-shell",
  "description": "Deny force pushes and recursive deletes of / or ~"
}
```

**Cost removed.** Anonymous hooks that cannot be toggled one at a time.

**Verify.**

1. `/hooks panel` lists `guard-shell`. Not run here.

## Cursor: configuration levels and working directory

**Definition.** A file needs `"version": 1` and lowerCamelCase event
names. The levels are enterprise, team, project
(`<root>/.cursor/hooks.json`, in trusted workspaces), and user
(`~/.cursor/hooks.json`), and all of them run. Project hooks run from
the project root, and user hooks from `~/.cursor/`. Per-entry options:

- `command`;
- `type` (`command` or `prompt`);
- `timeout` (seconds);
- `matcher` (regex);
- `failClosed`;
- `loop_limit`.

**Use when.** Wiring Cursor hooks.

**Do not use when.**

- Using PascalCase names such as `PreToolUse`, which Cursor does not
  recognize.
- Writing project paths as `./hooks/x`. Write `.cursor/hooks/x`.

**Example.** [`assets/config/cursor/.cursor/hooks.json`][c-asset]:

```json
{"version": 1, "hooks": {"preToolUse": [{
  "command": "python3 .cursor/hooks/guard_shell.py --host cursor",
  "matcher": "Shell", "timeout": 10, "failClosed": true}]}}
```

**Cost removed.** Hooks with wrong-case names that never fire; the
checker reports `unknown cursor event (did you mean preToolUse?)`.

**Verify.**

1. `check_hook_config.py .cursor/hooks.json --host cursor --project .`
   reports `0 error(s)`.

## Cursor: preToolUse decision and failure policy

**Definition.**

- Output is `permission` (`allow` or `deny`), with an optional
  `user_message`, `agent_message`, and `updated_input`. `ask` is
  accepted but not enforced for `preToolUse`.
- Exit 2 means deny. Other exit codes fail open unless the entry sets
  `failClosed: true`, which also counts "no output" as a failure.
- For permission hooks, invalid JSON or schema-invalid output blocks.
- Merged decisions across sources: deny wins over ask, and ask wins
  over allow.

**Use when.** Blocking shell, MCP, read, or tool calls.

**Do not use when.** Returning nothing from a `failClosed` hook on the
allow path, which blocks every call.

**Example.** `guard_shell.py --host cursor` answers
`{"permission": "allow"}` on the allow path, and a deny object with
both messages otherwise. From the skill root:

```sh
sed 's/git push --force origin main/npm test/' \
  assets/fixtures/cursor-pretooluse.json |
  python3 assets/handlers/guard_shell.py --host cursor
python3 assets/handlers/guard_shell.py --host cursor \
  < assets/fixtures/cursor-pretooluse.json | jq -c '[.permission, keys]'
```

```text
{"permission": "allow"}
["deny",["agent_message","permission","user_message"]]
```

**Cost removed.** A guard that blocks everything under `failClosed`, or
lets everything through when it crashes.

**Verify.**

1. `test_allows_benign_command_without_a_decision` expects
   `{"permission": "allow"}` for Cursor.

## Cursor: stop follow-ups

**Definition.** The `stop` hook receives `status` (`completed`,
`aborted`, `error`) and `loop_count`. Returning a non-empty
`followup_message` submits it as the next user message. `loop_limit`
(default 5 for Cursor hooks) caps the automatic follow-ups.

**Use when.** Building a "keep going until X" loop in Cursor.

**Do not use when.** Reusing `stop_gate.py` unchanged. It prints the
Claude and Codex fields (`decision` and `reason`), which Cursor does
not read. Map `reason` to `followup_message` instead.

**Example.**

```python
print(json.dumps({"followup_message": reason} if failed else {}))
```

**Cost removed.** Stop hooks that print fields Cursor ignores.

**Verify.**

1. In a trusted scratch workspace, a failing check produces a follow-up
   message. Not run here.

[gemini]: https://geminicli.com/docs/hooks/
[gemini-ref]: https://geminicli.com/docs/hooks/reference/
[cursor]: https://cursor.com/docs/hooks
[g-asset]: ../assets/config/gemini/.gemini/settings.json
[c-asset]: ../assets/config/cursor/.cursor/hooks.json
