# Subcommands, naming, and changing an existing CLI

How to structure commands, name them, and change them without breaking
scripts. Guidance adapted from the [Command Line Interface Guidelines][clig]
(CC BY-SA 4.0), sections Subcommands, Naming, and Future-proofing. Parser
APIs were checked against the cobra, pflag, and clap sources and Python
3.14.7 `argparse` (local run).

## Contents

- Inventory the interface before changing it
- Consistent subcommand structure
- No ambiguous or near-duplicate names
- Naming the program and its commands
- Additive changes
- Renaming a command or flag
- Removing or changing behavior
- Human output may change; script output may not
- No catch-all subcommand, no implicit abbreviations
- No time bombs

## Inventory the interface before changing it

**Definition.** The public interface of a CLI is every subcommand, alias,
flag, positional argument, environment variable, config key, exit code,
and machine-readable output format. Record it before an edit.

**Use when.** Any edit, rename, or removal in an existing CLI.

**Do not use when.** A brand-new tool with no users; still write the
inventory once, because it becomes the help and docs outline.

**Example.**

```sh
CMD --help > before/help.txt
for sub in add list remove; do CMD "$sub" --help > "before/$sub.txt"; done
rg -n 'getenv|environ|os\.Getenv|env::var|process\.env' src/  # env vars read
rg -n '\bexit\(|sys\.exit|os\.Exit|process\.exit' src/        # exit codes
rg -n "CMD (add|list|remove)" docs/ README.md tests/ completions/  # callers
```

**Cost removed.** Renames that miss the shell completions, docs, tests, or
a CI script.

**Verify.** After the change, diff the `before/` help files against new
output; every difference is intended.

## Consistent subcommand structure

**Definition.** Pick one shape and use it everywhere: `noun verb`
(`docker container create`), which is more common, or `verb noun`. The same
verb means the same action on every noun (`create`, `list`, `delete`), and
the same flag name means the same thing in every subcommand.

**Use when.** A tool with several object types or more than a handful of
operations.

**Do not use when.** A small tool with one object: flat verbs (`todo add`)
are enough; do not add a noun level for one noun.

**Example.** `gh pr list`, `gh issue list`, `gh release list` all use
`list` with `--limit` and `--json`.

**Cost removed.** Users memorizing per-command exceptions.

**Verify.** List all subcommands and flags; the same concept never has two
names (`rm`/`delete`, `--output`/`--out`).

## No ambiguous or near-duplicate names

**Definition.** Two commands must not have names whose difference users
cannot predict.

**Use when.** Naming a new command next to existing ones.

**Do not use when.** The distinction is an established convention in the
tool's ecosystem and is documented in help (for example `apt update` versus
`apt upgrade`); new tools avoid the pair.

**Example.** `update` and `upgrade` in one tool: rename one to say what it
does (`refresh-index`, `install-updates`).

**Cost removed.** Running the wrong operation.

**Verify.** For each pair of similar names, help states the difference in
the one-line summaries.

## Naming the program and its commands

**Definition.** A program name is a short, memorable, lowercase word, with
dashes only if needed, easy to type, and not a generic word another tool
already installs.

**Use when.** Naming a new tool, or a new top-level subcommand.

**Do not use when.** Renaming a shipped program for taste; the cost to
users is large (see renaming below).

**Example.** `curl` rather than `DownloadURL`. ImageMagick's `convert`
collided with a Windows system command. Docker Compose was first named
`plum`, awkward to type with one hand, and renamed to `fig`.

**Cost removed.** Typing friction and `PATH` collisions.

**Verify.** `command -v NAME` on a clean system finds nothing; the name is
all lowercase.

## Additive changes

**Definition.** Change an interface by adding a new flag, subcommand, or
output field, and keep the old behavior as it is.

**Use when.** Any behavior change that scripts could observe.

**Do not use when.** Each addition creates another way to do the same thing;
at that point plan a deprecation instead.

**Example.** Add `--format=csv` rather than changing the default output of
`export`.

**Cost removed.** Broken user scripts after an upgrade.

**Verify.** Old invocations in the test suite still pass unchanged.

## Renaming a command or flag

**Definition.** A rename is a new name plus a deprecated alias for the old
name. The old name keeps working, prints a warning on stderr that names the
replacement and the version that removes it, and is hidden from help. Remove
it only in a documented later major version.

**Use when.** Renaming a subcommand, flag, environment variable, or config
key that has shipped.

