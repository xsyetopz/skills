# Host discovery

Where each coding agent looks for instruction files, in what order, and
how to confirm what it loaded. Facts are from the
[AGENTS.md format][agents-md], OpenAI's [Codex AGENTS.md guide][codex], and
Claude Code's [memory documentation][cc-memory]; recheck them against the
installed versions.

## Contents

- AGENTS.md format
- Codex discovery chain
- Codex override files
- Codex fallback file names
- Claude Code: CLAUDE.md or AGENTS.md
- Claude Code: sharing one file with @AGENTS.md
- Claude Code: CLAUDE.local.md
- Claude Code: path-scoped rules
- Claude Code: imports
- Nested files in monorepos
- Confirming what loaded

## AGENTS.md format

**Definition.** Plain Markdown with no required schema or headings. Agents
read the nearest `AGENTS.md` in the directory tree; nested files let
subprojects add their own instructions ([agents.md][agents-md]).

**Use when.** The repository serves several agents (Codex, Claude Code,
Cursor, and others that read AGENTS.md).

**Do not use when.** A host needs its own file for a feature AGENTS.md
lacks (Claude Code `paths` rules). Add that file and keep shared rules in
AGENTS.md.

**Example.** `assets/examples/AGENTS.example.md`.

**Cost removed.** The same rules maintained in several host-specific
files.

**Verify.**

1. The file renders as ordinary Markdown and passes the checker.

## Codex discovery chain

**Definition.** Codex reads one global file from its home directory
(`~/.codex`: `AGENTS.override.md` if present, else `AGENTS.md`), then walks
from the project root (usually the Git root) down to the working
directory, taking at most one file per directory. It concatenates them
root first, so deeper files come later and take precedence. It skips empty
files and stops at `project_doc_max_bytes` (32 KiB default)
([Codex][codex]).

**Use when.** Deciding where a rule belongs when Codex users launch in
different directories.

**Do not use when.** You expect a sibling directory's AGENTS.md to apply.
Codex loads only the chain from root to the launch directory.

**Example.** Launching in `repo/services/payments` loads `repo/AGENTS.md`,
then `repo/services/AGENTS.md`, then `repo/services/payments/AGENTS.md`;
`repo/services/search/AGENTS.md` is not loaded.

**Cost removed.** Rules that never reach the agent.

**Verify.**

1. Run `codex --ask-for-approval never "Summarize the current
   instructions."` from the launch directory; Codex lists guidance sources
   in discovery order ([Codex][codex]).

## Codex override files

**Definition.** `AGENTS.override.md` in a directory replaces that
directory's `AGENTS.md` (in the Codex home, the global `AGENTS.md`).

**Use when.** One directory needs a temporary or local replacement for its
instructions without editing the shared file.

**Do not use when.** You expect it to replace the whole chain; it replaces
only its own directory's file.

**Example.** `services/payments/AGENTS.override.md` replaces
`services/payments/AGENTS.md`; `repo/AGENTS.md` still loads.

**Cost removed.** Editing a shared file for a personal or temporary rule.

**Verify.**

1. The Codex summary prompt above names the override file.

## Codex fallback file names

**Definition.** `project_doc_fallback_filenames` in Codex configuration
adds other file names Codex checks after `AGENTS.override.md` and
`AGENTS.md` in each directory ([Codex][codex]).

**Use when.** A repository already keeps instructions under another name
and cannot rename it.

**Do not use when.** You are creating a new file; name it `AGENTS.md`.

**Example.**

```toml
# ~/.codex/config.toml
project_doc_fallback_filenames = ["TEAM_GUIDE.md"]
```

**Cost removed.** A duplicate of an existing instructions file.

**Verify.**

1. The Codex summary prompt lists the fallback file.

## Claude Code: CLAUDE.md or AGENTS.md

**Definition.** By default Claude Code reads `CLAUDE.md` files. It reads
`AGENTS.md` instead only when no `CLAUDE.md`, `.claude/CLAUDE.md`, or
`CLAUDE.local.md` exists in the working directory or above (v2.1.277+). The
**Project instructions** setting can load both
(`claude-md-and-agents-md`) ([memory docs][cc-memory]).

**Use when.** A repository used with Claude Code has, or will get, both
files.

**Do not use when.** You would add a `CLAUDE.md` or `CLAUDE.local.md` to an
AGENTS.md-only repository without importing AGENTS.md: Claude Code then
stops reading AGENTS.md.

