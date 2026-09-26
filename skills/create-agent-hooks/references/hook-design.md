# Hook design across hosts

Rules that hold for every host, and the per-host facts that decide how
to apply them. The host sections link the primary docs, fetched on
2026-09-25. Every "Example" is in `assets/` and runs in
`assets/verify.sh`.

## Contents

- Guardrail, not enforcement boundary
- Event authority: observe, modify, or block
- Untrusted input parsing
- Deny, allow, and no decision
- Fail open or fail closed
- Stop gate with a loop guard
- Session context injection
- Script path resolution
- Install and roll back one entry
- Configuration check before the host loads it
- Environment and secrets

## Guardrail, not enforcement boundary

**Definition.** A hook runs only on the paths where the host fires it,
as the hosts themselves say:

- Claude Code: the `if` filter is best effort. Use the permission system
  for a hard allow or deny ([Claude hooks][claude]).
- Codex: some tool paths opt out of hooks, so hooks are "a useful
  guardrail, not a complete enforcement boundary" ([Codex hooks][codex]).
- Copilot: timeouts are fail-open even for policy hooks
  ([Copilot hooks][copilot]).

**Use when.** Deciding whether a hook alone can enforce a security
requirement.

**Do not use when.** The requirement is a hard boundary, such as "the
agent must never read `.env`". Put it in the host's permission or
sandbox settings, and use a hook only as a second layer.

**Example.** For Claude Code, pair the guard hook with a permission rule:

```json
{
  "permissions": { "deny": ["Bash(git push --force:*)"] },
  "hooks": { "PreToolUse": [ { "matcher": "Bash", "hooks": [ "..." ] } ] }
}
```

**Cost removed.** False confidence in a hook. Codex hosted tools such
as `WebSearch` never reach `PreToolUse`, so no guard hook sees them.

**Verify.**

1. The report names the permission or sandbox rule that enforces each
   hard requirement, and the hook's role next to it.

## Event authority: observe, modify, or block

**Definition.** Each event has a fixed authority: observe only, add
context, modify input, or block. Documented examples:

| Host | Blocks a tool call | Keeps the agent going | Advisory only |
| --- | --- | --- | --- |
| Claude Code | `PreToolUse` | `Stop`, `SubagentStop` | `SessionStart`, `Notification` |
| Codex | `PreToolUse` | `Stop` (continues the turn) | `SessionEnd` |
| Gemini CLI | `BeforeTool` | `AfterAgent` (forces a retry) | `SessionStart`, `PreCompress` |
| Cursor | `preToolUse`, `beforeShellExecution` | `stop` sends a `followup_message` | `sessionEnd` |
| Copilot | `preToolUse` | `agentStop` | `sessionEnd` |

**Use when.** Picking the event for a requirement.

**Do not use when.** The event is advisory but the requirement needs a
block, such as a policy check in `SessionStart`, whose decision fields
are ignored.

**Example.** `stop_gate.py` uses `Stop`, which Claude Code and Codex
both document as able to continue the conversation, not `SessionEnd`.
It refuses any other event, from `assets/handlers/stop_gate.py`:

```python
    if not isinstance(event, dict) or event.get("hook_event_name") != "Stop":
        print("stop_gate: expected a Stop event object", file=sys.stderr)
        return 2
```

Fed the SessionStart fixture from the skill root:

```sh
python3 assets/handlers/stop_gate.py --check true \
  < assets/fixtures/codex-sessionstart.json
echo "exit $?"
```

```text
stop_gate: expected a Stop event object
exit 2
```

**Cost removed.** Policies whose block path never runs. The checker
cannot see authority, so read the event's decision section before
wiring.

**Verify.**

1. The report quotes the host doc's sentence that says the chosen
   event can block, modify, or only observe.

## Untrusted input parsing

**Definition.** A handler reads one JSON object from stdin with a size
limit, uses only the documented fields it needs, and never executes
text from the payload. Commands, prompts, and file contents in the
payload come from the model and the repository.

**Use when.** Every command handler.

**Do not use when.** No exception.

