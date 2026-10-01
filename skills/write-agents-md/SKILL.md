---
name: write-agents-md
description: >-
  Writes and trims AGENTS.md and CLAUDE.md instruction files so agents follow
  the project's commands and rules. Use when creating or auditing agent
  instructions.
---

# Write AGENTS.md

Give coding agents the facts they cannot infer from the tree: commands that work, conventions that
differ from defaults, and boundaries with the alternative to use. Find existing files first,
ignoring `.gitignore`:

```sh
fd -HI -E node_modules -E .git \
  '^(AGENTS|CLAUDE|CLAUDE\.local)\.md$|^AGENTS\.override\.md$'
```

Also check `.claude/rules/`, and edit what you find in place.

## Rules

- Do not run destructive, publishing, deploy, migration, network, or credentialed commands; run at
  most their `--help` or a dry run. Run every other command you list, from the directory you state,
  before writing it down. For an existing file, list its commands first with
  `python3 scripts/check_instructions.py --commands FILE`. Invented or stale commands are the most
  common failure, and an agent trusts them. Report any you could not run.
- Delete what the model does anyway ("write clean code", "run the tests") and what a linter or
  formatter already enforces; keep a rule only if you can point to a manifest, CI file, or user
  decision behind it. Extra rules dilute the ones that matter.
- Write boundaries as "do X instead of Y" with the reason: "`src/gen/` is generated; edit
  `schema.json` and run `make proto`". A bare prohibition leaves the agent guessing.
- Keep it short: Claude Code recommends under 200 lines per CLAUDE.md because longer files reduce
  adherence; Codex stops reading at `project_doc_max_bytes` (32 KiB default) combined ([Claude Code
  memory][cc-memory], [Codex][codex]). Cut prose first, then move path-specific rules to nested
  files or `.claude/rules/`.
- Adding a rule that supersedes an older one: remove or merge the older one in the same edit, or the
  file contradicts itself.
- Claude Code reads `AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md`, or `CLAUDE.local.md`
  exists. Adding any of them to an AGENTS.md-only repository silently stops AGENTS.md loading; make
  it start with `@AGENTS.md` (Claude Code, [memory][cc-memory]).
- Codex loads one file per directory from the project root down to the launch directory, root first,
  so deeper files win; sibling directories are never loaded, and `AGENTS.override.md` replaces only
  its own directory's `AGENTS.md` (Codex, [guide][codex]). Put a rule where every launch directory
  that needs it sees it.
- Name sample instruction files `*.example.md` or `*.template.md`, never `AGENTS.md` or `CLAUDE.md`,
  or hosts load them as live instructions.
- Confirm loading in each host you can run: `/context` in Claude Code (Memory files),
  `codex exec -s read-only "Summarize the current instructions."` in Codex (sends them to OpenAI;
  only where Codex is approved). Mark hosts you could not check as not verified; a file's existence
  does not prove it loaded.

## Workflow

1. Gather evidence: manifests, lockfiles, task-runner recipes, CI workflows, formatter and linter
   configs, generated-file markers.
1. Write commands, non-default conventions, boundaries, and what "done" means (the checks to pass
   before finishing).
1. Place rules: root file for repository-wide facts, nested `AGENTS.md` per subproject that states
   only what differs, `.claude/rules/` with `paths` globs for Claude-only path rules.
1. Run `python3 scripts/check_instructions.py AGENTS.md [CLAUDE.md ...]`, fix errors, then rerun
   each command it extracts.

## Scripts

- `python3 scripts/check_instructions.py FILE... [--commands | --json]` resolves relative links, `@`
  imports (four hops), and symlinks; warns on size and generic phrases; extracts commands. Exit 0
  clean, 1 missing link, import, or dangling symlink, 2 bad input. On Windows, use `py -3` for
  `python3`.

## References

- Read [`references/hosts.md`](references/hosts.md) when a file is shared between hosts, symlinked,
  imported, nested, overridden, personal (`CLAUDE.local.md`), or path-scoped.

[cc-memory]: https://code.claude.com/docs/en/memory
[codex]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
