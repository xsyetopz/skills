# Recipes, dependencies, and execution

Recipe structure, ordering, and how commands run and fail. Examples live
in [`assets/examples/justfile`](../assets/examples/justfile);
`sh assets/examples/verify.sh` checks them (just 1.58.0, macOS).

## Contents

- Wrapping a canonical command
- Prior dependencies
- Subsequent dependencies
- Dependencies with arguments
- Parallel dependencies
- Line recipes run one shell per line
- Script recipes
- Failure stops the recipe
- The ignore-error prefix
- Confirmation for destructive recipes
- Platform attributes
- Working directory
- Default, private, grouped, and documented recipes
- Modules

## Wrapping a canonical command

**Definition.** A named entry point that calls the project's real tool
(`cargo`, `pytest`, `bun`, a script in `scripts/`) with fixed flags. The
logic stays in the tool or script.

**Use when.** The team repeats a command line, or CI and developers must
run the same command.

**Do not use when.** Re-implementing build logic (file dependency graphs,
incremental builds) in recipe lines. just has no file-timestamp logic;
keep that in the build tool.

**Example.**

```just
[positional-arguments]
test *args:
    uv run pytest "$@"
```

`"$@"` passes each argument through unchanged. Measured with just 1.58.0:
`just test -k 'foo bar'` gives pytest `['-k', 'foo bar']`, while
`{{ quote(args) }}` joins the variadic arguments first and gives one
argument, `['-k foo bar']` (see
[positional arguments](arguments.md#positional-arguments)).

**Cost removed.** Divergence between developer and CI commands.

**Verify.**

1. `just --show test` prints the recipe, and it matches the command in
   the CI config.
1. The argument probe ([verification.md](verification.md#argument-probe))
   shows every argument arriving separately.

## Prior dependencies

**Definition.** `recipe: dep1 dep2` runs each dependency before the recipe,
each at most once per invocation
([dependencies][dependencies]).

**Use when.** A step requires another first (build before package).

**Do not use when.** Unrelated checks should all report: dependencies stop
at the first failure. If you still list them in one aggregate recipe,
accept that the first failure stops the rest.

**Example.**

```just
build: _prepare
    @echo build

[private]
_prepare:
    @echo prepare
```

**Cost removed.** Forgotten setup steps. `just build` prints `prepare`,
`build`.

**Verify.**

1. `verify.sh` compares the output order.

## Subsequent dependencies

**Definition.** Dependencies after `&&` run after the recipe body
succeeds (since 0.9.9 per the [changelog][changelog]).

**Use when.** A follow-up must run only after success (notify, tag).

**Do not use when.** The follow-up is cleanup that must run even on
failure. just has no `finally`; use a script recipe with a shell `trap`.

**Example.**

```just
release: build && _announce
    @echo release
```

**Cost removed.** Announcing a release that failed. `just release` prints
`prepare`, `build`, `release`, `announce`.

**Verify.**

1. `verify.sh` compares the four lines in order.

## Dependencies with arguments

**Definition.** `(recipe "arg")` in a dependency list calls a
parameterized recipe, once per distinct argument list.

**Use when.** Running one parameterized recipe for several targets.

**Do not use when.** The target list is dynamic; call the recipe from a
script loop.

**Example.**

```just
deploy-all: (deploy "staging") (deploy "production")

[private]
deploy target:
    @echo "deploy {{ target }}"
```

**Cost removed.** Duplicated recipes per target.

**Verify.**

1. `verify.sh` expects `deploy staging` then `deploy production`.

## Parallel dependencies

**Definition.** `[parallel]` (1.42.0) runs a recipe's dependencies
concurrently instead of in order ([attributes][attributes]).

**Use when.** Independent, slow dependencies (lint and type-check).

**Do not use when.** Dependencies share output files, ports, or a lock
file, or their output must not interleave.

**Example.**

```just
[parallel]
parallel-pair: (_rendezvous "a" "b") (_rendezvous "b" "a")
```

Each `_rendezvous` touches its own marker and waits up to 5 s for the
other's, so the pair finishes only if both run at once.

**Cost removed.** Wall time drops from the sum of the dependencies to
roughly the longest one. The example proves concurrency
deterministically instead of timing it.

**Verify.**

1. `verify.sh` runs `just parallel-pair`; without `[parallel]` the first
   dependency times out and exits 1.

## Line recipes run one shell per line

**Definition.** Each line of an ordinary recipe runs in a new shell, so
`cd`, variables, and `set` options do not carry to the next line. The
default shell is `sh -cu` ([shell][shell]).

**Use when.** Each line is an independent command.

**Do not use when.** Lines depend on each other's state; use a script
recipe, or join with `&&` on one line.

**Example.**

```just
line-shells:
    @cd /
    @pwd
```

prints the justfile directory, not `/`.

**Cost removed.** None; it corrects a common wrong assumption.

**Verify.**

1. `verify.sh` expects the working copy directory.

## Script recipes

**Definition.** `[script]` (1.33.0; stable since 1.44.0) or a `#!` shebang
line makes the whole body one script file run by one interpreter. The
default `[script]` interpreter is `sh -eu`; change it with
`set script-interpreter` ([script recipes][script]).

**Use when.** The body needs loops, variables across lines, `trap`, or a
non-shell language (`[script("python3")]`).

**Do not use when.** The body is independent commands. Line recipes echo
each command and report the exact failing line.

**Example.**

```just
[script]
one-script:
    cd /
    pwd
```

prints `/`.

**Cost removed.** State lost between lines.

**Verify.**

1. `verify.sh` expects `/`.

## Failure stops the recipe

**Definition.** A line that exits non-zero stops the recipe and skips
later lines and dependents; just exits with that status.

**Use when.** Always; it is the default.

**Do not use when.** A command's failure is expected and handled. Test
for it explicitly (`if ! cmd; then ...; fi` in a script recipe).

**Example.**

```just
fail-fast:
    @exit 3
    @echo unreachable
```

**Cost removed.** Later steps running on a broken state. `just fail-fast`
exits 3 and prints nothing.

**Verify.**

1. `verify.sh` expects exit status 3 and empty stdout.

## The ignore-error prefix

**Definition.** A line starting with `-` ignores that line's failure.

**Use when.** Rarely: a best-effort cleanup whose failure is harmless,
with a comment saying so.

**Do not use when.** It would hide a failing check or tool; the recipe
then reports success.

**Example.**

```just
masked-failure:
    -@exit 3
    @echo "still reported success"
```

exits 0.

**Cost removed.** None; this is the anti-pattern. Search for it in review:
`rg -n '^\s+-@?' justfile`.

**Verify.**

1. `verify.sh` shows exit 0 despite the failing line.

## Confirmation for destructive recipes

**Definition.** `[confirm]` (1.17.0) or `[confirm("prompt")]` (1.23.0)
asks before running; `just --yes` answers yes in automation
([confirmation][confirm]).

**Use when.** The recipe deletes data, deploys, or publishes.

**Do not use when.** Never remove the attribute so CI can run the recipe
unattended; pass `--yes` in the CI command.

**Example.**

```just
[confirm("Delete the example cache?")]
clean:
    @rm -rf '{{ cache_dir }}'
    @echo "removed {{ cache_dir }}"
```

**Cost removed.** Accidental destructive runs. Without a terminal and
without `--yes`, `just clean` exits 1 and removes nothing.

**Verify.**

1. `verify.sh` runs it with stdin from `/dev/null` (exit 1) and with
   `--yes` (runs).

## Platform attributes

**Definition.** `[unix]`, `[windows]`, `[linux]`, `[macos]` (1.8.0) enable
a recipe only on that platform. Two recipes can share a name if their
platforms do not overlap ([attributes][attributes]).

**Use when.** The command differs by platform.

**Do not use when.** The only difference is the shell: set
`[windows] set shell := [...]` instead (`set windows-shell` is deprecated
since 1.56.0 in favor of this, per the [settings table][readme]).

**Example.**

```just
[unix]
platform:
    @echo unix

[windows]
platform:
    @echo windows
```

**Cost removed.** Recipes that break on one OS.

**Verify.**

1. `verify.sh` expects `unix` on macOS/Linux. The Windows branch needs a
   Windows run (not run locally).

## Working directory

**Definition.** Recipes run in the justfile's directory by default.
`[working-directory('path')]` (1.38.0) runs one recipe elsewhere; `[no-cd]`
(1.9.0) runs it in the directory just was invoked from;
`justfile_directory()` and `invocation_directory()` return those paths
([attributes][attributes], [functions][functions]).

**Use when.** A recipe must run inside a subproject, or act on the
caller's directory (a formatter run from any subdirectory).

**Do not use when.** Writing `cd dir && cmd` in one line where the
attribute states intent more clearly.

**Example.**

```just
[working-directory('sub')]
in-sub:
    @basename "$PWD"

[no-cd]
from-caller:
    @pwd
```

**Cost removed.** Commands operating on the wrong directory.

**Verify.**

1. `verify.sh`: `just in-sub` prints `sub`; `cd sub && just from-caller`
   prints the `sub` path.

## Default, private, grouped, and documented recipes

**Definition.** The first recipe, or the one marked `[default]` (1.43.0),
runs when `just` gets no arguments. `[private]` or a leading `_` hides a
recipe from `--list`. `[group('name')]` (1.27.0) groups the listing. A `#`
comment directly above a recipe becomes its `--list` description, or
`[doc('text')]` (1.27.0) sets it.

**Use when.** Always, so `just --list` is the documentation.

**Do not use when.** Never hide a recipe users are expected to call.

**Example.**

```just
# List recipes (the default recipe)
[default]
[private]
help:
    @just --justfile '{{ justfile() }}' --list
```

**Cost removed.** Reading the justfile to find the right recipe.

**Verify.**

1. `just --list` shows groups and descriptions and no `_` recipes;
   `verify.sh` checks `--summary` includes public recipes and the module.

## Modules

**Definition.** `mod name` loads `name.just` (or `name/mod.just`) as a
submodule called as `just name::recipe`. `import 'file'` (1.18.0) merges
another file into the current namespace
([modules][modules], [imports][imports]).

**Use when.** Subprojects own their recipes (`mod frontend`), or several
justfiles reuse a shared recipe file.

**Do not use when.** The only goal is shortening a small file; one flat
justfile reads better.

**Example.**

```just
mod tools
```

with `tools.just`:

```just
# Print the tool version
version:
    @echo "tools 1.0"
```

**Cost removed.** One very large justfile with unrelated owners.

**Verify.**

1. `verify.sh`: `just tools::version` prints `tools 1.0`.

[readme]: https://github.com/casey/just/blob/master/README.md
[changelog]: https://github.com/casey/just/blob/master/CHANGELOG.md
[dependencies]: https://just.systems/man/en/dependencies.html
[attributes]: https://just.systems/man/en/attributes.html
[shell]: https://just.systems/man/en/shell.html
[script]: https://just.systems/man/en/script-recipes.html
[confirm]: https://just.systems/man/en/requiring-confirmation-for-recipes.html
[functions]: https://just.systems/man/en/functions.html
[modules]: https://just.systems/man/en/modules.html
[imports]: https://just.systems/man/en/imports.html
