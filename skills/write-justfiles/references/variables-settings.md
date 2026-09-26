# Variables, settings, and functions

Values just computes and settings that change how recipes run. Examples
live in [`assets/examples/`](../assets/examples/justfile);
`sh assets/examples/verify.sh` checks them (just 1.58.0, macOS). Setting
and function versions come from the [settings table and function
list][readme].

## Contents

- Variables and strings
- env() with a default
- Command-line variable overrides
- Conditional expressions
- Backticks and set lazy
- Exporting to recipes
- Dotenv loading
- Shell setting
- require() and which()
- minimum-version

## Variables and strings

**Definition.** `name := expression` defines a variable. Expressions
combine strings with `+`, paths with `/`, and function calls. Single-quoted
strings take no escapes; double-quoted strings support `\n`, `\t`, `\"`,
and `\u{...}` (1.36.0); triple-quoted forms are dedented
([strings][strings]). Recipes read variables with `{{ name }}`.

**Use when.** Several recipes use the value (paths, image names, flags).

**Do not use when.** Only one shell command needs the value; keep it in
the command.

**Example.**

```just
build_dir := justfile_directory() / "build"
image := "registry.example.com/app:" + env("TAG", "dev")
```

**Cost removed.** Repeated literals that drift apart.

**Verify.**

1. `just --evaluate build_dir` prints the computed value;
   `verify.sh` runs `just --evaluate cache_dir`.

## env() with a default

**Definition.** `env(key)` returns an environment variable and aborts
when it is unset; `env(key, default)` (1.15.0) returns `default` instead.
`env_var` and `env_var_or_default` are deprecated aliases
([functions][functions]).

**Use when.** Configuration comes from the caller's environment (CI
variables, cache paths).

**Do not use when.** Loading from a `.env` file; that is the dotenv
setting, not `env()`.

**Example.**

```just
cache_dir := env("CACHE_DIR", "/tmp/example-cache")

show-cache:
    @echo "{{ cache_dir }}"
```

**Cost removed.** Hard-coded machine paths.

**Verify.**

1. `verify.sh`: without `CACHE_DIR` prints `/tmp/example-cache`; with
   `CACHE_DIR=/tmp/other` prints `/tmp/other`.
1. `rg -n 'env_var(_or_default)?\(' justfile` finds no deprecated aliases.

## Command-line variable overrides

**Definition.** `just name=value recipe` (or `--set name value`) overrides
a variable for that invocation
([setting variables from the command line][cli-vars]).

**Use when.** One run needs a different value without editing the file
or exporting a variable.

**Do not use when.** The value is a secret; it lands in shell history and
process listings.

**Example.**

```sh
just cache_dir=/tmp/cli show-cache   # prints /tmp/cli
```

**Cost removed.** Editing the justfile for one run.

**Verify.**

1. `verify.sh` runs the command above and compares output.

## Conditional expressions

**Definition.** `if a == b { x } else { y }` (also `!=`, `=~` regex, and
`&&`/`||` since 1.37.0) chooses a value when the variable is evaluated.
Only the taken branch is evaluated ([conditional
expressions][conditionals]).

**Use when.** A value depends on an environment variable or OS.

**Do not use when.** Whole recipes differ per OS; use platform
attributes.

**Example.**

```just
mode := if env("CI", "") != "" { "ci" } else { "local" }

show-mode:
    @echo "mode={{ mode }} os={{ os() }}"
```

`os()` returns Rust's OS names (`macos`, `linux`, `windows`), not `uname`
output.

**Cost removed.** Shell `if` blocks duplicated across recipes.

**Verify.**

1. `verify.sh` runs with and without `CI=1`. On macOS it expects
   `os=macos` (measured: `darwin` was wrong).

## Backticks and set lazy

**Definition.** `` name := `command` `` runs `command` with the configured
shell and stores its trimmed output. Without `set lazy` (1.47.0), just
evaluates every assignment on every invocation, so a backtick runs even
when the chosen recipe never uses it ([backticks][backticks],
[settings][readme]).

**Use when.** A value must come from a command (git revision, tool
version), and either the command is fast and safe to run every time or
`set lazy` is on.

**Do not use when.** The command is slow, networked, or can fail in some
environments where unrelated recipes must still work. Use `set lazy`,
move the command into the recipe that needs it, or call `shell()` in
that recipe's expression.

**Example.**

```just
set lazy

marker := `touch lazy.marker && echo created`

unrelated:
    @echo unrelated
```

**Cost removed.** Commands that run on every invocation for nothing.
Measured: `just --justfile eager.just unrelated` created `eager.marker`;
the same run with `set lazy` did not create `lazy.marker`.

