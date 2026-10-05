---
name: interview-to-openspec
description: >-
  Interviews the user in rounds of multiple-choice questions, then writes an
  OpenSpec change (proposal.md, spec deltas, design.md, tasks.md) and runs
  `openspec validate --strict`. Use when a request is vague, large, or has open
  decisions: "build me X", "I want to add Y", "let's design", "spec this out",
  or a plan before coding. Not for clear, small tasks or OpenSpec's
  /opsx:explore.
when_to_use: >-
  I want to add team accounts, not sure how yet. Help me figure out what to
  build before we code. Write a proposal for this feature. Ask me what you need,
  then plan it.
---

# Interview to OpenSpec

Turn an unclear request into an OpenSpec change that another agent can implement without guessing.
Look the facts up, ask the user only for decisions, and write the change once no open decision would
change what gets built. Checked against OpenSpec 1.14.0.

## Rules

- Look facts up before you ask: the code, docs, `git log`, `openspec/config.yaml` (its `context` and
  `rules`), `openspec list --specs`, and `openspec list` for changes already in flight. Ask the user
  only about goals, preferences, constraints, and approvals. A question that the repository answers
  wastes a round.
- Do not invent requirements. Timeouts, size limits, retry counts, retention periods, roles, and
  policies that nobody stated are decisions: ask. A plausible number in a spec reads as decided.
- Walk the decision tree in dependency order. Settle a parent decision (for example where data
  lives) before its children (its schema), and do not ask a child whose parent is still open.
- Ask each round as one question call: 1 to 4 questions, 2 to 4 options each, the recommended option
  first with "(Recommended)" at the end of its label, and a description that states the trade-off.
  Keep each `header` within 12 characters. Do not add an "Other" option, because the host adds it.
  Use `preview` to compare code, layouts, or configurations side by side.
- The default budget is 3 rounds. Then ask whether to continue or to write the change. Stop when no
  open decision would change the specs, the approach, or the task list, and confirm the summary of
  decisions with the user before you write.
- Check each technical decision before you build on it, yours and the user's. If the
  `second-opinion` skill (dotclaude-jev) is installed, use its decision check; otherwise compare the
  decision with facts in the codebase (data size, callers, existing patterns). If the facts show a
  risk, say so once with the evidence and ask the user to confirm. The user's answer is final, and a
  preference needs no check.
- Ask before you run `openspec init`, because it writes files and, with `--tools`, skills and
  commands for each tool. Ask which tools the user wants, or pass `--tools none`.
- If the `openspec` CLI is missing, say so, write the files from [the format
  reference](references/openspec-format.md), and report validation as skipped. Do not install the
  CLI without asking.
- Write scenarios as observations at the contract boundary: a return value, a response, a file, a
  row, a log line. "Works correctly" and "is fast" cannot fail; replace them with a stated value or
  ask for one.
- Design for the stated need only. Add a port when two implementations exist now (a test double
  counts), a service only for an independent deployment or scaling need, a queue only when a direct
  call fails a stated requirement. Give each piece of state one authoritative writer.
- Each task names its own check: a command that exists in the repository, a test, or an observable
  result. Tests and docs ship in the task group that needs them, not in a final group. A change
  meant to keep behavior starts with tests that pass on the current code.
- Give each step that changes data (migration, delete, rename, notification) a rollback or the line
  "irreversible, because ...", and order it expand, migrate, contract. Retries need an operation key
  that the store enforces.
- Finish the replacement. When the change adds a new path, a task removes the old path, flag, or
  shim, and its check is a search that finds none.
- Do not implement. The skill ends with a validated change; implementation is `/opsx:apply` or the
  user's go-ahead.

## Asking on Each Host

- Claude Code: `AskUserQuestion`. Subagents do not have it, and `claude -p` with
  `--permission-prompts none` removes it.
- Codex: `request_user_input`, in Plan mode only. Its schema asks for 1 to 3 questions with 2 or 3
  options and a snake_case `id`. In Default mode and `codex exec`, ask in plain text and suggest
  Plan mode.
- Plain text, everywhere else: numbered questions with lettered options, the recommended option
  first, then end the turn and wait for the answers.

## Workflow

1. Read the request, AGENTS.md or CLAUDE.md, the OpenSpec config, the related specs
   (`openspec show <spec> --type spec --json --no-scenarios`), and the code the change touches.
1. List the open decisions in dependency order, and look up every item that is a fact.
1. Interview in rounds, and check each technical decision. Confirm the summary.
1. Run `openspec new change <name>` (kebab-case, verb first, such as `add-team-accounts`). For each
   artifact, read `openspec instructions <artifact> --change <name>` and write the file it names,
   because the project's schema and `config.yaml` rules can differ from the defaults. Write
   `design.md` only for cross-cutting work, a new dependency, data model, security, performance, or
   migration risk, or a decision with alternatives.
1. Run `openspec validate <name> --strict --no-interactive` and fix every error and warning, because
   `--strict` fails on warnings.
1. Run `scripts/audit_plan_claims.py` on `tasks.md` and `design.md` and fix each MISSING claim,
   unless an earlier task creates it.
1. Report the change path, the decisions and who made them, the open questions left in `design.md`,
   and the validation result. Name each check that did not run.

## Scripts

- `python3 scripts/audit_plan_claims.py FILE.md REPO [--json]` checks the files, `just` recipes,
  `package.json` scripts, Makefile targets, Python modules, and programs that a Markdown file names.
  Exit 0 every claim found, 1 a claim missing, 2 bad input. A path counts as new when "new",
  "create", or "add" precedes it on the line. On Windows, use `py -3` for `python3`.

## References

- Read [the OpenSpec format](references/openspec-format.md) when you write or fix a change: the
  delta grammar, MODIFIED and RENAMED rules, proposal and tasks sections, `skip_specs`, and the
  validator messages.