**Do not use when.** The old name was never released (rename directly), or
it is a documented permanent alias (keep it visible and silent).

**Example.** `todo rm` became `todo remove`:

```python
for name in ("remove", "rm"):
    # No help= for the old name: argparse prints help=SUPPRESS literally
    # as "==SUPPRESS==" in the command list instead of hiding it.
    extra: dict[str, Any] = {}
    if name == "remove":
        extra["help"] = "delete a task"
    rem = subs.add_parser(
        name, parents=[common], **extra, description="Delete a task."
    )
    old = "rm" if name == "rm" else None
    rem.set_defaults(run=cmd_remove, renamed_from=old)
```

`cmd_remove` prints `warning: todo rm is deprecated and will be removed in
todo 2.0; use todo remove` to stderr. Parser support:

| Parser | Alias | Deprecation or hiding |
| --- | --- | --- |
| Python `argparse` | `add_parser(name, aliases=[...])` (shown in help) | `deprecated=True` on `add_parser` and `add_argument` (Python 3.13+); its warning does not name the replacement, so print your own |
| Go Cobra | `Command.Aliases` | `Command.Deprecated = "use X"`, `Command.Hidden`; pflag `FlagSet.MarkDeprecated(name, msg)`, `MarkHidden` |
| Rust clap | `alias`, `visible_alias` on `Command` and `Arg` | `hide(true)`; print the warning in the handler |

For environment variables and config keys, read the new name first, fall
back to the old one, and warn when only the old one is set.

Update in the same change: help text, docs, man pages, shell completions,
tests, examples, changelog (with the removal version), and every call in the
repository (`rg -n 'CMD rm\b'`).

**Cost removed.** Scripts that fail after an upgrade with "unknown command".

**Verify.** `verify.sh` checks that `todo rm 3 --force` works, warns on
stderr, prints nothing to stdout, and that `rm` is absent from `--help`.

## Removing or changing behavior

**Definition.** A change that is not additive gets an in-program warning at
least one release before it lands, telling users what to change now. Once
the user has changed (for example, passes the new flag), stop warning.

**Use when.** Changing a default, removing a flag, changing exit codes or
machine output.

**Do not use when.** Fixing behavior that contradicted the documentation;
call it a bug fix in the changelog instead.

**Example.** Release N: `--legacy-format` still works and warns
`--legacy-format will be removed in 3.0; pass --format=v2`. Release 3.0:
the flag fails with an error naming `--format=v2`.

**Cost removed.** Silent breakage.

**Verify.** A test runs the old usage and asserts the warning text and the
unchanged result.

## Human output may change; script output may not

**Definition.** Default human-readable output is not a stable interface and
may improve. `--json`, `--plain`, exit codes, and documented formats are
stable.

**Use when.** Deciding whether an output change is breaking.

**Do not use when.** The tool never offered a machine format: then scripts
parse the human output, and changing it is breaking until you add one.

**Example.** Adding a column to `todo list` is fine; renaming a key in
`todo list --json` is breaking.

**Cost removed.** Freezing the human output forever.

**Verify.** Snapshot tests cover `--json` and `--plain`, not decorative
output.

## No catch-all subcommand, no implicit abbreviations

**Definition.** Do not treat an unknown first word as an argument to a
default subcommand, and do not accept every unambiguous prefix as an alias.
Explicit, stable aliases are fine.

**Use when.** Designing top-level dispatch.

**Do not use when.** A prefix is an explicit, documented alias; it is then
part of the interface.

**Example.** If `mycmd echo hi` means `mycmd run echo hi`, a later `echo`
subcommand breaks scripts. If `mycmd i` means `install`, no later command
can start with `i`.

**Cost removed.** Being unable to add commands without breaking users.

**Verify.** An unknown subcommand exits non-zero with a suggestion.

## No time bombs

**Definition.** The command keeps working when a server you run, an
analytics endpoint, or an update check disappears.

**Use when.** Any network call not required for the command's purpose.

**Do not use when.** The network call is the command's purpose; then time
it out and report the failure (see
[timeouts](robustness-and-configuration.md#timeouts-and-recoverable-runs)).

**Example.** An update check that blocks startup for 30 s when the endpoint
is gone is a time bomb.

**Cost removed.** Tools that stop working years later.

**Verify.** Run with networking blocked; only commands that need the
network fail, promptly.

[clig]: https://clig.dev/
