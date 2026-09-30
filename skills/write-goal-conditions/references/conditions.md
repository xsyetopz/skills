# Goal condition examples and sources

## Conditions by kind of work

| Work | Condition |
| :- | :- |
| Fix failing tests | `bun test` prints `0 fail` and exits 0 after the last edit, or stop after 15 turns |
| Migration | `rg -c 'oldApi\(' src` prints no matches and `just check` exits 0, or stop after 30 turns |
| Size budget | `wc -l` on every file in `src/parser/` prints under 400, `just test` exits 0, or stop after 20 turns |
| Backlog | `gh issue list --label triage --state open` prints no rows, or stop after 25 turns |
| Constraint | `just check` exits 0 and `git diff --stat -- tests` shows no changes, or stop after 15 turns |

Each one names a command, the output to see, and a bound. Substitute the
repository's own commands; run them once first to learn the output format.

## Failure patterns

- **No command**: "tests pass". Claude may run nothing and say so.
- **Stale evidence**: an earlier green run, then more edits. Require the
  check after the last edit.
- **Weakened check**: the goal is met by deleting or skipping the failing
  test. Add a constraint that shows tests are untouched.
- **No bound**: a check that cannot pass runs until the context, budget, or
  limits end it. The evaluator's `impossible` verdict is a backstop, not a
  plan.
- **Stale goal**: the request moved on. Replace or clear the goal.

## Sources

- Claude Code `/goal` documentation:
  <https://code.claude.com/docs/en/goal>
- Prompt-based Stop hooks:
  <https://code.claude.com/docs/en/hooks-guide#prompt-based-hooks>