**Example.** From `guard_shell.py`:

```python
def read_event() -> dict:
    raw = sys.stdin.buffer.read(LIMIT + 1)
    if len(raw) > LIMIT:
        raise BadEvent("input exceeds 1 MiB")
    try:
        event = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise BadEvent(f"input is not JSON: {error}") from None
    if not isinstance(event, dict):
        raise BadEvent("input is not a JSON object")
    return event
```

**Cost removed.**

- Crashes on unexpected payloads. Claude Code treats exit 1 as a
  non-blocking error, so a crashing guard lets the action through.
- Command injection through `eval` or `sh -c` of payload text.

**Verify.**

1. `test_invalid_input_blocks_with_exit_2` feeds `not json`, `[1, 2]`,
   and an object without a tool name, and each exits 2.
1. `rg -n 'eval|exec\(|shell=True|os.system' assets/handlers/`
   finds nothing.

## Deny, allow, and no decision

**Definition.** A policy hook has three answers: deny, allow, and no
decision, which defers to the host's normal permission flow. Each host
spells deny differently:

| Host | Deny output (exit 0) | Exit-code deny |
| --- | --- | --- |
| Claude Code, Codex | `hookSpecificOutput.permissionDecision: "deny"` | exit 2 + stderr |
| VS Code Local | same `hookSpecificOutput` shape (docs' example) | not documented on the page |
| Gemini CLI | `{"decision": "deny", "reason": ...}` | exit 2 + stderr |
| Cursor | `{"permission": "deny", "user_message", "agent_message"}` | exit 2 |
| Copilot | `{"permissionDecision": "deny", "permissionDecisionReason"}` | exit 2 |

"Allow" is not neutral. In Claude Code, `"allow"` skips the permission
prompt. A guard that is not approving the call prints nothing (Claude
Code, Codex).

**Use when.** Writing any PreToolUse-type hook.

**Do not use when.** The hook exists to approve something, such as
read-only tools. Then `"allow"` is the point; document it.

**Example.** `guard_shell.py` answers the benign `npm test` with no
output on Claude Code and Codex, `{}` on Gemini, and
`{"permission": "allow"}` on Cursor. Cursor treats "no output" as a
hook failure, which blocks under `failClosed`. From the skill root:

```sh
for pair in claude:claude-pretooluse codex:codex-pretooluse \
  gemini:gemini-beforetool cursor:cursor-pretooluse; do
  host=${pair%%:*}
  out=$(sed 's/git push --force origin main/npm test/' \
    "assets/fixtures/${pair#*:}.json" |
    python3 assets/handlers/guard_shell.py --host "$host")
  echo "$host: ${out:-(no output)}"
done
```

```text
claude: (no output)
codex: (no output)
gemini: {}
cursor: {"permission": "allow"}
```

**Cost removed.** Accidental auto-approval, and deny shapes the host
ignores. A Cursor-shaped `{"permission": "deny"}` sent to
Codex fails its schema with `unexpected property 'permission'`
(`test_cursor_style_output_would_fail_codex_schema`).

**Verify.**

1. `test_denies_force_push_in_each_host_shape` and
   `test_allows_benign_command_without_a_decision` pass.
1. For Codex, the output validates against
   `pre-tool-use.command.output.schema.json`.

## Fail open or fail closed

**Definition.** What each host does when the hook itself fails: a
crash, a timeout, bad output.

| Host | Crash / other exit | Timeout |
| --- | --- | --- |
| Claude Code | non-blocking error, action proceeds (exit 1 too) | `PreToolUse` command hook: does not block |
| Codex | hook run marked failed; see event section | default 600 s; `SessionEnd`/`Interrupt` 1 s (max 3) |
| Gemini CLI | warning, continues | default 60000 ms |
| Cursor | action proceeds unless `failClosed: true` | same, per `failClosed` |
| Copilot | `preToolUse`: denies ("hook errored"); others logged | fail-open for every event |

**Use when.** Choosing exit codes and timeouts for a policy hook.

**Do not use when.** Raising the timeout to fix a slow policy check.
Make the check fast instead: a slow `PreToolUse` delays every tool
call.

**Example.** `guard_shell.py` exits 2 on input it cannot read, because
every listed host treats that code as block. Its Cursor entry sets
`"failClosed": true`. From `assets/handlers/guard_shell.py`:

```python
    try:
        command = shell_command(args.host, read_event())
    except BadEvent as error:
        print(f"guard_shell: {error}; blocking", file=sys.stderr)
        return 2
```

Fed a JSON array instead of an object, from the skill root:

```sh
echo '[1, 2]' | python3 assets/handlers/guard_shell.py --host claude
echo "exit $?"
```

```text
guard_shell: input is not a JSON object; blocking
exit 2
```

**Cost removed.** Silent pass-through. On Claude Code, a guard that
raises an exception exits 1, and the command runs.

**Verify.**

1. Each policy hook's error path exits 2; the test sends malformed
   input and asserts exit 2.
1. The configured timeout is shorter than the host's default and fits
   the measured run time. Record `time` for the handler on its
   fixture.

## Stop gate with a loop guard

**Definition.** A `Stop` hook that runs a check and keeps the agent
working (`decision: "block"` with a `reason`) until the check passes.
It lets the agent stop when `stop_hook_active` is true, which means a
Stop hook already continued this turn. Claude Code also caps
continuations at 8 in a row.

**Use when.** "Don't finish until the tests pass" in Claude Code or
Codex.

**Do not use when.**

- The check takes minutes. The Stop hook delays the end of every
  turn.
- The host is Cursor or Gemini, which use `loop_limit` and
  `AfterAgent`. Write their own shapes.

**Example.** From `assets/handlers/stop_gate.py`, dedented, with the
check command's run elided at `...`:

```python
if event.get("stop_hook_active") is True:
    print("{}")  # already continued once: let the agent stop
    return 0
...
reason = (
    f"`{args.check}` failed with exit {result.returncode}. "
    f"Fix the failures before finishing:\n{output}"
)
print(json.dumps({"decision": "block", "reason": reason}))
```

**Cost removed.** Turns that end with failing tests. The loop guard
prevents an endless continue loop:
`test_stop_hook_active_prevents_a_loop` sends an active flag with a
failing check and gets `{}`.

**Verify.**

1. Four tests pass: failing check (block with output, valid against
   the Codex stop schema), passing check, active flag, and timeout.

## Session context injection

**Definition.** In Claude Code and Codex, a `SessionStart` hook adds
text to the model's context through plain stdout or
`hookSpecificOutput.additionalContext`.

**Use when.** The agent needs facts that change per session, such as
the branch and changed files. Static instructions belong in
`AGENTS.md` or `CLAUDE.md` (`$write-agents-md`).

**Do not use when.** The output would be large or slow, since
`SessionStart` runs on every session. Codex caps the text with
`additionalContextLimit` and saves the rest to disk.

**Example.** `session_context.py` prints the branch and up to 20
changed files. It uses `git branch --show-current` (git 2.22+), which
works before the first commit, where `git rev-parse --abbrev-ref HEAD`
fails; the test caught that. From
`assets/handlers/session_context.py`:

```python
    # --show-current also works before the first commit (unborn branch),
    # where `rev-parse --abbrev-ref HEAD` fails; it prints "" when detached.
    branch = git(event["cwd"], "branch", "--show-current")
    status = git(event["cwd"], "status", "--porcelain")
    if branch is None or status is None:
        return 0  # not a repository: no context, no error
```

**Cost removed.** The agent spending its first turn asking git the same
questions.

**Verify.**

1. `test_reports_branch_and_changed_files` passes in a new repository,
   and the output matches the Codex `session-start` output schema.
1. Outside a repository the hook prints nothing and exits 0.

## Script path resolution

**Definition.** A hook command runs in a working directory that the
host chooses. Reference scripts through the host's root variable or an
absolute path:

| Host | Working directory | Root reference |
| --- | --- | --- |
| Claude Code | current directory | `${CLAUDE_PROJECT_DIR}`, exec form with `args` |
| Codex | session `cwd` | `"$(git rev-parse --show-toplevel)"` |
| Gemini CLI | - | `$GEMINI_PROJECT_DIR` |
| Cursor | project root (project hooks), `~/.cursor/` (user) | `.cursor/hooks/x.py` |
| Copilot cloud | `/workspace` | relative to the repo |

**Use when.** Every command that runs a script from the repository.

**Do not use when.** The command is a tool found on `PATH`.

**Example.** Claude Code exec form. There is no shell, so a path with
spaces needs no quoting:

```json
{
  "type": "command",
  "command": "python3",
  "args": [
    "${CLAUDE_PROJECT_DIR}/.agent-hooks/guard_shell.py",
    "--host",
    "claude"
  ]
}
```

**Cost removed.** Hooks that fail with exit 127 when the agent starts
in a subdirectory. Claude Code reports that as a non-blocking error, so
the guard silently stops guarding.

**Verify.**

1. `check_hook_config.py FILE --host H --project DIR` reports no
   `script not found`.

## Install and roll back one entry

**Definition.** Add a hook by merging one handler into the existing
file, and roll back by removing that entry. Never overwrite the user's
settings file or remove other handlers.

**Use when.** Installing any hook into an existing configuration.

**Do not use when.** Policy manages the file, as with managed settings
or `/etc/...`. Those need an admin.

**Example.**

```sh
python3 scripts/merge_hooks.py .claude/settings.json --host claude \
  --event PreToolUse --matcher Bash \
  --handler '{"type":"command","command":"python3","args":["g.py"]}'
# same command with --remove rolls back; --dry-run prints a diff
```

**Cost removed.** Lost user settings and duplicate handlers. Adding
twice leaves one entry, and removing restores the original file, which
`verify.sh` compares.

**Verify.**

1. `test_remove_restores_the_original_content` and
   `test_add_twice_is_a_no_op` pass.
1. After a real install, the host's hook list (`/hooks` in Claude Code,
   Codex, and Gemini) shows the entry once. Not run here.

