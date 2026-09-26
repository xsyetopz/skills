---
name: write-justfiles
description: >-
  Writes, debugs, and reviews justfiles for the just command runner: recipes,
  parameters and quoting, dependencies, attributes, settings, dotenv, modules.
  Use when adding or fixing just recipes. Not for replacing a build system.
---

# Write Justfiles

Expose a project's existing commands as `just` recipes that pass arguments
exactly, fail when the wrapped command fails, and document themselves in
`just --list`. Every construct below is a recipe in
`assets/examples/justfile` that `assets/examples/verify.sh` runs with
exact expected output.

## Workflow

1. Record `just --version` and read the existing justfile, imports,
   modules, and settings. Use only features the project's minimum version
   supports; the cards give the version for each attribute and setting.
1. Find the canonical command for each operation (package scripts, `cargo`,
   `uv run`, a script under `scripts/`); the recipe calls it, it does not
   re-implement it ([wrapping][wrapping]).
1. Decide how arguments reach the command
   ([arguments](references/arguments.md)). Anything user-supplied goes
   through `[positional-arguments]` with `"$@"`, an exported
   (dollar-prefixed) parameter, or `quote()`; never bare `{{ arg }}`.
1. Add dependencies, attributes (`[group]`, `[private]`, `[confirm]`,
   platform attributes), and settings only where the cards' **Use when**
   applies.
1. Run `just --fmt` then `just --fmt --check`, `just --list`, and
   `just --dry-run RECIPE`.
1. Run each new recipe for real: normal arguments, an argument with a
   space and a `$`, a failing underlying command (check just's exit
   status), and the confirm path for destructive recipes.
1. Report the commands run and their output.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| New recipe for an existing command | [Wrapping](references/recipes.md#wrapping-a-canonical-command) |
| Arguments with spaces split or break | [Interpolation splits](references/arguments.md#interpolation-splits-arguments), [quote()](references/arguments.md#quote), [positional](references/arguments.md#positional-arguments), [exported](references/arguments.md#exported-parameters) |
| Optional parameter | [Defaults](references/arguments.md#default-parameter-values) |
| Forward a list of files or test filters | [Variadic](references/arguments.md#variadic-parameters) |
| `--flag value` style options, value validation | [arg attribute](references/arguments.md#option-style-arguments-with-the-arg-attribute) |
| Step A must run before B | [Prior dependencies](references/recipes.md#prior-dependencies) |
| Step must run only after success | [Subsequent dependencies](references/recipes.md#subsequent-dependencies) |
| Same recipe for several targets | [Dependency arguments](references/recipes.md#dependencies-with-arguments) |
| Independent slow steps | [Parallel](references/recipes.md#parallel-dependencies) |
| `cd` or variables lost between lines | [Line shells](references/recipes.md#line-recipes-run-one-shell-per-line), [Script recipes](references/recipes.md#script-recipes) |
| Recipe reports success after a failure | [Failure stops](references/recipes.md#failure-stops-the-recipe), [ignore-error prefix](references/recipes.md#the-ignore-error-prefix) |
| Deletes, deploys, publishes | [Confirm](references/recipes.md#confirmation-for-destructive-recipes) |
| Different commands per OS | [Platform attributes](references/recipes.md#platform-attributes) |
| Recipe runs in the wrong directory | [Working directory](references/recipes.md#working-directory) |
| `just --list` is unclear | [Default, private, groups, docs](references/recipes.md#default-private-grouped-and-documented-recipes) |
| Subproject recipes | [Modules](references/recipes.md#modules) |
| Shared values, paths | [Variables](references/variables-settings.md#variables-and-strings), [env()](references/variables-settings.md#env-with-a-default), [overrides](references/variables-settings.md#command-line-variable-overrides) |
| Value depends on CI or OS | [Conditionals](references/variables-settings.md#conditional-expressions) |
| Every recipe is slow or fails on a missing tool | [Backticks and lazy](references/variables-settings.md#backticks-and-set-lazy), [require()](references/variables-settings.md#require-and-which) |
| Tool reads environment variables | [Exporting](references/variables-settings.md#exporting-to-recipes), [Dotenv](references/variables-settings.md#dotenv-loading) |
| Pipelines hide failures, Windows shell | [Shell setting](references/variables-settings.md#shell-setting) |
| Contributors on old just | [minimum-version](references/variables-settings.md#minimum-version) |
| Proving the justfile works | [Verification](references/verification.md) |

## Rules

- A recipe calls the project's canonical command; it does not duplicate
  build logic, and it does not replace a working build system.
- User-supplied values never reach a shell through bare `{{ arg }}`.
- A recipe's exit status is the wrapped command's: no `-` prefix,
  `|| true`, or unchecked pipeline to make a failing check pass.
- Destructive recipes carry `[confirm]`; CI passes `--yes` explicitly.
- Use features only if the project's just version has them; state the
  minimum (`set minimum-version`, 1.55.0+) when adding newer attributes.
- Do not use the deprecated `env_var`, `env_var_or_default`,
  `set windows-shell`, or `set windows-powershell` in new code.
- `just --fmt --check` and `--dry-run` prove syntax and command text, not
  behavior; run the recipe.

## Bundled tools

- `assets/examples/verify.sh`: runs every example recipe in a temporary
  copy and compares output and exit status; prints `SKIP` if just is
  missing.
- `scripts/check_justfiles.py PATH...`: runs `just --fmt --check` on every
  justfile under the paths; exit 0 pass, 1 format failure, 2 bad input.

## References

- [Arguments](references/arguments.md): interpolation, `quote()`,
  positional and exported arguments, defaults, variadics, `[arg]`.
- [Recipes](references/recipes.md): wrapping, dependencies (prior,
  subsequent, with arguments, parallel), line versus script recipes,
  failure handling, confirm, platforms, working directory, listing,
  modules.
- [Variables and settings](references/variables-settings.md): strings,
  `env()`, overrides, conditionals, backticks and `set lazy`, exports,
  dotenv, shell, `require()`, `minimum-version`.
- [Verification](references/verification.md): `--fmt --check`, listing,
  `--dry-run`, `--evaluate`, JSON dump, argument probes, exit status,
  batch checks.

## Completion evidence

The report includes `just --version`, the `just --fmt --check` result, the
`just --list` output for new recipes, each new recipe's real run with an
argument containing a space (output shown), a failing-command run with
its exit status, and anything not run (for example a Windows-only
recipe), stated as not verified.

[wrapping]: references/recipes.md#wrapping-a-canonical-command
