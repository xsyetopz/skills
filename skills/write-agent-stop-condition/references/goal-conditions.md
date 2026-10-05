# Goal Conditions

Claude Code only ([`/goal` docs][goal]). Codex has no `/goal` evaluator: its nearest equivalent is a
Stop hook.

## Contents

- [How the Evaluator Works](#how-the-evaluator-works)
- [Session Behavior](#session-behavior)
- [Examples](#examples)
- [Failure Patterns](#failure-patterns)

## How the Evaluator Works

After every turn a small fast model reads the condition and the conversation so far and returns one
verdict with a short reason:

- Not yet met: Claude starts another turn and takes the reason as guidance.
- Met: the goal clears and the transcript records it as achieved.
- Impossible: the goal clears and the transcript records it as failed.

It runs no commands, reads no files, and calls no tools. It judges only what Claude surfaced in the
conversation. `/goal` is a session-scoped prompt-based Stop hook ([prompt-based hooks][prompt]); the
persistent, scriptable form is a Stop hook in settings.

## Session Behavior

- One goal per session. A new `/goal <condition>` replaces it, and it starts a turn at once with the
  condition as the directive.
- The condition can be up to 4,000 characters. There is no built-in turn or time cap.
- `/goal` alone shows the condition, elapsed time, turns, token spend, and the last reason.
  `/goal clear` removes it (`stop`, `off`, `reset`, `none`, `cancel` are aliases), and so does
  `/clear`.
- Resuming restores an active goal, with the turn count, timer, and token baseline reset.
- A rate or usage limit pauses the goal. Authentication, no credit, context overflow, or an
  unavailable model clear it: run `/goal` again after the fix.
- `/goal` does not change the permission mode. In Manual mode Claude still asks before each tool
  call that settings do not allow. Switching to auto mode is the user's decision.
- It is unavailable when `disableAllHooks` or `allowManagedHooksOnly` is set.

## Examples

| Work | Condition |
| --- | --- |
| Fix failing tests | `bun test` prints `0 fail` and exits 0 after the last edit, or stop after 15 turns |
| Migration | `rg -c 'oldApi\(' src` prints no matches and `just check` exits 0, or stop after 30 turns |
| Size budget | `wc -l` on every file in `src/parser/` prints under 400, `just test` exits 0, or stop after 20 turns |
| Lint backlog | `just lint` prints `0 problems` and exits 0, or stop after 25 turns |
| Constraint | `just check` exits 0 and `git diff --stat -- tests` shows no changes, or stop after 15 turns |

Run the repository's own command once first to learn its output format.

## Failure Patterns

- No command ("tests pass"): Claude may run nothing and say so.
- Stale evidence: an earlier green run, then more edits. Require the check after the last edit.
- Weakened check: met by deleting or skipping the failing test. Add a constraint command that shows
  the tests are untouched.
- No bound: an unpassable check runs until context, budget, or limits end it. The `impossible`
  verdict is a backstop, not a plan.
- Stale goal: the request moved on. Replace or clear it.

[goal]: https://code.claude.com/docs/en/goal
[prompt]: https://code.claude.com/docs/en/hooks-guide#prompt-based-hooks
