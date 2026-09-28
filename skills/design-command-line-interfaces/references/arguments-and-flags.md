# Arguments, flags, and interactivity

How a command accepts input. Guidance adapted from the
[Command Line Interface Guidelines][clig] (CC BY-SA 4.0), sections
Arguments and flags and Interactivity, and from the
[POSIX Utility Syntax Guidelines][posix]. Runnable examples are in
[`assets/examples/todo.py`](../assets/examples/todo.py).

## Contents

- Flags over positional arguments
- Long names for every flag, short names for common ones
- Standard flag names
- Flags that work before and after the subcommand
- `-` for stdin and stdout, `--` to end options
- Optional values need a keyword
- Secrets never in flags or environment variables
- Prompts only on a terminal, and --no-input
- Confirmation scaled to danger

## Flags over positional arguments

**Definition.** Positional arguments are ordered values (`cp SRC DST`);
flags are named (`--output FILE`). Prefer flags. Several positional
arguments of the same kind are fine (`rm a b c`, which also works with
globs).

**Use when.** Adding any input that is not the command's single obvious
object.

**Do not use when.** The command is a frequent primary action whose order
people already know (`cp SRC DST`, `mv`). Two positional arguments with
different roles elsewhere are a design smell.

**Example.** `deploy --env prod --region eu-west-1 app` rather than
`deploy app prod eu-west-1`.

**Cost removed.** Ambiguity when a later version needs another input, and
swapped arguments that nothing detects.

**Verify.** Every positional argument in `--help` is either the single
primary object or a list of the same kind.

## Long names for every flag, short names for common ones

**Definition.** Every flag has a `--long-name`. Only frequently typed flags
also get a one-letter form, because the short namespace is small and shared
across subcommands.

**Use when.** Adding a flag.

**Do not use when.** Giving a rare flag a short form "because it is free":
that letter is then unavailable for a common flag later.

**Example.** `-q, --quiet` and `-f, --force` in `todo.py`; `--store` and
`--no-input` have no short form.

**Cost removed.** Unreadable scripts full of `-x -Z -k`, and short-flag
collisions between subcommands.

**Verify.** In `--help`, no flag has only a short form.

## Standard flag names

**Definition.** Reuse the name and meaning other tools already use, so
people can guess flags.

| Flag | Meaning |
| --- | --- |
| `-a`, `--all` | all items |
| `-d`, `--debug` | debugging output |
| `-f`, `--force` | skip confirmation; do the destructive action |
| `-h`, `--help` | help, and nothing else |
| `-n`, `--dry-run` | describe changes without making them |
| `-o`, `--output` | output file |
| `-p`, `--port` | port |
| `-q`, `--quiet` | less output |
| `-u`, `--user` | user |
| `--json` | JSON output |
| `--no-input` | never prompt |
| `--version` | version |

`-v` means verbose in some tools and version in others; avoid giving it
either meaning in a new tool, or match the ecosystem you ship into.

**Use when.** Naming any flag with one of these meanings.