**Verify.**

1. `verify.sh` checks both marker files.

## Exporting to recipes

**Definition.** `export name := value` exports one variable to recipe
environments, `set export` exports all variables and parameters, and
`[env("NAME", "VALUE")]` (1.47.0) sets one variable for one recipe
([attributes][attributes]).

**Use when.** A tool reads configuration from the environment
(`RUST_LOG`, `PYTHONPATH`, `NODE_ENV`).

**Do not use when.** Backticks in the same scope need the value; exports
do not reach them ([README][readme]).

**Example.**

```just
[env("GREETING", "hi")]
with-env:
    @echo "$GREETING"
```

**Cost removed.** `NAME=value cmd` prefixes repeated across lines.

**Verify.**

1. `verify.sh`: `just with-env` prints `hi`.

## Dotenv loading

**Definition.** `set dotenv-load` loads `.env` if present;
`set dotenv-filename := "name"` changes the file name;
`set dotenv-required` (1.28.0) fails when the file is missing;
`set dotenv-path` loads a specific path and errors if absent
([dotenv settings][dotenv]).

**Use when.** A project keeps local, untracked configuration in a dotenv
file.

**Do not use when.** The values are secrets that could leak through
`just --evaluate` or logs, or CI provides the variables directly.

**Example.**

```just
set dotenv-load
set dotenv-filename := "example.env"
set dotenv-required

show-token:
    @echo "token=$API_TOKEN"
```

**Cost removed.** Sourcing files by hand before running recipes, and,
with `dotenv-required`, silent runs without configuration.

**Verify.**

1. `verify.sh`: prints `token=from-dotenv`; with the file renamed, exits 1.

## Shell setting

**Definition.** `set shell := ["command", "args"...]` selects the program
that runs recipe lines and backticks; the default is `sh -cu`. On Windows,
use `[windows] set shell := [...]`; `set windows-shell` and
`set windows-powershell` are deprecated ([shell][shell],
[settings][readme]).

**Use when.** Recipes need bash features (`set -o pipefail`, arrays) or the
project targets PowerShell on Windows.

**Do not use when.** Plain POSIX commands suffice; the default `sh`
exists on every Unix and keeps recipes portable.

**Example.**

```just
set shell := ["bash", "-euo", "pipefail", "-c"]

[windows]
set shell := ["powershell.exe", "-NoLogo", "-Command"]
```

**Cost removed.** Pipelines that hide failures: with `pipefail`, `false |
cat` fails the recipe.

**Verify.**

1. Add a recipe with `false | cat`; it must exit non-zero with pipefail.

## require() and which()

**Definition.** `require(name)` (1.39.0) returns the full path of an
executable on `PATH` or halts with an error naming it; `which(name)`
returns an empty string when the executable is missing
([functions][functions]).

**Use when.** Recipes depend on a tool that may be missing. An early
error naming the tool beats a later "command not found".

**Do not use when.** Only one rarely used recipe needs the tool. Without
`set lazy`, every invocation evaluates the assignment, so a missing tool
breaks every recipe. Put the check in that recipe or enable `set lazy`.

**Example.**

```just
tool := require("definitely-not-installed-tool")

use-tool:
    @echo "{{ tool }}"
```

**Cost removed.** Confusing mid-recipe failures.

**Verify.**

1. `verify.sh`: exits 1 and stderr names `definitely-not-installed-tool`.

## minimum-version

**Definition.** `set minimum-version := "1.55.0"` (1.55.0) makes just fail
with a clear error when it is older than the given version
([settings][readme]).

**Use when.** The justfile uses features contributors may lack (`[arg]`,
`[parallel]`, `[script]`, `set lazy`).

**Do not use when.** Contributors run just older than 1.55.0. Those
versions do not know the setting and fail with a parse error instead of
the clear message; document the minimum in the README instead.

**Example.**

```just
set minimum-version := "1.55.0"
```

**Cost removed.** Obscure parse errors on old just versions.

**Verify.**

1. `just --version` is at least the stated version. The example justfile
   uses this setting and passes `verify.sh`.

[readme]: https://github.com/casey/just/blob/master/README.md
[strings]: https://just.systems/man/en/strings.html
[functions]: https://just.systems/man/en/functions.html
[cli-vars]: https://just.systems/man/en/setting-variables-from-the-command-line.html
[conditionals]: https://just.systems/man/en/conditional-expressions.html
[backticks]: https://just.systems/man/en/command-evaluation-using-backticks.html
[attributes]: https://just.systems/man/en/attributes.html
[dotenv]: https://just.systems/man/en/dotenv-settings.html
[shell]: https://just.systems/man/en/shell.html
