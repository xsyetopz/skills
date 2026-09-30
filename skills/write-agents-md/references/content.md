# Instruction content

What goes into an AGENTS.md (or CLAUDE.md) and how to prove each line
true. The worked files in [`assets/examples/`](../assets/examples/) are
named `*.example.md`; only `verify.sh`'s temporary project renames them,
so no host loads them as live instructions.
`scripts/check_instructions.py` checks links, imports, symlinks, size, and
generic phrases, and extracts commands.

## Contents

- [Commands that run](#commands-that-run)
- [Project map](#project-map)
- [Non-default conventions](#non-default-conventions)
- [Boundaries with reasons](#boundaries-with-reasons)
- [Definition of done](#definition-of-done)
- [Evidence for each rule](#evidence-for-each-rule)
- [Revising rules instead of appending](#revising-rules-instead-of-appending)
- [What to leave out](#what-to-leave-out)
- [Size budget](#size-budget)
- [Example files never named AGENTS.md](#example-files-never-named-agentsmd)

## Commands that run

**Definition.** Exact build, test, lint, and format commands with their
working directory, copied from the repository's manifests, task runner, or
CI, and run before you write them down.

**Use when.** Any instruction file. Agents need commands most and get them
wrong most often.

**Do not use when.** The command comes from memory or another project
("`npm test`" in a Bun repository).

**Example.**

```markdown
## Commands

Run from the repository root:

    python3 -m unittest discover -s tests -t .
    python3 -m compileall -q src

Both must pass before a change is reported as done.
```

In the real file, use a fenced `sh` block so the checker can extract the
commands.

**Cost removed.** Agents guessing commands, installing tools the project
does not use, or reporting "done" without the real checks.

**Verify.**

1. `python3 scripts/check_instructions.py --commands AGENTS.md` lists the
   commands; run each and record its exit status. `verify.sh` does this
   for the example: 3 commands, all pass.

## Project map

**Definition.** A few lines on where the main parts live and what is
generated, only where directory names do not already say so. Link the
human docs that explain a part (architecture notes, module READMEs)
instead of repeating them. When an agent had to read code to learn what
those docs should have said, fix the docs: people and agents both read
them.

**Use when.** The layout has non-obvious locations (generated code,
vendored code, a second package root).

**Do not use when.** It would restate the directory tree; agents can list
files.

**Example.** "Invoice service: a Python library in `src/invoice/` with
unit tests in `tests/`."

**Cost removed.** Searching for the right package, and edits to generated
files.

**Verify.**

1. Every path named in the file exists (`check_instructions.py` checks
   Markdown links; check backticked paths with `ls`).

## Non-default conventions

**Definition.** Rules that differ from what an agent assumes by default:
package manager, units, naming schemes, error conventions, import rules.

**Use when.** The project's choice is not the ecosystem default or cannot
be inferred from one file.

**Do not use when.** The formatter or linter already enforces it; point to
the command instead.

**Example.**

```markdown
- Money is integer cents (`int`), never `float`; names end in `_cents`.
- Use Bun for JavaScript tooling. Never introduce npm, npx, Yarn, or pnpm.
```

**Cost removed.** The same review comment on every agent change.

**Verify.**

1. Each convention shows in the code (`rg -n '_cents\b' src/`) or a config
   file. If the code contradicts it, fix the rule or ask.

## Boundaries with reasons

**Definition.** Actions agents must not take, each with its reason or
alternative: editing generated files (and how to regenerate them),
directories owned by others, commands that publish or deploy.

**Use when.** A mistake would be costly or hard to reverse.

**Do not use when.** The approval rule comes from hypothetical risk. Keep
only boundaries the project has.

**Example.**

```markdown
- Do not edit `src/invoice/_rates_generated.py`; regenerate it with
  `python3 scripts/generate_rates.py` instead.
```

**Cost removed.** Edits to generated files that the next regeneration
silently discards.

**Verify.**

1. The regeneration command exists and runs (`verify.sh` runs it).

## Definition of done

**Definition.** The checks, matching CI, that a change must pass before
the agent reports it complete.

**Use when.** Any instruction file.

**Do not use when.** The check is not in CI and needs tools the project
does not provision.

**Example.** "Both must pass before a change is reported as done."

**Cost removed.** Changes reported done that fail CI.

**Verify.**

1. Compare with the commands in the CI config (`.github/workflows/*.yml`,
   `.gitlab-ci.yml`); they match, or the file explains the difference.

## Evidence for each rule

**Definition.** Every instruction traces to evidence: a manifest script,
a CI job, a config file, representative code, or an explicit user
decision.

**Use when.** Writing or auditing each line.

| Instruction kind | Evidence | Common mistake |
| --- | --- | --- |
| Command | manifest, task runner, CI step | remembered command not defined here |
| Ownership boundary | exports, callers, generated inputs | one package's pattern made a root rule |
| Required check | CI job, existing policy | optional local tool made mandatory |
| Prohibited action | existing policy, user constraint | invented approval rule |
| Compatibility | toolchain pins, support matrix | upgrade required because an example uses it |

**Do not use when.** No exception: never add a rule you cannot trace.

**Example.** "Use Bun" traces to `package.json` `packageManager: bun@1.4.2`
and `bun.lock`.

**Cost removed.** Rules that contradict the repository.

**Verify.**

1. For each rule, name its evidence in the change description.

## Revising rules instead of appending

**Definition.** Teams add one rule per correction. After weeks the file
holds rules that are stale (the tool changed), duplicate (two rules say
the same thing differently), or contradictory (a later exception was never
folded into the original rule).

**Use when.** Adding a rule that overlaps an existing one.

**Do not use when.** No exception: never append a rule next to one it
supersedes and leave both.

**Example.** A rule says "use `npm test`"; the project moved to Bun.
Replace it with "use `bun test`" instead of adding a second, newer line.

**Cost removed.** A file that grows past its budget with instructions that
no longer apply, and an agent that cannot tell which of two rules to
follow.

**Verify.**

1. Search the file for the tool, path, or convention the new rule
   mentions; merge or remove what it supersedes.
1. `python3 scripts/check_instructions.py` still reports no size warning.

## What to leave out

**Definition.** Generic advice ("follow best practices", "write clean
code"), persona text ("You are an expert"), content duplicated from the
README, secrets, and instructions that belong in a tool's config.

**Use when.** Reviewing a draft.

**Do not use when.** The text is a concrete, project-specific rule that
happens to use one of those words.

**Example.** `generic-AGENTS.example.txt` has four generic phrases and a
broken link; the checker flags all five.

**Cost removed.** Context spent on text that changes no action.

**Verify.**

1. `check_instructions.py` reports no `generic phrase` warnings.

## Size budget

**Definition.** Codex stops adding instruction files once their combined
size reaches `project_doc_max_bytes` (32 KiB by default)
([Codex AGENTS.md][codex]). Claude Code recommends under 200 lines per
CLAUDE.md because longer files reduce adherence
([Claude Code memory][cc-memory]). dotclaude's session-start hook applies
its own, stricter policy on top of that host target, not a host limit: it
warns once one file passes 150 lines and fails at 200 (Claude Code's own
target), counting each `@import` and each `.claude/rules/` file as its own
file and stripping block-level HTML comments first, since Claude Code
never sends them; and it warns once everything loaded at session start
passes about 3,000 tokens and fails at 5,000.

**Use when.** A file grows past a screen or two.

**Do not use when.** You would cut commands or boundaries to save space.
Cut prose first, then move path-specific rules into nested files or
`.claude/rules/`.

**Example.** The example `AGENTS.md` is 803 bytes and 29 lines. Across
five runs on an ambiguous task, a 12-line AGENTS.md cut wall time 27% and
tokens 24% against no file; concrete instructions ("run `npm run lint`
after any source change") beat aspirational ones ("follow best
practices") ([aaif.io][aaif-agents-md]).

**Cost removed.** Instructions silently truncated or ignored, and the
slower, costlier runs a missing or vague file produces.

**Verify.**

1. `check_instructions.py` warns above 32 KiB or 200 lines.
1. Where dotclaude is installed, its session-start hook reports the same
   file against the 150/200-line and 3,000/5,000-token thresholds.

## Example files never named AGENTS.md

**Definition.** Sample instruction files in a repository (templates,
skill assets, docs) must not use the live file names: hosts load
`AGENTS.md`/`CLAUDE.md` from directories an agent reads.

**Use when.** Shipping examples or templates of instruction files.

**Do not use when.** The file is meant to be the live instructions for that
directory.

**Example.** `AGENTS.example.md`, `CLAUDE.example.md`,
`AGENTS.template.md`; `verify.sh` copies them to real names inside a
temporary directory.

**Cost removed.** An agent obeying a sample file's rules in the wrong
project.

**Verify.**

1. `fd -H '^(AGENTS|CLAUDE)\.md$' assets docs` lists no example files.

[codex]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
[cc-memory]: https://code.claude.com/docs/en/memory
[aaif-agents-md]: https://aaif.io/blog/measuring-agents-md-what-five-runs-show-that-one-doesn-t
