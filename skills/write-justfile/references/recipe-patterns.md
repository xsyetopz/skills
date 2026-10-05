# Recipe Patterns

Syntax verified with just 1.58.0. Manual: <https://just.systems/man/en/>.

## Contents

- [Dependencies](#dependencies)
- [Platforms](#platforms)
- [Modules and Imports](#modules-and-imports)
- [Variables](#variables)

## Dependencies

```just
build target='all': _helper        # runs before the body
release: build && tag              # `tag` runs after the body succeeds
all: (build 'x') (build 'y')       # dependencies with arguments
[parallel]
check: lint test                   # dependencies run concurrently
```

- A dependency runs at most once per invocation, even if several recipes name it, unless it is
  called with different arguments.
- A failing dependency stops the chain, so `&& tag` does not run after a failed `release` body.

## Platforms

```just
[unix]
open:
    xdg-open docs

[windows]
open:
    start docs
```

Also `[linux]` and `[macos]`. Same-name recipes are allowed only when their platform attributes are
disjoint.

## Modules and Imports

- `mod backend` loads `backend/justfile` (or `backend.just`); call `just backend test` or
  `just backend::test`. Module recipes run in the module's directory, and `just --list` shows
  `backend ...`.
- `import 'common.just'` merges a file into the current namespace, and its recipes run relative to
  the importing justfile.

## Variables

```just
ci := env('CI', 'false')
mode := if ci == "true" { "strict" } else { "loose" }
```

- `env(key, default)` reads the process environment at evaluation time.
- Override on the command line with `just mode=strict build`, before the recipe name.
