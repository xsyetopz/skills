---
name: create-agent-hooks
description: >-
  Writes Claude Code and Codex hooks, including shell guards, stop gates, and
  goal conditions that check an end state. Use when adding, merging, or
  debugging hooks.
---

# Create Agent Hooks

A hook is a command the host runs on an event, with a JSON payload on
stdin. Models guess event names, exit codes, and output shapes from one
host and apply them to another. Read the host's reference first: [Claude
Code][cc-ref], [Codex][codex-ref]. Both have a `/hooks` browser.

## Rules

- Use the event names, payload fields, and output shape of the one host
  you write for. `PreToolUse` is Claude Code and Codex, `preToolUse` is
  Cursor, `BeforeTool` is Gemini CLI. Formats are not interchangeable,
  and this skill covers only Claude Code and Codex.
- Read the payload as JSON from stdin, never from argv or environment
  variables. Treat every field as untrusted input: never `eval`, never
  interpolate a payload string into a shell line, and pass paths as
  arguments rather than through `sh -c`. A branch or file name can hold
  `$(...)`.
- Exit 2 blocks on events that can block, and stderr is shown to the
  model as the reason. Exit 1, including an uncaught Python exception,
  is a non-blocking error and the action proceeds. A policy hook must
  catch its own failures and exit 2 (`scripts/guard_shell.py` does).
  Exit 2 output is not parsed as JSON: choose exit 2 with stderr, or
  exit 0 with JSON, never both.
- Emit the decision with the documented field. Claude Code and Codex
  `PreToolUse`: `hookSpecificOutput.permissionDecision` (`deny`, plus
  `allow`, `ask`, `defer` on Claude Code only) with
  `permissionDecisionReason`. Stop: `{"decision": "block", "reason":
  "..."}`. Codex ignores plain stdout on `PreToolUse` and rejects it on
  `Stop`: print JSON, `{}` for no opinion.
- Print no decision when the hook has no opinion. `allow` skips the
  permission prompt on Claude Code, so a guard that prints `allow` for
  everything it does not recognize removes the user's prompts.
- Guard every Stop hook against its own loop: if `stop_hook_active` is
  `true` the agent is already continuing because of a Stop hook, so
  print `{}` and let it stop. Without this, a check that keeps failing
  blocks forever. `scripts/stop_gate.py` does this; Claude Code also
  caps continuations at 8.
- Set `matcher` for the host's syntax. Claude Code: letters, digits,
  `_`, `-`, `,`, and `|` are exact names, anything else is an
  unanchored JS regex (`Edit.*` also matches `NotebookEdit`). Codex:
  always a regex, ignored on `Stop` and `UserPromptSubmit`. The shell
  tool is `Bash` on both. An unmatched matcher silently never fires.
- `timeout` is in seconds (default 600). A timed-out Claude Code
  command hook does not block the call, so keep policy hooks fast and
  offline.
- A hook is a guardrail, not a security boundary: it runs only on the
  paths where the host fires it, and a regex over a shell string misses
  `sh -c`, variable indirection, and scripts that run the command. For
  a hard rule also add a permission deny rule or sandbox setting
  ([Claude Code permissions][cc-perms]).
- Hooks run with the user's permissions, with no sandbox. Never log the
  environment or payload, send either anywhere, or fetch code to run.
- Reference scripts by absolute path from the host's root: Claude Code
  `${CLAUDE_PROJECT_DIR}` in exec form (`command` plus `args`), Codex
  `$(git rev-parse --show-toplevel)`. A relative path breaks when the
  session starts in a subdirectory.
- Merge one entry into the existing settings file and keep everything
  else; never rewrite the file from a template. Remove only that entry
  to roll back. `scripts/merge_hooks.py` does both and is idempotent.
- Codex does not run a new or edited hook until the user reviews it in
  `/hooks`, and project hooks need a trusted project. Claude Code picks
  up edits through its file watcher. Say which steps you could not run
  in a host session.

## Workflow

