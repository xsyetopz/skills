# Hook design across hosts

Rules that hold for every host, and the per-host facts that decide how
to apply them. The host sections link the primary docs, fetched on
2026-09-25. Every "Example" is in `assets/` and runs in
`assets/verify.sh`.

## Contents

- [Guardrail, not enforcement boundary](#guardrail-not-enforcement-boundary)
- [Event authority: observe, modify, or block][toc-1]
- [Untrusted input parsing](#untrusted-input-parsing)
- [Shell paths and write targets](#shell-paths-and-write-targets)
- [Deny, allow, and no decision](#deny-allow-and-no-decision)
- [Ask budget and ask memory](#ask-budget-and-ask-memory)
- [Verdict log](#verdict-log)
- [Fail open or fail closed](#fail-open-or-fail-closed)
- [Stop gate with a loop guard](#stop-gate-with-a-loop-guard)
- [Loop and waste detectors](#loop-and-waste-detectors)
- [Session context injection](#session-context-injection)
- [Script path resolution](#script-path-resolution)
- [Install and roll back one entry](#install-and-roll-back-one-entry)
- [Configuration check before the host loads it][toc-2]
- [Environment and secrets](#environment-and-secrets)
- [Sources](#sources)

[toc-1]: #event-authority-observe-modify-or-block
[toc-2]: #configuration-check-before-the-host-loads-it

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

## Shell paths and write targets

**Definition.** Two rules for path-based policies on shell commands:

- Resolve paths the way the shell does. In `cd ~/x && find .`, the `.`
  is `~/x`, not the project directory. Expand a leading `~` in a `cd`
  target to the home directory. When a `cd` target contains `$`, the
  hook cannot know the path: report it as unknown and apply the rule's
  unknown-path answer (ask or deny). Do not guess a value.
- Shell writes bypass file-tool hooks. `cat > f <<EOF`, `tee f`,
  `sed -i`, and `>` or `>>` redirects write files without the Edit or
  Write tool. A path rule on Edit and Write also needs a check of the
  shell command's write targets.

**Use when.** A hook protects paths, such as "no writes outside the
project" or "never edit `.env`".

**Do not use when.** The requirement is a hard boundary. Use the
host's sandbox or filesystem permissions; a parser of shell text
misses forms such as `python -c` or a script that writes the file.

**Pattern.** Split the command on `&&`, `;`, and `|`, and track the
working directory through each `cd`. For each segment, collect the
redirect targets and the file arguments of `tee` and `sed -i`, then
resolve them against the tracked directory. Test with fixtures:

| Command | Resolved target |
| --- | --- |
| `cd ~/x && find .` | `$HOME/x` |
| `cd "$DIR" && rm -r build` | unknown |
| `echo x > .env` | `.env` in the project |
| `sed -i s/a/b/ ../y.txt` | `y.txt` in the parent directory |

**Cost removed.** A path rule that the same agent passes with one
shell command, and false denies on paths the agent never touches.

**Verify.**

1. Each fixture row above resolves as listed, and a write through
   each shell form hits the same rule as the Edit tool.

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

**Levels.** Give each rule one level:

| Level | For | Output |
| --- | --- | --- |
| deny | a hard rule with no valid exception | the host's deny shape |
| ask | a judgment call that the user can approve | Claude Code `ask` |
| warn | a note the agent should see; the call continues | context only, such as `additionalContext` |

Group the rules by reversibility, not by tool. An action that cannot be
undone (force push, deleting untracked files, writing outside the
project) is a deny or an ask. An action that `git` or a re-run can undo
is a warn or no decision.

When several hooks answer the same Claude Code `PreToolUse` call, the
strongest answer wins: `deny`, then `defer`, then `ask`, then `allow`.
One hook's `allow` cannot cancel another hook's `deny`, so split rules
across hooks freely, but do not rely on an `allow` to open a path that
another hook denies.

**Reason text.** A deny reason is an instruction to the model. Claude
Code shows the `deny` reason to Claude, and shows an `ask` reason to
the user but not to Claude. Write each deny reason with the cause and
the next action:

```text
Blocked: `npm run dev` does not exit and would hold the turn. Run it
with `run_in_background`, then read its output with `Monitor`.
```

A reason with no next action, such as "Blocked by policy", tells the
model only that this route failed. It then tries the same thing by
another route, such as a different tool or a rewritten command. Test
the reason text: the fixture output must name the action to take.

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
1. Each deny reason in the fixture output names a cause and a next
   action.

## Ask budget and ask memory

**Definition.** Rules that keep `ask` prompts rare enough that the user
reads them:

- Budget: at most one ask for each turn, across all gates. Keep the
  count in a session state file keyed by `session_id`. When the budget
  is spent, answer later asks with no decision or a warn; a suppressed
  ask comes back on the next turn if the action repeats.
- Memory: when the user approves an ask, record the rule and target
  for the session, and do not ask again for the same pair.
- Never remember a deny. A deny is re-evaluated on every call.

**Use when.** More than one hook can return `ask`, or one hook can ask
about the same target many times.

**Do not use when.** The rule is a hard rule. Make it a deny, which has
no budget.

**Pattern.** A hook sees the call, not the user's answer. Record the
ask when you emit it. On Claude Code, the tool runs only after the
user approves, so a `PostToolUse` hook that sees the same tool input
can mark the pair as approved. Write state under the host's per-user
data directory, not in the project.

**Cost removed.** Prompt fatigue: a user who sees many asks approves
them without reading.

**Verify.**

1. A test sends two asking calls in one turn and gets one ask.
1. After an approved ask, the same call in the same session gets no
   ask. After a deny, the same call gets the deny again.
1. The same ask appears twice in one session only if the setup has a
   bug, such as memory keyed by the wrong field. Treat a repeat in the
   verdict log as a defect.

## Verdict log

**Definition.** One JSONL line for each deny, ask, and warn, with these
fields: time, `session_id`, `agent_id` (empty on the main thread), rule
name, level, and a short target.

**Use when.** Any policy hook that the user relies on over many
sessions.

**Do not use when.** The hook only adds context and never decides.

**Pattern.** Cut the target to a fixed length, such as 80 characters,
and never log the environment, the full payload, or file contents.
The target can hold a token that was on the command line.

```python
record = {
    "time": datetime.now(timezone.utc).isoformat(),
    "session": event.get("session_id"),
    "agent": event.get("agent_id", ""),
    "rule": rule, "level": level, "target": target[:80],
}
```

**Cost removed.** Gates that fire too often without anyone noticing. A
gate that fires on most calls is a bug: a wide pattern, a wrong path
resolution, or a missing ask memory. Count lines by rule to find it:

```sh
jq -r '.rule + " " + .level' verdicts.jsonl | sort | uniq -c | sort -rn
```

**Verify.**

1. A test writes one verdict and reads back exactly the listed
   fields, with the target cut to the limit.

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

**Ending checks.** A Stop gate can also block a turn whose final text
announces work instead of doing it, such as a turn that ends with
"Next I'll...". That gate must pass a turn that ended with a question
tool call, such as Claude Code's `AskUserQuestion`: the agent is
waiting for the user, not stopping early. Read the last assistant
message from `transcript_path`, and pass when it holds a `tool_use`
block for the question tool. The transcript line format is not
documented; inspect the keys of a local transcript before you match
on them.

**Verify.**

1. Four tests pass: failing check (block with output, valid against
   the Codex stop schema), passing check, active flag, and timeout.
1. An ending-check gate has two more fixtures: a "Next I'll..."
   ending blocks once, and the same text followed by a question tool
   call passes.

## Loop and waste detectors

**Definition.** Hooks that notice an agent spending turns without
progress, and answer with a warn or a deny whose reason names the next
action:

| Pattern | Signal | Pass case that must stay green |
| --- | --- | --- |
| Re-read of an unchanged file | a full read of a path whose size and mtime match the last read in this session | a read after the file changed, or a read of a line range |
| Repeated status command | the same status command three times with the same output | the same command after a change, or with different output |
| Foreground command that does not end | a dev server, a `--watch` flag, or `tail -f` run in the foreground | the same command in the background, or `tail -n` |

**Use when.** Sessions show the pattern in the verdict log or the
transcript.

**Do not use when.** The pattern is rare. Each detector adds a check to
every matching call, and a false positive costs a turn.

**Pattern.** Keep per-session state keyed by `session_id` (and
`agent_id` in subagents). A repeated-output detector needs the output,
so it runs in `PostToolUse`; the foreground detector runs in
`PreToolUse` and denies with the background form as the next action.

**Cost removed.** Turns and context spent on reads and polls that
return nothing new, and turns that hang on a process that never exits.

**Verify.**

1. Each detector has a fixture that fires and a fixture for its pass
   case. Both run in the test suite, and the pass case stays green
   after every change to the pattern.

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

**Repeated events.** An injection can fire more than once for the same
agent. In Claude Code, `SubagentStart` fires again when a running
subagent is messaged with `SendMessage` ([issue #80489][cc-80489]).
Key each injection by `agent_id` in a session state file, and inject
once for each agent.

**Cache cost.** Context that changes between calls can change the
cached prompt prefix. In Claude Code, changing `PreToolUse` or
`PostToolUse` `additionalContext` can invalidate the prompt cache
([issue #83913][cc-83913]). Before you add context that changes on
each call, measure cache writes with and without the hook: run the
same multi-tool task with `claude -p ... --output-format json` and
compare `cache_creation_input_tokens` and `cache_read_input_tokens` in
`usage` ([prompt caching][cc-cache]). Cache creation that stays high
with the hook means it changes the prefix.

**Cost removed.** The agent spending its first turn asking git the same
questions.

**Verify.**

1. `test_reports_branch_and_changed_files` passes in a new repository,
   and the output matches the Codex `session-start` output schema.
1. Outside a repository the hook prints nothing and exits 0.
1. A repeated-event hook injects once when it gets the same `agent_id`
   twice.

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

## Sources

The sources below were checked again on 2026-09-30.

- [Claude Code hooks reference][claude]
- [Claude Code prompt caching][cc-cache]
- [anthropics/claude-code#80489][cc-80489]: messaging a running
  subagent re-fires `SubagentStart` hooks (open when fetched).
- [anthropics/claude-code#83913][cc-83913]: prompt cache invalidated
  when `PreToolUse`/`PostToolUse` `additionalContext` changes (open
  when fetched).

[claude]: https://code.claude.com/docs/en/hooks
[codex]: https://developers.openai.com/codex/hooks
[copilot]: https://docs.github.com/en/copilot/reference/hooks-reference
[cc-cache]: https://code.claude.com/docs/en/prompt-caching
[cc-80489]: https://github.com/anthropics/claude-code/issues/80489
[cc-83913]: https://github.com/anthropics/claude-code/issues/83913