## Configuration check before the host loads it

**Definition.** Validate the file offline: event names for that host,
handler types, matchers, timeout units, and script paths
(`scripts/check_hook_config.py`).

**Use when.** After writing or merging any hook file, and in CI for
committed hook files.

**Do not use when.** Treating a clean check as proof that the host
loads and runs the hook. It proves only the static rules.

**Example.**

```text
$ python3 scripts/check_hook_config.py bad.json --host cursor
bad.json: error: cursor hook files need "version": 1
bad.json: error: PreToolUse: unknown cursor event (did you mean preToolUse?)
```

A Gemini `SessionStart` matcher `startup|resume` gets a warning:
lifecycle matchers there are exact strings, so it never matches.

**Cost removed.** Hooks that never fire because of a wrong-case or
invented event name, which the host does not report.

**Verify.**

1. All six configuration assets report `0 error(s)` in `verify.sh`.

## Environment and secrets

**Definition.** Hooks run with the host's environment:

- Claude Code: the parent environment, minus `OTEL_*` variables.
- Gemini CLI: a sanitized environment plus `GEMINI_*` variables.
- Copilot cloud agent: `GITHUB_COPILOT_API_TOKEN` and
  `GITHUB_COPILOT_GIT_TOKEN`.

A hook that logs its environment or the payload can leak these.

**Use when.** Any hook that logs, sends HTTP requests, or writes files.

**Do not use when.** No exception.

**Example.** None of the bundled handlers log or send the payload. A
hook that must log keeps only chosen fields:

```python
record = {k: event.get(k) for k in ("hook_event_name", "tool_name")}
```

**Cost removed.** Tokens in logs and in outbound requests.

**Verify.**

1. `rg -n 'environ|getenv|requests|urlopen|curl' assets/handlers/`
   lists every environment read and network call, each with a
   reason.

[claude]: https://code.claude.com/docs/en/hooks
[codex]: https://developers.openai.com/codex/hooks
[copilot]: https://docs.github.com/en/copilot/reference/hooks-reference
