# Current Just API

This reference was verified against Just 1.58.0 on 2026-09-12. Recheck the
[programmer's manual](https://just.systems/man/en/) and
[current release](https://github.com/casey/just/releases/latest) before relying
on version-sensitive syntax.

## Environment variables

Use the overloaded `env` function:

```just
required := env("REQUIRED_TOKEN")
cache := env("XDG_CACHE_HOME", env("HOME") + "/.cache")
```

- `env(key)` aborts when `key` is unset.
- `env(key, default)` returns `default` when `key` is unset.
- `env_var(key)` and `env_var_or_default(key, default)` are deprecated aliases.
  Do not add them to new or edited justfiles.

Dotenv loading is a separate setting. State the intended policy explicitly with
`set dotenv-load := true` or `set dotenv-load := false`; do not mistake `env()`
for dotenv loading.

## Recipes and composition

Recipe dependencies run before the dependent recipe. A recipe with no body can
serve as a named aggregate:

```just
check: lint test
```

Arguments are positional unless attributes define command-line behavior. Use
documented recipe parameters rather than parsing `$@` inside an unrelated shell.
Use modules when separate justfiles have distinct ownership, not merely to make
the root file shorter.

Each recipe line normally runs in a fresh shell. Use a shebang recipe when the
whole body must run as one script, or `[script]` where its interpreter contract
is supported by the repository's minimum Just version.

## Paths, commands, and failure behavior

Double-quote interpolated filesystem paths in recipe commands. Prefer
`require("tool")` when evaluation must fail immediately if a program is missing.
Use `which("tool")` only when absence has an intentional alternate path.

Do not prefix commands with `-` to hide an unexpected failure. If a tool is
optional, test its availability, print an explicit skip reason, and keep the
recipe's success criteria truthful.

Use `justfile_directory()` for paths owned by the justfile and
`invocation_directory()` only when behavior intentionally follows the caller's
working directory.

## Inspection and validation

- `just --fmt --check` parses the selected justfile and checks canonical
  formatting without rewriting it.
- `just --fmt` rewrites it; inspect that diff before continuing.
- `just --list`, `just --show NAME`, and `just --dump` expose the resolved task
  surface.
- `just --dry-run NAME` prints recipe commands without executing them. It does
  not prove runtime behavior or make command substitution harmless.
- `just --summary` is useful for automation that needs recipe names only.

`just-lsp analyze PATH` provides the same diagnostics used by supported editor
clients. It complements Just's parser and formatter; it does not replace a real
recipe run.

The authoritative function list, including version annotations and deprecated
aliases, is in the
[built-in functions reference](https://just.systems/man/en/functions.html).
