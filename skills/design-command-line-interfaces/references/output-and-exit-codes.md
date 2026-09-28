# Output, streams, and exit codes

How a command reports results so that both people and scripts can use it.
Guidance adapted from the [Command Line Interface Guidelines][clig]
(CC BY-SA 4.0), sections Basics and Output. Runnable examples are in
[`assets/examples/todo.py`](../assets/examples/todo.py);
`sh assets/examples/verify.sh` checks them (Python 3.14.7, macOS, local run).

## Contents

- Parse with a library
- Exit codes
- Data on stdout, messages on stderr
- Terminal detection
- Color
- Machine-readable output: --json and --plain
- Success output and --quiet
- Report state changes and next commands
- Pager for long output

## Parse with a library

**Definition.** Use the language's standard or a well-known argument parser
(Python `argparse`, Click, Typer; Go Cobra or urfave/cli; Rust clap; Java
picocli; Kotlin Clikt; Node oclif; Swift swift-argument-parser) instead of
reading `argv` by hand.

**Use when.** Always, unless the program takes no options at all.

**Do not use when.** The project already uses a parser: extend that one.
Two parsers in one program give two sets of help and error formats.

**Example.** `todo_bad.py` hand-parses `sys.argv`; it treats `-h` as an
unknown command and prints its error to stdout with exit 0. `todo.py` uses
`argparse`, which gives `-h`, `--help`, usage errors on stderr, and exit 2
without extra code.

**Cost removed.** Hand-written help, error handling, and option syntax
(`--flag=value`, grouped short flags, `--`) that drift from convention.

**Verify.** `check_cli.py -- CMD` reports no `help-long`, `help-short`, or
`unknown-flag` findings.

## Exit codes

**Definition.** Exit 0 on success and non-zero on failure. Map distinct
non-zero codes to the failures a script needs to tell apart.

**Use when.** Every command. Scripts, CI, `&&`, and `set -e` read only the
exit status.

**Do not use when.** Inventing many codes that nobody documents. Two or three
documented codes are more useful than twenty undocumented ones.

**Example.** `todo.py` uses 0 success, 1 runtime failure (missing task,
unreadable store), 2 usage error (argparse's convention, also Click's
`UsageError`), 130 on Ctrl-C (shells report 128 + signal number; SIGINT is
2). BSD `sysexits.h` defines another scheme (`EX_USAGE` 64); pick one
scheme and list it in `--help` or the docs.

**Cost removed.** Scripts that continue after a failure because the command
printed an error and exited 0.

**Verify.**

1. Run the failing case and print `$?`; it is non-zero.
1. `check_cli.py` reports no `unknown-flag` finding (exit 0 on an unknown
   flag is the most common defect).

## Data on stdout, messages on stderr

**Definition.** The command's primary output, and anything machine-readable,
goes to stdout. Progress, status, warnings, errors, and prompts go to
stderr.

**Use when.** Every command. A pipe carries stdout only, so messages on
stdout corrupt the next program's input.

**Do not use when.** Help requested with `--help` is the requested output;
print it to stdout so `CMD --help | less` works. Usage shown because of an
error goes to stderr.

**Example.** `todo add` prints nothing to stdout and `Added 1 task(s) to …`
to stderr; `todo list` prints tasks to stdout and the empty-list hint to
stderr.

**Cost removed.** `CMD | jq` failing on a status line; errors vanishing into
a file with `CMD > out`.

**Verify.** `CMD ARGS >out 2>err`, then inspect both files: `out` holds only
data.

## Terminal detection

**Definition.** Check whether each stream is an interactive terminal
(Python `stream.isatty()`, Node `process.stdout.isTTY`, Go
`golang.org/x/term.IsTerminal(fd)`, Rust `std::io::IsTerminal`). A
terminal means a person is probably reading.

**Use when.** Deciding on color, animation, progress bars, pagers, prompts,
and table wrapping. Check each stream separately: with stdout piped, stderr
can still be a terminal.

