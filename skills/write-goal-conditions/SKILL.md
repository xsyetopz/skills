---
name: write-goal-conditions
description: >-
  Writes and repairs Claude Code `/goal` completion conditions that the
  transcript-only evaluator can judge: an end state the output shows, the exact
  check command, and a turn bound. Use when setting `/goal`, when asked to keep
  going until something holds, or when a goal never ends or ends too early. Not
  for plan task done conditions, `/loop` schedules, or writing Stop hooks.
---

# Write goal conditions

`/goal <condition>` is a Claude Code feature. Other agents have no such
evaluator. Their nearest equivalent is a Stop hook: use `$create-agent-hooks`.

## How the evaluator works

After every turn a small fast model reads the condition and the conversation so
far. It returns one verdict with a short reason:

- **Not yet met**: Claude starts another turn and takes the reason as guidance.
- **Met**: the goal clears and the transcript records it as achieved.
- **Impossible**: the goal clears and the transcript records it as failed.

The evaluator does not run commands, read files, or call tools. It judges only
what Claude surfaced in the conversation. A condition about a fact that never
appears in the transcript cannot become met, and a vague one is judged on
Claude's own claims.

`/goal` is a session-scoped prompt-based Stop hook. The persistent, scriptable
form is in `$create-agent-hooks`.

## Session behavior

- One goal is active per session. A new `/goal <condition>` replaces it.
- Setting a goal starts a turn at once, with the condition as the directive.
  Send no separate prompt.
- The condition can be up to 4,000 characters.
- There is no built-in turn or time cap. Put the bound in the condition.
- `/goal` alone shows the condition, elapsed time, turns evaluated, token
  spend, and the last reason.
- `/goal clear` removes the goal. `stop`, `off`, `reset`, `none`, and `cancel`
  are aliases. `/clear` also removes it.
- Resuming a session restores a goal that was still active. The turn count,
  timer, and token baseline reset. A met or cleared goal is not restored.
- A rate limit or usage limit pauses the goal. Some failures (authentication,
  no credit, context overflow, model unavailable) clear it: run `/goal` again
  after the fix.
- `/goal` does not change the permission mode. In Manual mode Claude still
  asks before each tool call that settings do not allow, so an unattended
  loop needs auto mode.
- `/goal` is unavailable when hooks are disabled by `disableAllHooks` or
  `allowManagedHooksOnly`.

## Write the condition

1. **Name one end state that output shows.** A test summary line, an exit
   code, the printed contents of a file, a count, an empty queue.
1. **Name the exact check command** Claude must run and whose output it must
   show, for example `just check`. Claude must run it after the last edit,
   not cite an earlier run.
1. **Add a bound.** End with `or stop after 15 turns`. A time clause also
   works. The evaluator judges the bound from the conversation, so ask for
   progress against it each turn.
1. **Add constraints that must hold on the way.** For example "no test file
   is modified" or "no dependency is added". Pair each with a command that
   shows it, such as `git diff --stat`.
1. **Check for the evaluator's blind spots.** Could the condition be met by
   Claude stating it, with no output behind it? Could it be met by deleting
   the failing test? Fix the wording until neither is true.

Template:

```text
/goal <command> <result> in the transcript after the last edit, <constraint
shown by another command>, or stop after <N> turns
```

Good:

```text
/goal `just check` exits 0 in the transcript, or stop after 15 turns
```

Bad, with the repair:

| Bad | Problem | Repair |
| :- | :- | :- |
| the code is clean | No observable state | `just lint` prints no warnings and exits 0 |
| all bugs fixed | No list, no check | `pytest tests/test_parser.py` reports 0 failed |
| the feature works | Claude's claim decides | `curl -s localhost:8080/health` prints `ok` |
| tests pass | No command, no bound | `bun test` exits 0, or stop after 20 turns |

More examples are in [references/conditions.md][examples].

## Rewrite procedure

For a request like "keep going until X":

1. Restate X as a fact a command can print.
1. Find the repository's real command in the justfile, scripts, or CI. Run it
   once to see its output format.
1. Write the condition from the template. Name the line or exit code to look
   for.
1. Choose the bound from the work size: a few turns for a known fix, more for
   a migration. Do not leave it out.
1. Read the condition as the evaluator: from the transcript alone, could a
   false claim satisfy it? Tighten until it cannot.

## Keep the condition true to the request

The condition is the only thing the loop serves. If the request changes, or
the condition no longer says what is wanted, replace it with a new
`/goal <condition>` or run `/goal clear`. Do not keep a stale goal and steer
around it with prompts.

If Claude reports the goal is unreachable (missing credentials, a check that
cannot run here), let the `impossible` verdict end it or clear it, and report
the blocker. Do not weaken the check to reach `met`.

## Out of scope

- Done conditions for tasks in a plan: use `$write-implementation-plans`.
- A check that must run as code on every session: use `$create-agent-hooks`.
- Time-interval repetition: `/loop`.

[examples]: references/conditions.md
