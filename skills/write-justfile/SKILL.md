---
name: write-justfile
description: >-
  Writes and fixes justfiles and just recipes, such as forwarding arguments,
  recipes that pass when the command fails, dotenv loading,
  confirm on destructive recipes, and Windows.
  Use when adding a just command, a recipe misbehaves, or moving from make to just.
  Not for CI or npm scripts.
---

# Write Justfile

Expose a project's existing commands as `just` recipes that pass arguments exactly, fail when the
wrapped command fails, and show up in `just --list`. Checked against just 1.58.0. Recipes run under
`sh`, including on Windows (Git for Windows or Cygwin `sh` must be on `PATH`). To use another shell
there, put the `[windows]` attribute on the line before
`set shell := ["powershell.exe", "-NoLogo", "-Command"]`.

## Rules

- Each recipe line runs in its own shell, so `cd dir` on one line does not affect the next and
  variables do not carry over. Put multi-line logic in a shebang recipe (`#!/usr/bin/env bash`) or
  `[script("bash")]`, or join lines with `&&` or `\`.
- A shebang or `[script]` recipe does not stop at the first failing command: `false` followed by
  `echo ok` exits 0. Start the body with `set -euo pipefail`, because line recipes stop on failure
  and script bodies do not.
- Never paste a user-supplied value with bare `{{ arg }}`: the shell splits it (`just f 'a b'`
  passes two arguments) and runs `;` commands. Use a parameter declared with a leading `$` (it is
  exported, so read `"${x}"`), `{{ quote(arg) }}`, or `set positional-arguments` with `"$@"`.
- For a variadic (`*args` or `+args`), use `"$@"`, not `{{ quote(args) }}`. just joins variadics
  into one string first, so `just test -k 'a b'` gives pytest one argument `-k a b`, while `"$@"`
  gives `-k` and `a b`.
- The exit status must be the wrapped command's. Do not add a `-` prefix, `|| true`, or an unchecked
  pipeline to make a failing check pass; search review diffs with `rg -n '^\s+-@?' justfile`.
- `just --fmt --check` and `just --dry-run RECIPE` prove syntax and command text, not behavior
  (dry-run exits 0 even when the first line is `exit 3`). Run each new recipe: normal arguments, an
  argument with a space and a `$`, and a failing command (read just's exit status). For deploy,
  publish, push, or destructive recipes, show `just --dry-run RECIPE` and ask the user instead of
  running them.
- Call the project's canonical command (`uv run pytest`, `cargo test`, a script under `scripts/`)
  instead of reimplementing it. Do not translate an incremental Makefile build: just does not track
  file timestamps, so a recipe that calls `make` keeps it.
- `set dotenv-load` (or `dotenv-path`, `dotenv-filename`) loads `.env` into recipes' environment,
  and the search walks up parent directories, so a stray `.env` above the project is loaded. A
  missing file is silently ignored unless `set dotenv-required` is also set, which then fails with
  `dotenv file not found`. Dotenv values are environment variables, not just variables: read secrets
  and dotenv values as `$FOO`, never `{{ FOO }}` or `{{ env('FOO') }}`, because just echoes
  interpolated lines and `--dry-run` prints them.
- `set export` exports every just variable to recipes; a `$`-prefixed parameter exports just that
  parameter; `[env("NAME", "VALUE")]` exports for one recipe. Without one of these a just variable
  is text substitution only, not an environment variable.
- Every backtick assignment (``name := `cmd` ``) runs on every invocation, even when the chosen
  recipe never uses it, so a slow or failing command slows or breaks `just --list`. Add `set lazy`,
  or move the command into the recipe.
- Recipes run in the justfile's directory, not where you invoked just. `[no-cd]` runs in the
  invocation directory (for recipes that take relative paths from the user);
  `[working-directory('sub')]` runs elsewhere.
- Destructive recipes carry `[confirm]`; without a terminal they fail with `was not confirmed`
  unless CI passes `--yes`. Never pass `--yes` yourself or put it in the recipe; ask the user to run
  it.
- Attributes and settings newer than the project's minimum just version fail to parse. Check
  `just --version` and the CI install, and state the floor with `set minimum-version := "X.Y.Z"`
  when you add a newer one.
- In a recipe body, write a literal `{{` as `{{{{`.

## Workflow

1. Read the existing justfile, imports, modules, and settings, plus `just --version`.
1. Write the recipe: parameters with defaults (`build target='all':`), dependencies, and `[private]`
   or `_name` for helpers.
1. Run `just --fmt` then `just --fmt --check`, `just --list`, and `just --dry-run RECIPE`.
1. Run the recipe for real, except the recipes the rules above say to ask about, and name each
   recipe you did not run in the report.

## Scripts

- `python3 scripts/check_justfiles.py PATH...` runs `just --fmt --check` on every justfile under the
  paths (it never runs recipes). Exit 0 pass, 1 format failure, 2 bad input. On Windows, use `py -3`
  for `python3`.

## References

- Read [recipe patterns](references/recipe-patterns.md) when you need dependency ordering, parallel
  steps, dependencies with arguments, platform-specific recipes, modules, imports, or conditionals.
