# Host Discovery

Facts from the [AGENTS.md format][agents-md], OpenAI's [Codex AGENTS.md guide][codex], and Claude
Code's [memory docs][cc-memory] and [costs docs][cc-costs]. Recheck against the installed versions.

## Symlinked Files

`ln -s AGENTS.md CLAUDE.md` (or `GEMINI.md`) gives hosts one file, but Windows checkouts without
`core.symlinks` get a text file; prefer a `CLAUDE.md` containing `@AGENTS.md`. Claude Code's Edit
and Write refuse to write through the link and redirect to `AGENTS.md`. A dangling link loads
nothing, silently; `check_instructions.py CLAUDE.md` reports it as an error. If a host needs extra
rules, import instead of symlinking.

## Codex

- Global file in `~/.codex`: `AGENTS.override.md` if present, else `AGENTS.md`. Then one file per
  directory from the project root (usually the Git root) to the working directory, concatenated root
  first. Empty files are skipped; loading stops at `project_doc_max_bytes` (32 KiB).
- Launching in `repo/services/payments` loads `repo/AGENTS.md`, `repo/services/AGENTS.md`, and
  `repo/services/payments/AGENTS.md`, not `repo/services/search/AGENTS.md`.
- `AGENTS.override.md` replaces that directory's `AGENTS.md` only; parent files still load.
- `project_doc_fallback_filenames = ["TEAM_GUIDE.md"]` in `~/.codex/config.toml` adds names checked
  after the two above. Use it only for an existing file that cannot be renamed.

## Claude Code

- Reads `CLAUDE.md` files by default, and `AGENTS.md` only when no `CLAUDE.md`, `.claude/CLAUDE.md`,
  or `CLAUDE.local.md` exists in the working directory or above (v2.1.277+). The Project
  instructions setting (`claude-md-and-agents-md`) can load both.
- Share one file with a `CLAUDE.md` that starts with `@AGENTS.md`, then adds Claude-only rules. Do
  not copy AGENTS.md content; copies drift.
- `@path` imports resolve relative to the importing file, nest four hops, are not parsed inside code
  spans or fences, and need one-time approval when outside the working directory. Wrap a path in
  backticks to avoid importing it.
- `CLAUDE.local.md` at the project root holds personal instructions and loads after `CLAUDE.md`. Add
  it to `.gitignore`; verify with `git check-ignore CLAUDE.local.md`.
- `.claude/rules/*.md` load at startup, or only when Claude works with files matching a `paths`
  frontmatter glob list:

  ```markdown
  ---
  paths:
    - "tests/**/*.py"
  ---
  ```

- A `# Compact instructions` section in `CLAUDE.md` tells compaction what to keep; add it only when
  sessions compact and lose decisions or exact errors ([costs docs][cc-costs]).

## Nested Files

A subproject `AGENTS.md` adds rules for its subtree and loads with its ancestors: in Codex when
launched inside the subtree, in Claude Code when it reads files there. State only what differs from
the root.

[agents-md]: https://agents.md/
[codex]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
[cc-memory]: https://code.claude.com/docs/en/memory
[cc-costs]: https://code.claude.com/docs/en/costs