**Do not use when.** The existing tool already uses the letter differently
and scripts depend on it; renaming needs the
[rename procedure](subcommands-and-evolution.md#renaming-a-command-or-flag).

**Example.** `rsync -n` and `git add -n` are dry runs; `todo remove -f`
forces.

**Cost removed.** A trip to `--help` for every flag.

**Verify.** Compare the flag list with the table; each match uses the
standard meaning.

## Flags that work before and after the subcommand

**Definition.** Global flags (`--store`, `--quiet`, `--no-color`) are
accepted on either side of the subcommand with the same meaning. People
press the up arrow and append a flag at the end.

**Use when.** Any tool with subcommands and global flags.

**Do not use when.** The parser cannot do it; then reject the misplaced
flag with an error that says where it goes. Never accept it and ignore it.

**Example.** In Python `argparse`, adding the same flags to subparsers with
`parents=[common]` silently overwrites a value given before the subcommand
with the subparser's default: `todo --store x.json add t` wrote to the
default path (local run, Python 3.14.7). `parents=` also shares the
`Action` objects, so `set_defaults` on one parser changes the default for
all of them. `todo.py` fixes both:

```python
common = argparse.ArgumentParser(
    add_help=False, argument_default=argparse.SUPPRESS
)
# ... parents=[common] on the top parser and on every subparser ...
args = top.parse_args(argv)
for name, value in GLOBAL_DEFAULTS.items():
    vars(args).setdefault(name, value)
```

Cobra gives the same result with persistent flags (`PersistentFlags()`);
clap with `global = true` on the argument.

**Cost removed.** A flag that is accepted but has no effect, which is worse
than an error.

**Verify.** Run both orders against a temporary path and compare the
effect; `verify.sh` does this for `--store`.

## `-` for stdin and stdout, `--` to end options

**Definition.** Where a command takes a file operand, `-` means stdin (or
stdout for output) (POSIX guideline 13). The first `--` ends option parsing,
so later arguments that start with `-` are operands (POSIX guideline 10).

**Use when.** Any file input or output; any command that forwards
arguments or accepts arbitrary names.

**Do not use when.** The parser library already implements `--`; do not
reimplement it, only test it.

**Example.** `git log --format=%s | todo add -` adds one task per line;
`todo add -- -weird-title` adds a task whose title starts with `-`.

**Cost removed.** Temporary files between commands; operands that the
parser mistakes for flags.

**Verify.** `printf 'a\n' | CMD -` reads the pipe; `CMD -- -x` treats
`-x` as an operand.

## Optional values need a keyword

**Definition.** A flag whose value is optional takes a keyword such as
`none` for "no value", not an empty string.

**Use when.** A flag selects an optional file or setting.

**Do not use when.** A separate `--no-FLAG` reads better.

**Example.** `ssh -F none` runs with no config file.

**Cost removed.** Ambiguity about whether the next word is the flag's value
or an operand.

**Verify.** `CMD --flag none` has the documented effect.

## Secrets never in flags or environment variables

**Definition.** Accept secrets through a file (`--password-file PATH`),
stdin, a credential helper or keychain, or a secret service. Not through a
flag value, which appears in `ps` output and shell history, and not
through environment variables, which leak into child processes, logs,
`docker inspect`, and `systemctl show`.

**Use when.** Passwords, tokens, API keys, private keys.

**Do not use when.** An existing tool already reads a token from an
environment variable and users depend on it: keep it, add the file or stdin
path, and document the safer path first.

**Example.** `curl -H @headers.txt` reads a header from a file instead of
`-H "Authorization: Bearer $TOKEN"`.

**Cost removed.** Credentials exposed to every local user and to logs.

**Verify.** `ps -o args` while the command runs shows no secret; no
`--password VALUE` flag exists.

## Prompts only on a terminal, and --no-input

**Definition.** Prompt for missing input only when stdin is a terminal.
Otherwise fail at once and name the flag that supplies the value.
`--no-input` disables every prompt. Never make a prompt the only way to
supply a value. Turn off echo for password prompts. Ctrl-C always works.

**Use when.** Any command that may ask the user something.

**Do not use when.** The command runs only in scripts; then take flags only.

**Example.** `todo remove 3` on a terminal asks `Delete task 3 ('...')?
[y/N]`. With stdin from `/dev/null`, or with `--no-input`, it exits 2 with
`pass --force to delete without a prompt`.

**Cost removed.** CI jobs that hang until a timeout waiting for an answer.

**Verify.** `CMD ARGS </dev/null` finishes and names the flag;
`check_cli.py` reports no `bare-noninteractive` finding.

## Confirmation scaled to danger

**Definition.** Match confirmation to how hard the action is to undo:

- Mild (delete one local file): no prompt, or a prompt when the command
  name does not already say "delete".
- Moderate (delete a directory or a remote resource, bulk change): prompt
  on a terminal; `--force` in scripts; offer `--dry-run`.
- Severe (delete an application, server, or database): ask the user to type
  the resource name; accept `--confirm=NAME` for scripts.

Also treat indirect destruction as severe: changing a count from 10 to 1
that deletes nine things.

**Use when.** Any command that deletes, overwrites, or changes remote state.

**Do not use when.** Asking for trivial, easily undone actions; frequent
prompts train people to answer yes without reading.

**Example.** `todo remove` is moderate: prompt on a terminal, `--force`
otherwise.

**Cost removed.** Accidental destruction from a mistyped or reused command
line.

**Verify.** Without `--force` and without a terminal, the command changes
nothing and exits non-zero; `--dry-run` output matches what the real run
then does.

[clig]: https://clig.dev/
[posix]: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap12.html
