# Help, documentation, and errors

How a command teaches its own use and explains failure. Guidance adapted
from the [Command Line Interface Guidelines][clig] (CC BY-SA 4.0), sections
Help, Documentation, and Errors. Runnable examples are in
[`assets/examples/todo.py`](../assets/examples/todo.py).

## Contents

- [Help flags at every level](#help-flags-at-every-level)
- [Concise usage when run bare](#concise-usage-when-run-bare)
- [Help text layout](#help-text-layout)
- [Suggest corrections, do not run them](#suggest-corrections-do-not-run-them)
- [Waiting on a terminal stdin](#waiting-on-a-terminal-stdin)
- [Documentation outside the help text](#documentation-outside-the-help-text)
- [Rewrite expected errors for people](#rewrite-expected-errors-for-people)
- [Unexpected errors and bug reports](#unexpected-errors-and-bug-reports)

## Help flags at every level

**Definition.** `-h` and `--help` print full help to stdout and exit 0, at
the top level and for each subcommand. Adding `-h` anywhere in a command
line shows help instead of running it. `-h` means nothing else. Git-like
tools also accept `CMD help SUB`.

**Use when.** Every command and subcommand.

**Do not use when.** Never reuse `-h` for another flag (`--host`, `--human`);
users type it expecting help.

**Example.** `todo --help`, `todo -h`, `todo remove --help`.

**Cost removed.** Users running a command to learn about it and triggering
the action instead.

**Verify.** `check_cli.py --sub SUB ... -- CMD` reports no `help-long`,
`help-short`, or `sub-help` finding.

## Concise usage when run bare

**Definition.** A command that needs arguments, run without them, prints a
short usage (what it does, one or two examples, and "run `CMD --help`") and
exits non-zero.

**Use when.** The command cannot do anything useful without arguments.

**Do not use when.** The program is interactive by design (`npm init`);
then it prompts when stdin is a terminal, and still fails fast without one.

**Example.** `todo` prints `usage: todo …` and
`Run todo --help for commands and examples.` to stderr, exit 2.

**Cost removed.** A bare command that hangs waiting for input, or a wall of
flags that hides what the tool is for.

**Verify.** `check_cli.py` reports no `bare-noninteractive` or
`bare-terminal` finding.

## Help text layout

**Definition.** Order: one-line description, usage, the most common
commands and flags, examples, then a docs link and where to report issues.
Lead with examples; people copy examples before they read flag lists. Use
bold or headings only when the output is a terminal.

**Use when.** Writing or restructuring any `--help`.

**Do not use when.** Examples would make help very long: move the full set
to a docs page or an `examples` subcommand and keep two or three in help.

**Example.** `todo --help` ends with an `examples:` block that shows piping
into `todo add -` and `todo list --json | jq`, then the docs URL. `git`
groups subcommands by task ("start a working area", "work on the current
change").

**Cost removed.** Users searching the web for the invocation the help could
have shown.

**Verify.** `CMD --help | head -20` shows the purpose, usage, and at least
one example.

## Suggest corrections, do not run them

**Definition.** On an unknown command or flag close to a known one, say
what the user may have meant. Ask before running it, or just print it.

**Use when.** Typos in subcommand and flag names.

**Do not use when.** Silently running the guess. Invalid input may be a
logic error, and each accepted misspelling becomes syntax you must keep
supporting.

**Example.** `brew update jq` tells the user to run `brew upgrade jq`.
Cobra's `SuggestFor` field and clap's built-in suggestions do this.

**Cost removed.** A dead-end "unknown command" with no next step.

**Verify.** Run a one-letter typo of a subcommand; the error names the
right one and exits non-zero.

## Waiting on a terminal stdin

**Definition.** A command that reads input from a pipe, run with stdin on a
terminal and no input arguments, prints usage (or a stderr note that it is
reading stdin) instead of waiting silently.

**Use when.** Filters and commands that accept `-` or piped data.

**Do not use when.** Reading stdin interactively is the documented mode.

**Example.** `cat` with no arguments waits silently; a tool following this
rule prints `reading from stdin; press Ctrl-D to end, or see CMD --help`.

**Cost removed.** Users thinking the tool is frozen.

**Verify.** `check_cli.py` `bare-terminal` probe (runs the command on a
pseudo-terminal).

## Documentation outside the help text

**Definition.** Web documentation (searchable, linkable) plus terminal
documentation that matches the installed version: man pages, or a
`help` subcommand that shows them (`npm help ls` equals `man npm-ls`).
Link the matching web page from help.

**Use when.** The tool has more behavior than fits in `--help`.

**Do not use when.** Duplicating the same text by hand in three places;
generate man pages and web docs from one source (parser metadata or a tool
such as ronn).

**Example.** `todo --help` ends with `docs: https://example.com/todo/docs`.

**Cost removed.** Docs that describe another version than the one installed.

**Verify.** Every flag in `--help` appears in the docs, and the docs list
no flag that `--help` lacks.

## Rewrite expected errors for people

**Definition.** Catch errors you can predict and rewrite them as: what
failed, why, and what to do next. Put the most important line last, where
the eye lands. Group many errors of one kind under one heading.

**Use when.** File not found, permission denied, invalid config, network
unreachable, missing credentials, and every validation failure.

**Do not use when.** Hiding the original cause: keep the underlying message
(`strerror`, HTTP status) in the rewritten text.

**Example.** `todo: no task with id 99; run todo list to see ids`, exit 1.
Source example: "Can't write to file.txt. You might need to make it
writable by running `chmod +w file.txt`."

**Cost removed.** A trip to the docs or the source for every error.

**Verify.** Trigger each expected failure; each message names the object
and a next step, and `check_cli.py` reports no `stack-trace`.

## Unexpected errors and bug reports

**Definition.** For a failure you did not anticipate, print a one-line
summary, write the debug detail or traceback to a log file (or show it with
`--debug`/`--verbose`), and say where to report the bug, ideally with a URL
that pre-fills version and platform.

**Use when.** Top-level exception handlers.

**Do not use when.** Expected errors: those get the rewritten form above,
not a bug-report prompt.

**Example.** `main` in `todo.py` prints expected failures (`RuntimeError`,
`OSError`) as one line. Any other exception writes its traceback to a
`todo-crash-*.log` temporary file and prints that path, the version, and the
issue tracker URL.

**Cost removed.** Stack traces that scare users and bury the one useful
line; bug reports without version information.

**Verify.** Force an internal error (for example, make a code path raise
`ValueError`); the terminal shows two lines, and the log file holds the
traceback.

[clig]: https://clig.dev/
