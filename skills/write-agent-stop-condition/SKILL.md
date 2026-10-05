---
name: write-agent-stop-condition
description: >-
  Writes stop conditions that keep Claude Code or Codex working until a check
  passes, as goal commands or Stop hooks that run tests, lint, or just check
  before the agent may finish. Use when the agent stops too early, claims done
  without running the tests, or a goal or Stop hook loops forever. Not for
  PreToolUse guards, formatters, or other hooks.
when_to_use: >-
  Keep going until cargo test passes. Do not let Claude stop until the build
  is green. My goal never ends. The Stop hook blocks forever. Claude met the
  goal by deleting the failing test.
---

# Write Agent Stop Condition

A stop condition decides when the agent may finish. A vague one is met by a claim ("tests pass"),
and an unbounded one loops until limits end it. Claude Code has two forms: `/goal`, judged by a
small model from the transcript, and a Stop hook, which runs a real command. Codex has only the Stop
hook.

## Rules

- Name one end state that output shows: a test summary line, an exit code, a count, an empty queue.
  "The code is clean" and "tests pass" name no output, so the agent's own claim meets them.
- Name the repository's own check command (`just check`, `bun test`), read from its justfile,
  package.json, or README, and require its output after the last edit. An earlier green run is stale
  evidence.
- Bound every `/goal` with a turn count: `or stop after 15 turns`. `/goal` has no built-in cap.
- Add a constraint that shows the check was not gamed, tied to a command: `git diff --stat -- tests`
  shows no changes. Otherwise deleting or skipping the failing test meets the goal. Never weaken the
  check to reach the end state; replace the goal or `/goal clear` instead.
- Use a Stop hook when the check must really run (a `/goal` evaluator runs nothing and reads only
  the transcript), when the host is Codex, or when the gate must persist across sessions.
- Bound every Stop hook's retries. `stop_gate.py` blocks at most `--max-retries` times in a row
  (default 3), counted per session while `stop_hook_active` is `true`, and starts over on a new
  stop. A gate that blocks on every `stop_hook_active: true` payload loops forever on Codex, which
  has no cap; Claude Code caps continuations at 8, so a higher value has no effect there.
- Stop output on both hosts: `{"decision": "block", "reason": "..."}` on stdout with exit 0 to keep
  the agent working, `{}` to let it stop. Codex rejects plain text from a Stop hook as a hook error
  and ends the turn, so every path prints JSON.
- Put the check's failing output in `reason`. The agent acts on the reason, so "tests failed" alone
  sends it back blind.
- Set the hook `timeout` above the check's own timeout. A timed-out hook does not block, so the
  agent stops unchecked.
- Merge one Stop entry into the existing hooks file and keep every other entry. Never rewrite the
  file from a template. Read the file first and show the user the diff.
- Codex runs a new or edited hook only after the user reviews it in `/hooks`, in a trusted project.
  Say so, because you cannot run that step.

## Workflow

1. Find the check command and run it once to learn its output and exit code.
1. Choose the form. Claude Code with an interactive user and no need to run the check: `/goal`.
   Otherwise a Stop hook.
1. For `/goal`, write one condition:

   ```text
   /goal `just check` exits 0 in the transcript after the last edit, `git diff --stat -- tests`
   shows no changes, or stop after 15 turns
   ```

   Read it as the evaluator: could a false claim in the transcript satisfy it?
1. For a Stop hook, copy [`scripts/stop_gate.py`](scripts/stop_gate.py) into the project
   (`.claude/hooks/` or `.codex/hooks/`) so the entry does not depend on where the skill is
   installed, then add one entry to `hooks.Stop` in the existing file.
   Claude Code, `.claude/settings.local.json` (or `.claude/settings.json` if the user wants it
   shared), exec form so paths with spaces work:

   ```json
   {"hooks": [{"type": "command", "command": "python3",
     "args": ["${CLAUDE_PROJECT_DIR}/.claude/hooks/stop_gate.py", "--check", "just check",
              "--timeout", "300"],
     "timeout": 330}]}
   ```

   Codex, `.codex/hooks.json`:

   ```json
   {"hooks": [{"type": "command",
     "command":
     "python3 \"$(git rev-parse --show-toplevel)/.codex/hooks/stop_gate.py\" --check 'just check'",
     "timeout": 150}]}
   ```

   The hook `timeout` stays above the gate's `--timeout` (default 120 seconds).
1. Prove the hook with payloads piped to the exact entry command, with `TMPDIR` set to a scratch
   directory so the retry counter stays out of the real one. A Stop payload needs
   `hook_event_name`, `session_id`, `cwd`, and `stop_hook_active`. A failing check with
   `stop_hook_active` false prints a block with the output tail and `Retry 1 of 3`; a passing check
   prints `{}`; a failing check sent three more times with `stop_hook_active` true blocks twice,
   then prints `{}`.
1. Report the condition or entry, each payload result, how to remove it (`/goal clear`, or
   delete the one entry), and each step not run in the host.

## Scripts

- `python3 scripts/stop_gate.py --check CMD [--timeout S] [--max-retries N]` blocks Stop with the
  check's output tail until `CMD` exits 0, at most N times in a row (default 3), then lets the agent
  stop. It also lets the agent stop when its counter file in the temp directory cannot be written.
  Exit 0, or 2 for a non-Stop event, an empty or unclosed-quote `CMD`, or N below 1. On Windows, use
  `py -3`. Test: `test_stop_gate.py`.

## References

Read [`references/goal-conditions.md`](references/goal-conditions.md) when a `/goal` needs session
behavior (resume, pause on limits, permission mode), more example conditions, or a repair for a goal
that never ends.
