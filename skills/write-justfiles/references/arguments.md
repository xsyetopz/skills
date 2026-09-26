# Recipe arguments

How command-line values reach commands. Each card is a recipe in
[`assets/examples/justfile`](../assets/examples/justfile) that
`sh assets/examples/verify.sh` checks against exact expected output
(executed with just 1.58.0 on macOS). Version numbers come from the
[just README attribute and settings tables][readme].

## Contents

- Interpolation splits arguments
- quote()
- Positional arguments
- Exported parameters
- Default parameter values
- Variadic parameters
- Option-style arguments with the arg attribute

## Interpolation splits arguments

**Definition.** `{{ arg }}` pastes the value into the command text before
the shell parses it, so the shell interprets any whitespace and
metacharacters in the value ([Avoiding argument splitting][splitting]).

**Use when.** The value is a fixed identifier you control (a closed set of
values, a path without spaces) and you want just's typo check on
`{{ name }}`.

**Do not use when.** The value comes from a user or can contain spaces,
quotes, `$`, or `;`: `just split-interpolation 'a b'` passes two
arguments, and `x; rm -rf ~` runs a second command.

**Example.**

```just
# Anti-pattern: interpolation splits arguments on whitespace
split-interpolation arg:
    @printf '[%s]\n' {{ arg }}
```

`just split-interpolation 'a b'` prints `[a]` and `[b]`.

**Cost removed.** None; this card shows the failure the next three cards
remove.

**Verify.**

1. `verify.sh` asserts the split output, so a change in just's behavior
   fails the check.

## quote()

**Definition.** `quote(s)` returns `s` wrapped in single quotes with
embedded single quotes escaped, so the shell receives it as one word
([functions][functions]; available since 0.10.4 per the
[changelog][changelog]).

**Use when.** Interpolating one value into a `sh`-compatible command line
with just's typo check kept.

**Do not use when.** The recipe shell is not POSIX-like (PowerShell,
`cmd.exe`, Python via `set shell`): the quoting rules differ.

**Example.**

```just
quoted arg:
    @printf '[%s]\n' {{ quote(arg) }}
```

**Cost removed.** Argument splitting and injection through the value.
`just quoted 'a b'` prints `[a b]`; `just quoted "it's"` prints `[it's]`.

**Verify.**

1. `verify.sh` runs both inputs and compares output exactly.

## Positional arguments

**Definition.** With the `positional-arguments` setting, or the
`[positional-arguments]` attribute on one recipe (1.29.0), just passes
recipe arguments as shell positional parameters: `$1`, `$2`, and `"$@"`
([positional arguments][positional]).

**Use when.** Forwarding any number of arbitrary arguments to a command
(`pytest`, `cargo test`, a CLI). `"$@"` preserves each argument exactly,
including empty strings and `$`.

**Do not use when.** You need just to catch parameter-name typos; it does
not notice `$2` written for `$1`.

**Example.**

```just
[positional-arguments]
positional *args:
    @printf '[%s]\n' "$@"
```

`just positional 'a b' '$HOME' ''` prints `[a b]`, `[$HOME]`, `[]`.

**Cost removed.** Lost or split arguments when forwarding to a tool.

**Verify.**

1. `verify.sh` passes a value with a space, a literal `$HOME`, and an empty
   string and compares the three output lines.

## Exported parameters

**Definition.** A parameter written `$name` is exported to the recipe's
environment. The body reads it as `"$name"`, which the shell expands
without re-parsing ([exported arguments][splitting]).

**Use when.** One arbitrary value must reach a command or script that
reads it from the environment.

**Do not use when.** The recipe also runs backticks that need the value:
exported parameters are not exported to backticks in the same scope
([README][readme]).

**Example.**

```just
exported $arg:
    @printf '[%s]\n' "$arg"
```

`just exported 'a "b" c'` prints `[a "b" c]`.

**Cost removed.** Quoting failures for values containing double quotes.

**Verify.**

1. `verify.sh` passes a value with embedded double quotes.

## Default parameter values

**Definition.** `name="value"` gives a parameter a default for when the
argument is omitted. Defaults can be expressions.

**Use when.** A recipe has a sensible default (environment `dev`, target
`all`).

**Do not use when.** Correctness depends on the value (a production
target); leave it required so omission fails.

**Example.**

```just
greet name="world":
    @echo "hello {{ name }}"
```

**Cost removed.** Callers typing common values; `just greet` prints
`hello world`, `just greet team` prints `hello team`.

**Verify.**

1. `verify.sh` runs both forms.

## Variadic parameters

**Definition.** A final parameter `+name` takes one or more arguments;
`*name` takes zero or more. Without positional arguments, interpolation
joins them with spaces.

**Use when.** Forwarding a list of files or test filters.

**Do not use when.** Values can contain spaces and you would interpolate
`{{ files }}`; use `[positional-arguments]` and `"$@"` instead.

**Example.**

```just
[positional-arguments]
at-least-one +files:
    @printf '[%s]\n' "$@"
```

**Cost removed.** Manual argument parsing inside recipes. `just
at-least-one` with no arguments exits 1 before running anything.

**Verify.**

1. `verify.sh` checks `x 'y z'` (two lines) and the empty call (exit 1).

## Option-style arguments with the arg attribute

**Definition.** `[arg("name", long="name")]` makes a parameter a
`--name VALUE` option; `short="n"` gives `-n`; `pattern="regex"` rejects
values that do not match; `value=...` makes it a flag
([attributes][attributes]: `long`/`short`/`value` since 1.46.0, `pattern`
since 1.45.0).

**Use when.** A recipe has several optional settings, where positional
order invites mistakes.

**Do not use when.** The project supports just below 1.46. Check
`just --version`, and use `set minimum-version` (1.55.0) so older
installs fail with a clear message.

**Example.**

```just
[arg("level", long="level", pattern="debug|info|warn")]
log level="info":
    @echo "level={{ level }}"
```

**Cost removed.** Invalid values reaching the command: `just log --level
loud` exits 1 without running the body.

**Verify.**

1. `verify.sh`: `--level debug` prints `level=debug`; `--level loud` exits
   1.

[readme]: https://github.com/casey/just/blob/master/README.md
[splitting]: https://just.systems/man/en/avoiding-argument-splitting.html
[positional]: https://just.systems/man/en/positional-arguments.html
[functions]: https://just.systems/man/en/functions.html
[attributes]: https://just.systems/man/en/attributes.html
[changelog]: https://github.com/casey/just/blob/master/CHANGELOG.md