**Do not use when.** The output format for scripts (`--json`, `--plain`)
must not change with the terminal; scripts rely on it.

**Example.** `color_enabled(args, sys.stdout)` in `todo.py`.

**Cost removed.** Escape codes and spinner frames in logs, files, and CI
output.

**Verify.** `check_cli.py` runs every probe with pipes and reports
`ansi-when-piped` if any escape sequence appears.

## Color

**Definition.** Color highlights what needs attention (an error, a changed
value). Disable it when: the stream is not a terminal, `NO_COLOR` is set to
a non-empty value ([no-color.org](https://no-color.org/)), `TERM` is
`dumb`, or the user passes `--no-color`. An app-specific variable
(`MYAPP_NO_COLOR`) is optional.

**Use when.** Output for people on a terminal.

**Do not use when.** Everything would be colored: color that marks
everything marks nothing. Never make color the only carrier of meaning.

**Example.**

```python
def color_enabled(args, stream) -> bool:
    return (
        not args.no_color
        and not os.environ.get("NO_COLOR")
        and os.environ.get("TERM") != "dumb"
        and stream.isatty()
    )
```

**Cost removed.** Unreadable logs and broken `grep` matches from escape
codes.

**Verify.** `CMD | cat -v` shows no `^[[`; `NO_COLOR=1 CMD` on a terminal
shows no color.

## Machine-readable output: --json and --plain

**Definition.** `--json` prints structured output; `--plain` prints one
record per line with no wrapping, alignment, or decoration, for `grep`,
`cut`, and `awk`.

**Use when.** The default human output is formatted (tables, wrapped cells,
grouped sections), or scripts need fields. Tell script authors to use these
flags, because default human output may change.

**Do not use when.** The default output is already one plain record per line
and has no structure a script needs; do not add flags without a need.

**Example.** `todo list` prints `ID<TAB>TITLE` per line; `todo list --json`
prints a JSON array. `verify.sh` parses it.

**Cost removed.** Scripts that scrape formatted tables and break when a
column width changes.

**Verify.** `CMD --json | python3 -m json.tool` (or `jq .`) exits 0.

## Success output and --quiet

**Definition.** On success print a short confirmation, not nothing and not
a debug log. `-q`/`--quiet` suppresses non-essential messages.

**Use when.** A command that changes state or runs longer than a moment.

**Do not use when.** The command is a filter whose output is the result
(`cat`-like); extra messages would be noise there.

**Example.** `todo add` confirms on stderr; `todo add -q` prints nothing.

**Cost removed.** People re-running a silent command because they cannot
tell whether it worked; scripts redirecting stderr to `/dev/null` and losing
errors too.

**Verify.** Run with and without `-q`; errors still appear with `-q`.

## Report state changes and next commands

**Definition.** After a change, say what changed and the resulting state.
When commands form a workflow, suggest the next command. Make actions that
cross the program's boundary (writing files the user did not name, network
calls) explicit.

**Use when.** State changes that are not visible otherwise, and multi-step
workflows.

**Do not use when.** The output is consumed by scripts; keep suggestions on
stderr so they do not enter pipes.

**Example.** `Added 1 task(s) to /path/tasks.json` names the file written.
The empty list prints `No tasks. Add one with: todo add TITLE`.

**Cost removed.** Users guessing where data went or what to run next.

**Verify.** Read the output of each state-changing command: it names the
object and the new state.

## Pager for long output

**Definition.** Page long output through `$PAGER` or `less -FIRX` (no
paging if it fits one screen, case-insensitive search, raw color codes,
screen kept after exit), only when stdout is a terminal.

**Use when.** Output routinely exceeds a screen (diffs, logs, full help).

**Do not use when.** stdout is not a terminal, or the user set `--no-pager`
or `PAGER=cat`.

**Example.** `git diff` pages on a terminal and prints directly into a pipe.

**Cost removed.** Output scrolling off screen.

**Verify.** `CMD | cat` never starts a pager.

[clig]: https://clig.dev/