1. Identify the host and version (`claude --version`, `codex
   --version`) and the target file (Claude Code
   `.claude/settings.local.json` unless the user wants it shared in
   committed `.claude/settings.json`; Codex `.codex/hooks.json`). Read it.
1. Write the handler. Test it with a payload copied from the host doc
   for deny, no opinion, a non-matching tool, and malformed input.
1. Preview the entry:
   `python3 scripts/merge_hooks.py FILE --host claude --event PreToolUse
   --matcher Bash --handler '{"type": "command", ...}' --dry-run`. Drop
   `--dry-run` to write it.
1. Run `python3 scripts/check_hook_config.py FILE --host claude
   --project .`. Fix errors, explain warnings.
1. Report the file, entry, test results, rollback (`merge_hooks.py ...
   --remove`), and what was not run in the host.

## Goal conditions

`/goal <condition>` is Claude Code only: after every turn a small model
reads the condition and the transcript and decides met, not yet met, or
impossible. It runs nothing, so only what the conversation shows counts.
Codex has no equivalent: use a Stop hook.

- Name one end state that output shows: a test summary line, an exit
  code, printed file contents, a count, an empty queue. "The code is
  clean" and "tests pass" have none, so Claude's own claim decides.
- Name the repository's own check command (`just check`) and require
  its output after the last edit, not an earlier run.
- End with a bound: `or stop after 15 turns`. There is no built-in cap,
  so a check that cannot pass loops until limits end it.
- Add a constraint that shows the check was not gamed, each with a
  command: `git diff --stat -- tests` shows no changes. Otherwise
  deleting the failing test meets the goal.
- Read the wording as the evaluator: could a false claim in the
  transcript satisfy it? If the goal becomes unreachable or stale,
  replace it or `/goal clear`; never weaken the check to reach met.

```text
/goal `just check` exits 0 in the transcript after the last edit, `git
diff --stat -- tests` shows no changes, or stop after 15 turns
```

## Scripts

- `python3 scripts/guard_shell.py [--deny REGEX]` denies force push
  (`--force`, `-f`, `+refspec`, or a lease without `:SHA`) and
  `rm -rf /` or `~` for the `Bash` tool on Claude Code and Codex. Each
  `--deny` adds a pattern to these defaults. Exit 0 (deny JSON or
  nothing), 2 on bad input or an invalid pattern. On Windows, use `py -3`
  for `python3`. Test: `test_guard_shell.py`.
- `python3 scripts/stop_gate.py --check CMD [--timeout S]` blocks Stop with the
  check's output tail until `CMD` exits 0, and lets the agent stop when
  `stop_hook_active` is true. Exit 0, or 2 for a non-Stop event or an
  empty or unclosed-quote `CMD`. Test:
  `test_stop_gate.py`.
- `python3 scripts/merge_hooks.py FILE --host H --event E --handler JSON
  [--matcher M] [--remove] [--dry-run] [--json]` adds or removes one
  entry. Exit 0 written or already present, 1 `--remove` found nothing,
  2 bad input.
- `python3 scripts/check_hook_config.py FILE --host H [--project DIR] [--json]`
  checks events, handler types, matchers, timeout units, and script
  paths, one finding per line. Exit 0 clean, 1 errors, 2 unreadable.
  Both: `test_merge_and_check.py`.

## References

- Read [`references/claude-code.md`](references/claude-code.md) when
  writing Claude Code hooks: locations, matcher rules, handler types,
  PreToolUse and Stop output, SubagentStart and StopFailure.
- Read [`references/codex.md`](references/codex.md) when writing Codex
  hooks: trust review, config shape, matcher support, unsupported
  outputs.
- Read [`references/goal-conditions.md`](references/goal-conditions.md)
  when a `/goal` needs session behavior, more examples, or a repair for
  a goal that never ends.

[cc-ref]: https://code.claude.com/docs/en/hooks
[codex-ref]: https://developers.openai.com/codex/hooks
[cc-perms]: https://code.claude.com/docs/en/permissions