**Example.** This repository has only `AGENTS.md`, so Claude Code loads it
and shows `no CLAUDE.md found; AGENTS.md loaded: ...` in an interactive
session.

**Cost removed.** Instructions that silently stop loading.

**Verify.**

1. Run `/context` in Claude Code and check **Memory files**.

## Claude Code: sharing one file with @AGENTS.md

**Definition.** A `CLAUDE.md` that imports AGENTS.md with an `@AGENTS.md`
line and adds Claude-specific rules.

**Use when.** Claude Code and other agents share the repository and Claude
needs a few extra rules.

**Do not use when.** You would copy AGENTS.md content into CLAUDE.md; the
copies drift.

**Example.**

```markdown
@AGENTS.md

## Claude Code

- Use the `unittest` command above; `pytest` is not installed here.
```

**Cost removed.** Two diverging instruction files.

**Verify.**

1. `python3 scripts/check_instructions.py CLAUDE.md` resolves the import;
   `/context` lists both files.

## Claude Code: CLAUDE.local.md

**Definition.** `CLAUDE.local.md` at the project root holds personal,
uncommitted instructions. It loads after `CLAUDE.md`; list it in
`.gitignore` ([memory docs][cc-memory]).

**Use when.** A developer needs private preferences (sandbox URLs, local
data paths).

**Do not use when.** The project relies on AGENTS.md alone. Creating
`CLAUDE.local.md` makes Claude Code stop reading AGENTS.md unless the
setting loads both.

**Example.** `echo 'CLAUDE.local.md' >> .gitignore`

**Cost removed.** Personal settings committed for everyone.

**Verify.**

1. `git check-ignore CLAUDE.local.md` prints the path.

## Claude Code: path-scoped rules

**Definition.** Markdown files in `.claude/rules/` load at startup, or,
with a `paths` frontmatter list of globs, only when Claude works with
matching files ([memory docs][cc-memory]).

**Use when.** A rule applies to one area (tests, migrations, a frontend
package) and would otherwise enlarge every session.

**Do not use when.** The rule applies everywhere; put it in the main file.

**Example.**

```markdown
---
paths:
  - "tests/**/*.py"
---

# Test rules

- Each test name states the behavior: `test_rounds_half_even_cents`.
```

**Cost removed.** Context spent on rules irrelevant to the current files.

**Verify.**

1. `/context` shows the rule only after Claude reads a matching file.

## Claude Code: imports

**Definition.** `@path` in a CLAUDE.md imports another file, resolved
relative to the importing file. Imports nest up to four hops. Claude Code
does not parse imports in code spans or fences. Imports from outside the
working directory need one-time approval ([memory docs][cc-memory]).

**Use when.** Reusing a file (AGENTS.md, a shared style guide) instead of
copying it.

**Do not use when.** You mention a path you do not want loaded; wrap it
in backticks.

**Example.** `@docs/testing.md` imports; `` `@docs/testing.md` `` does
not.

**Cost removed.** Copies of the same rules in several files.

**Verify.**

1. `check_instructions.py` reports missing imports and imports deeper
   than four hops.

## Nested files in monorepos

**Definition.** A subproject's own `AGENTS.md` adds rules for its subtree.
Hosts load it along with its ancestors: Codex when launched inside the
subtree, Claude Code when it reads files there.

**Use when.** A package has its own toolchain or commands (a Bun web
client inside a Python repository).

**Do not use when.** It would repeat root rules; state only what differs.

**Example.** `nested-AGENTS.example.md` becomes `web/AGENTS.md` and lists
`bun install --frozen-lockfile` and `bun test`.

**Cost removed.** Root files full of per-package exceptions.

**Verify.**

1. Launch or read from inside the subtree and confirm both files load
   (Codex summary prompt, Claude `/context`).

## Confirming what loaded

**Definition.** Each host can show its loaded instructions. Codex lists
sources when asked to summarize its instructions. Claude Code lists
**Memory files** in `/context` and prints a line when it loads AGENTS.md
instead of CLAUDE.md.

**Use when.** You created, moved, or renamed any instruction file.

**Do not use when.** No exception: a file's existence does not prove it
loaded.

**Example.**

```sh
codex --ask-for-approval never "Summarize the current instructions."
```

**Cost removed.** Debugging an agent that "ignores" a file it never read.

**Verify.**

1. Record the host version and the listed files in the report. If the host
   is not installed, mark the result not verified.

[agents-md]: https://agents.md/
[codex]: https://learn.chatgpt.com/docs/agent-configuration/agents-md
[cc-memory]: https://code.claude.com/docs/en/memory
