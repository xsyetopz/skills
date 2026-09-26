# Verification

Commands that prove a justfile parses, is formatted, exposes the intended
recipes, and runs with the intended arguments and exit status.
`sh assets/examples/verify.sh` executed all of them with just 1.58.0.

## Contents

- Format check
- Listing and inspection
- Dry run
- Evaluate variables
- Machine-readable dump
- Argument probe
- Exit-status check
- Batch format check across a repository

## Format check

**Definition.** `just --fmt --check` parses the justfile and exits non-zero
with a diff when it differs from just's canonical format; `just --fmt`
rewrites it ([README][readme]). The formatter also sorts attributes
alphabetically (measured: `[arg(...)]` before `[group(...)]`).

**Use when.** After every edit, and in CI.

**Do not use when.** You need proof that recipes run; it checks only
syntax and layout.

**Example.**

```sh
just --fmt --check
just --fmt --check --justfile tools.just
```

**Cost removed.** Syntax errors and formatting churn in review.

**Verify.**

1. Exit status 0; `verify.sh` runs it on every example file.

## Listing and inspection

**Definition.** `just --list` shows public recipes with groups and doc
comments; `just --show NAME` prints one recipe; `just --summary` prints
recipe names on one line, including module recipes such as
`tools::version`.

**Use when.** Checking what users see, or scripting over recipe names.

**Do not use when.** Checking behavior; these print only definitions.

**Example.**

```sh
just --list
just --show release
just --summary
```

**Cost removed.** Hidden or undocumented recipes.

**Verify.**

1. `verify.sh` checks `--summary` contains `build` and `tools::version`.

## Dry run

**Definition.** `just --dry-run RECIPE` prints the commands a recipe would
run (on stderr) without executing them, and exits 0.

**Use when.** Checking interpolation and dependency order before a
destructive or slow recipe runs.

**Do not use when.** Proving the recipe works. Nothing executes, and the
exit status is 0 even when the first line is `exit 3`. Measured on
1.58.0: backticks in assignments were not evaluated under `--dry-run`
either (`eager.just` created no marker file), so command-derived values
go unexercised.

**Example.**

```sh
just --dry-run fail-fast; echo "status=$?"   # status=0
```

**Cost removed.** Surprise commands from interpolation.

**Verify.**

1. `verify.sh` asserts exit 0 and empty stdout for `--dry-run fail-fast`.

## Evaluate variables

**Definition.** `just --evaluate` prints all variables; `just --evaluate
NAME` prints one.

**Use when.** Checking computed paths, `env()` defaults, and conditional
values.

**Do not use when.** Variables hold secrets and the output is logged.

**Example.**

```sh
just --evaluate cache_dir
```

**Cost removed.** Guessing a variable's value.

**Verify.**

1. `verify.sh` expects `/tmp/example-cache`.

## Machine-readable dump

**Definition.** `just --dump --dump-format json` (or `--json`, 1.48.0)
prints the parsed justfile as JSON: recipes, parameters, attributes,
dependencies, settings.

**Use when.** Writing checks over recipes (every recipe has a doc comment,
no recipe uses a forbidden command).

**Do not use when.** A human-readable `--list` answers the question.

**Example.**

```sh
just --dump --dump-format json | python3 -c \
  'import json,sys; print(sorted(json.load(sys.stdin)["recipes"]))'
```

**Cost removed.** Fragile regex parsing of justfiles.

**Verify.**

1. `verify.sh` asserts `build` is among the dumped recipes.

## Argument probe

**Definition.** A recipe, or a temporary edit, that prints each received
argument on its own delimited line, exposing splitting, empty arguments,
and unexpanded `$`.

**Use when.** Writing any recipe that forwards user arguments.

**Do not use when.** No exception: every forwarding recipe gets a probe.

**Example.**

```just
[positional-arguments]
positional *args:
    @printf '[%s]\n' "$@"
```

```sh
just positional 'a b' '$HOME' ''
# [a b]
# [$HOME]
# []
```

**Cost removed.** Arguments silently split or dropped.

**Verify.**

1. Compare the printed lines with the arguments passed, including a value
   with a space, a `$`, a quote, and an empty string.

## Exit-status check

**Definition.** Running a recipe whose underlying command fails and
checking just's own exit status.

**Use when.** A recipe wraps a check (tests, lint) that CI relies on.

**Do not use when.** No exception; always rerun it after adding `-`
prefixes, `|| true`, or pipelines.

**Example.**

```sh
just fail-fast; echo "status=$?"        # status=3
just masked-failure; echo "status=$?"   # status=0: the failure is hidden
```

**Cost removed.** CI passing while the wrapped check fails.

**Verify.**

1. `verify.sh` expects 3 and 0 respectively.

## Batch format check across a repository

**Definition.** `scripts/check_justfiles.py PATH...` finds `justfile`,
`.justfile`, and `*.just` files (skipping `.git`, `node_modules`, `.venv`,
`target`, `.build`, and directory symlinks) and runs
`just --fmt --check --justfile FILE` on each without a shell. Exit 0: all
pass; 1: a file fails; 2: bad input, no files, missing just, or timeout.
It never rewrites files.

**Use when.** Several justfiles exist (modules, subprojects).

**Do not use when.** One file: run `just --fmt --check` directly.

**Example.**

```sh
python3 scripts/check_justfiles.py .
python3 scripts/check_justfiles.py --just /usr/local/bin/just --timeout 30 .
```

**Cost removed.** Unchecked module files.

**Verify.**

1. `python3 scripts/test_check_justfiles.py` passes.

[readme]: https://github.com/casey/just/blob/master/README.md
