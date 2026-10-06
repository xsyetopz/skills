---
name: design-cli-interface
description: >-
  Designs and fixes command-line tools, including flags, subcommands, help text,
  exit codes, stdout vs stderr, JSON output, CI prompts that hang, and NO_COLOR.
  Use when adding or renaming a CLI command or flag, or when piping its output to jq breaks.
  Not for just recipes, TUIs, or CLI startup speed.
---

# Design CLI Interface

Make every command usable by a person at a terminal and by a script in a pipe, and change shipped
commands without breaking either. The rules adapt the [Command Line Interface
Guidelines](https://clig.dev/) (CC BY-SA 4.0) and the [POSIX utility conventions][posix].

## Rules

- Extend the project's existing parser (`argparse`, Click, Cobra, clap, picocli, oclif, commander).
  Do not add a second one or hand-parse `argv`, because two parsers give two help and error formats.
- Record the interface before editing: `CMD --help`, each `CMD SUB --help`, env vars read
  (`rg -n 'getenv|environ|env::var|process\.env'`), exit codes, and callers (`rg -n 'CMD SUB'` in
  tests, docs, completions, CI). Diff the help afterwards so every change is intended.
- Primary and machine-readable output go to stdout; status, progress, warnings, errors, and prompts
  go to stderr. Help the user asked for goes to stdout; usage shown because of an error goes to
  stderr. A pipe carries only stdout, so a status line there corrupts `CMD | jq`.
- A failure exits non-zero. An unknown flag exiting 0 is the most common defect. Use few documented
  codes: 0 success, 1 runtime failure, 2 usage error (argparse and Click), 130 after Ctrl-C (128 +
  SIGINT).
- Never make a prompt the only way to supply a value. Without a terminal on stdin, or with
  `--no-input`, fail at once and name the flag that supplies it. Check with `CMD ARGS </dev/null`
  (cmd.exe: `CMD ARGS <NUL`). A prompt in CI hangs until timeout.
- Scale confirmation to danger: no prompt for a mild action, prompt plus `--force` and `--dry-run`
  for a remote or bulk delete, and type-the-name plus `--confirm=NAME` for deleting an application
  or database. Lowering a count that deletes the surplus is also destructive.
- Color, spinners, and pagers only when that stream is a terminal, and never with `NO_COLOR`
  non-empty ([no-color.org](https://no-color.org/)), `TERM=dumb`, or `--no-color`. Test each stream
  separately, since stderr can be a terminal while stdout is piped. Escape codes corrupt logs.
- A flag the parser accepts must take effect on either side of the subcommand (`CMD --store x add`
  and `CMD add --store x`). Test both; an accepted but ignored flag is worse than an error. Parser
  traps are in [parser gotchas](references/parser-gotchas.md).
- Do not put secrets in flag values (visible in `ps` and shell history) or env vars (inherited by
  children, shown by `docker inspect`). Accept `--password-file PATH`, stdin, or a keychain.
- A shipped name is an interface: flags, subcommands, env vars, config keys, exit codes, and
  `--json` fields. Keep a renamed one as a hidden alias that warns on stderr, naming the replacement
  and the removal version, until a documented major release. If the project or maintainer allows
  breaking changes (pre-1.0, no compatibility promise), rename directly and list old and new names
  in the changelog instead. Never skip the same-change updates: help, docs, completions, tests,
  every in-repo caller.
- `--json`, `--plain`, exit codes, and documented formats are stable; default human output may
  change. Adding a column to a table is fine, renaming a JSON key is breaking. Say so in the docs,
  and keep `--json` output identical on and off a terminal.
- Use the standard flag meanings: `-h/--help` (nothing else), `-q/--quiet`, `-f/--force`,
  `-n/--dry-run`, `-o/--output`, `-a/--all`, `--json`, `--no-input`, `--version`. Avoid `-v` in a
  new tool (verbose in some tools, version in others). Give every flag a long name; give only
  frequently typed flags a short one.
- Prefer flags over positional arguments, except one primary object or a list of the same kind
  (`rm a b c`). Accept `-` for stdin or stdout and `--` to end options; test `CMD -- -x` rather than
  reimplementing it.
- Suggest a correction for a mistyped command; do not run it. Do not add a catch-all default
  subcommand or accept unambiguous prefixes as aliases, because a later subcommand would break
  scripts.
- Rewrite predictable errors as what failed, why, and what to do next, with the underlying cause
  (`strerror`, HTTP status) kept and the most important line last. For unexpected errors print one
  line, write the traceback to a log file or `--debug`, and say where to report. No stack trace by
  default.
- Validate all input before any side effect. Give every network call a timeout flag. On SIGINT print
  a message at once and exit quickly; write files to a temporary name then rename so an interrupt
  leaves no half file.
- Precedence from highest to lowest: flags, environment, project config, user config, system config.
  Put user config and data under `$XDG_CONFIG_HOME` and `$XDG_DATA_HOME` on Linux
  ([spec](https://specifications.freedesktop.org/basedir-spec/latest/)), and in the platform
  directory elsewhere (`%APPDATA%` on Windows, via platformdirs or dirs), unless the project already
  chose one. Env names are uppercase letters, digits, and underscores, with an app prefix.
- Follow the project's conventions where they conflict with a rule, and report the conflict rather
  than changing shipped behavior silently.

## Workflow

1. Record the interface and run the checker for a baseline (below).
1. Implement with the project's parser, error type, and output helpers. Add tests beside the
   existing CLI tests that assert streams, exit codes, and the non-terminal path.
1. Rerun the checker (no new findings), the tests, the help diff, and each changed command with
   stdin from `/dev/null` (`NUL` on Windows) and stdout piped.

## Scripts

- `python3 scripts/check_cli.py [--sub SUB]... [--skip ID]... [--timeout S] [--json] [--strict] --
  COMMAND [ARG...]` runs the command with pipes and checks `--help`, `-h`, `SUB --help`, an unknown
  flag (non-zero, stderr only), stack traces, `--version`, ANSI escapes in pipes, and that a bare
  run finishes with stdin from `/dev/null` and on a pseudo-terminal. Exit 0 clean, 1 errors (or
  warnings with `--strict`), 2 bad usage. It starts the command, so point it only at code you trust;
  `--skip ID` documents a deliberate exception. `scripts/test_check_cli.py` tests it. On Windows,
  use `py -3` for `python3`.

## References

- Read [parser gotchas](references/parser-gotchas.md) when a flag is ignored after the subcommand,
  or when adding aliases, deprecations, or hidden commands in `argparse`, Cobra, or clap.

[posix]: https://pubs.opengroup.org/onlinepubs/9699919799/basedefs/V1_chap12.html
