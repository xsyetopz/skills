---
name: write-agents-md
description: >-
  Writes and audits AGENTS.md and CLAUDE.md repository instructions for Codex,
  Claude Code, and other agents: verified commands, conventions, boundaries,
  nesting, imports. Use when creating or fixing agent instruction files. Not
  for skills or hooks.
---

# Write AGENTS.md

Give coding agents the project facts they cannot infer: the commands that
build and test the repository, the conventions that differ from defaults,
and the boundaries with their alternatives. Place each file where every
target host loads it.

## Workflow

1. Inventory existing instruction files and their scope:
   `fd -H '^(AGENTS|CLAUDE|CLAUDE\.local)\.md$|^AGENTS\.override\.md$'`
   and `.claude/rules/`. Note which hosts the team uses.
1. Gather evidence: manifests and lockfiles, task runner recipes, CI
   workflows, formatter and linter configs, generated-file markers.
1. Run each candidate command from the stated directory and keep only the
   ones that work ([commands](references/content.md#commands-that-run)).
1. Write the sections: commands, non-default conventions, boundaries with
   alternatives, definition of done
   ([content](references/content.md)).
1. Place the rules: root file for repository-wide facts, nested files for
   subprojects, `CLAUDE.md` importing `@AGENTS.md` when Claude needs extras,
   `.claude/rules/` for path-scoped Claude rules
   ([hosts](references/hosts.md)).
1. Check: `python3 scripts/check_instructions.py AGENTS.md [CLAUDE.md ...]`
   (links, imports, size, generic phrases), then run every command from
   `--commands` output again.
1. Confirm loading in each available host (`/context` in Claude Code, the
   Codex summary prompt); state hosts you could not check.

## Route the task to a card

| Task | Card |
| --- | --- |
| Which commands to list | [Commands that run](references/content.md#commands-that-run) |
| Describing the layout | [Project map](references/content.md#project-map) |
| Team conventions | [Non-default conventions](references/content.md#non-default-conventions) |
| Generated files, owned areas, publishing | [Boundaries](references/content.md#boundaries-with-reasons) |
| What "done" means | [Definition of done](references/content.md#definition-of-done) |
| Is this rule justified? | [Evidence](references/content.md#evidence-for-each-rule), [what to leave out](references/content.md#what-to-leave-out) |
| File is long | [Size budget](references/content.md#size-budget), [path-scoped rules](references/hosts.md#claude-code-path-scoped-rules) |
| Shipping sample instruction files | [Example file names](references/content.md#example-files-never-named-agentsmd) |
| Codex users launch in subdirectories | [Codex chain](references/hosts.md#codex-discovery-chain), [overrides](references/hosts.md#codex-override-files), [fallback names](references/hosts.md#codex-fallback-file-names) |
| Repository has AGENTS.md and Claude users | [CLAUDE.md or AGENTS.md](references/hosts.md#claude-code-claudemd-or-agentsmd), [sharing with @AGENTS.md](references/hosts.md#claude-code-sharing-one-file-with-agentsmd) |
| Personal, uncommitted instructions | [CLAUDE.local.md](references/hosts.md#claude-code-claudelocalmd) |
| Reusing another file | [Imports](references/hosts.md#claude-code-imports) |
| Monorepo packages | [Nested files](references/hosts.md#nested-files-in-monorepos) |
| Did the host load it? | [Confirming what loaded](references/hosts.md#confirming-what-loaded) |

## Rules

- Every command in the file was run successfully from its stated directory
  during this change; report any that could not be run.
- Every rule traces to evidence in the repository or an explicit user
  decision; no generic advice, persona text, or invented approval rules.
- Do not add `CLAUDE.md` or `CLAUDE.local.md` to an AGENTS.md-only
  repository without importing `@AGENTS.md`: Claude Code stops reading
  AGENTS.md.
- Sample instruction files are named `*.example.md` or `*.template.md`,
  never `AGENTS.md` or `CLAUDE.md`.
- Keep files within the hosts' limits: Codex stops at 32 KiB combined by
  default; Claude Code recommends under 200 lines per file.
- Preserve existing instruction files' scope and owners; edit in place
  rather than adding a parallel file.

## Bundled tools

- `scripts/check_instructions.py FILE... [--commands]`: resolves links and
  `@` imports (four hops), warns on size and generic phrases, and extracts
  commands; exit 1 on missing links or imports.
- `assets/examples/*.example.md` and `verify.sh`: a root AGENTS.md, a
  CLAUDE.md that imports it, a path-scoped rule, a nested web AGENTS.md,
  and a generic file the checker rejects; `verify.sh` installs them in a
  temporary demo project and runs every listed command.
- `assets/AGENTS.template.md`: a starting skeleton.

## References

- [Instruction content](references/content.md): commands, project map,
  conventions, boundaries, done criteria, evidence, exclusions, size,
  example file names.
- [Host discovery](references/hosts.md): AGENTS.md format, Codex chain,
  overrides and fallbacks, Claude Code selection, imports, local files,
  path-scoped rules, nesting, confirming what loaded.

## Completion evidence

The report lists each instruction file changed and its scope, each command
with the directory it ran in and its exit status, the evidence for each
convention and boundary, the checker output, and which hosts confirmed
loading (or that a host was unavailable).
