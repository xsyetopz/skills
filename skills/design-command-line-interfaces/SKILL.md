---
name: design-command-line-interfaces
description: >-
  Designs, reviews, and changes an application's command-line interface:
  subcommands, flags and arguments, help text, stdout and stderr, exit codes,
  errors, prompts, color, `--json` output, config and environment variables,
  and renaming or deprecating commands without breaking scripts. Probes a
  built CLI with a bundled checker. Use when adding, editing, renaming, or
  reviewing CLI commands. Not for justfile recipes or full-screen TUIs.
---

# Design Command-Line Interfaces

Make every command usable by a person at a terminal and by a script in a
pipe, and change existing commands without breaking either. The cards adapt
the [Command Line Interface Guidelines](https://clig.dev/) (CC BY-SA 4.0)
and the POSIX utility conventions. `assets/examples/todo.py` implements
them, `assets/examples/todo_bad.py` is the baseline, and
`assets/examples/verify.sh` checks both.

## Workflow

1. Find the CLI's entry point and parser (`argparse`, Click, Typer, Cobra,
   clap, picocli, oclif, commander). Extend that parser; never add a second
   one or hand-parse `argv`.
1. Record the current interface before editing: `CMD --help` and each
   `CMD SUB --help`, environment variables read, exit codes, and
   machine-readable formats
   ([inventory][inventory]).
   Find callers of what you will change: tests, docs, completions, CI
   scripts, `rg -n 'CMD SUB'`.
1. Run the checker on the current build to get a baseline:
   `python3 scripts/check_cli.py --sub SUB ... -- CMD`.
1. Classify the task and follow its cards:
   - New command or flag: [arguments](references/arguments-and-flags.md),
     [output](references/output-and-exit-codes.md),
     [help](references/help-and-errors.md).
   - Rename, removal, or behavior change: [evolution][evolution] first.
   - Review: every row of the routing table.
1. Implement with the project's existing parser, error type, and output
   helpers. Add tests next to the existing CLI tests that assert streams,
   exit codes, and the non-terminal path.
1. Verify: rerun the checker (no new findings), run the tests, diff the new
   help output against the recorded one, and run each changed command with
   stdin from `/dev/null` and stdout piped.
1. Report the interface changes (added, renamed, deprecated, removed), the
   checker output before and after, and the commands run.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| Hand-parsed `argv`, choosing a parser | [Parse with a library](references/output-and-exit-codes.md#parse-with-a-library) |
| Failure exits 0, choosing exit codes | [Exit codes](references/output-and-exit-codes.md#exit-codes) |
| Status text breaks `CMD \| jq`, errors lost in `> file` | [stdout and stderr](references/output-and-exit-codes.md#data-on-stdout-messages-on-stderr) |
| Escape codes or spinners in logs and CI | [Terminal detection](references/output-and-exit-codes.md#terminal-detection), [Color](references/output-and-exit-codes.md#color) |
| Scripts scrape tables | [`--json` and `--plain`](references/output-and-exit-codes.md#machine-readable-output---json-and---plain) |
| Silent success, too much output | [Success output and --quiet](references/output-and-exit-codes.md#success-output-and---quiet), [State changes](references/output-and-exit-codes.md#report-state-changes-and-next-commands) |
| Long output scrolls away | [Pager](references/output-and-exit-codes.md#pager-for-long-output) |
| `-h` missing or runs the command | [Help flags](references/help-and-errors.md#help-flags-at-every-level) |
| Bare command hangs or dumps every flag | [Concise usage](references/help-and-errors.md#concise-usage-when-run-bare), [Terminal stdin](references/help-and-errors.md#waiting-on-a-terminal-stdin) |
| Writing or reordering `--help` | [Help text layout](references/help-and-errors.md#help-text-layout), [Documentation](references/help-and-errors.md#documentation-outside-the-help-text) |
| Typo in a command name | [Suggest corrections](references/help-and-errors.md#suggest-corrections-do-not-run-them) |
| Error messages, stack traces | [Expected errors](references/help-and-errors.md#rewrite-expected-errors-for-people), [Unexpected errors](references/help-and-errors.md#unexpected-errors-and-bug-reports) |
| Adding an input | [Flags over arguments](references/arguments-and-flags.md#flags-over-positional-arguments), [Long and short names](references/arguments-and-flags.md#long-names-for-every-flag-short-names-for-common-ones), [Standard names](references/arguments-and-flags.md#standard-flag-names) |
| Flag ignored after the subcommand | [Flag position](references/arguments-and-flags.md#flags-that-work-before-and-after-the-subcommand) |
| File input or output, operands starting with `-` | [`-` and `--`](references/arguments-and-flags.md#--for-stdin-and-stdout----to-end-options), [Optional values](references/arguments-and-flags.md#optional-values-need-a-keyword) |
| `--password`, tokens in env | [Secrets](references/arguments-and-flags.md#secrets-never-in-flags-or-environment-variables) |
| Prompts, CI hangs, deletes | [Prompts and --no-input](references/arguments-and-flags.md#prompts-only-on-a-terminal-and---no-input), [Confirmation](references/arguments-and-flags.md#confirmation-scaled-to-danger) |
| Adding or grouping subcommands | [Structure](references/subcommands-and-evolution.md#consistent-subcommand-structure), [Ambiguous names](references/subcommands-and-evolution.md#no-ambiguous-or-near-duplicate-names), [Catch-all](references/subcommands-and-evolution.md#no-catch-all-subcommand-no-implicit-abbreviations) |
| Naming a program or command | [Naming](references/subcommands-and-evolution.md#naming-the-program-and-its-commands) |
| Renaming a command, flag, or env var | [Renaming][evolution] |
| Changing defaults, removing flags or output fields | [Additive changes](references/subcommands-and-evolution.md#additive-changes), [Removing](references/subcommands-and-evolution.md#removing-or-changing-behavior), [Output stability](references/subcommands-and-evolution.md#human-output-may-change-script-output-may-not) |
| Update checks, phone-home calls | [Time bombs](references/subcommands-and-evolution.md#no-time-bombs), [Analytics](references/robustness-and-configuration.md#analytics-only-with-consent) |
| Late failures, slow or hung commands | [Validate early](references/robustness-and-configuration.md#validate-early), [Progress](references/robustness-and-configuration.md#responsive-before-fast-progress-for-long-work), [Timeouts](references/robustness-and-configuration.md#timeouts-and-recoverable-runs) |
| Ctrl-C ignored, corrupt state after interrupt | [Ctrl-C and crash-only](references/robustness-and-configuration.md#ctrl-c-and-crash-only-design) |
| Settings from flags, env, and files | [Precedence](references/robustness-and-configuration.md#configuration-precedence), [Where config lives](references/robustness-and-configuration.md#where-configuration-lives), [Environment variables](references/robustness-and-configuration.md#environment-variables) |
| Packaging the tool | [Distribution](references/robustness-and-configuration.md#distribution-and-uninstall) |

## Rules

- Primary output and anything machine-readable go to stdout; everything
  else goes to stderr. A pipe carries only stdout, so a status line on
  stdout corrupts the next program's input.
- A failure exits non-zero. Scripts, CI, and `set -e` see nothing else.
- Never require a prompt. Without a terminal on stdin, or with `--no-input`,
  fail at once and name the flag that supplies the value; a prompt in CI
  hangs until the job times out.
- Color, animation, and pagers only on a terminal, and never with
  `NO_COLOR` set or `TERM=dumb`; escape codes corrupt logs and `grep`.
- A shipped name is an interface. Renames keep the old name as a hidden,
  warned alias until a documented major version, because user scripts
  cannot be updated in the same commit as the tool.
- A flag the parser accepts must take effect wherever the user puts it; an
  accepted but ignored flag is worse than an error. Test both positions.
- No secrets in flag values (visible in `ps` and shell history) or in
  environment variables (inherited by children, shown by `docker inspect`).
- Do not auto-run a guessed correction; suggest it. Invalid input may be a
  logic error, and each accepted misspelling becomes permanent syntax.
- `--json`, `--plain`, exit codes, and documented formats are stable; the
  default human output may change. Say so in the docs.
- Follow the project's existing conventions where they conflict with a card,
  and report the conflict instead of changing shipped behavior silently.

## Bundled tools

- `scripts/check_cli.py [--sub SUB]... [--skip ID]... [--timeout S]
  [--json] [--strict] -- COMMAND [ARG...]`: runs the command with pipes
  and checks `--help`, `-h`, `SUB --help`, an unknown flag (non-zero,
  stderr only), stack traces, `--version`, ANSI escapes in pipes, and that
  a bare run finishes with stdin from `/dev/null` and on a pseudo-terminal.
  Exit 0 clean, 1 errors (or warnings with `--strict`), 2 bad usage. It
  starts the command, so point it only at code you trust; `--skip ID`
  documents deliberate exceptions.
- `assets/examples/todo.py` (candidate), `assets/examples/todo_bad.py`
  (baseline), `assets/examples/verify.sh`: `sh assets/examples/verify.sh`
  prints `VERIFY PASSED` (Python 3.14.7, macOS).

## References

- [Output and exit codes](references/output-and-exit-codes.md): parser,
  exit codes, streams, TTY, color, --json and --plain, --quiet, pager.
- [Help and errors](references/help-and-errors.md): help flags, bare usage,
  help layout, suggestions, docs, error messages, bug reports.
- [Arguments and flags](references/arguments-and-flags.md): flags versus
  arguments, names, flag position, `-` and `--`, secrets, prompts,
  confirmation.
- [Subcommands and evolution](references/subcommands-and-evolution.md):
  inventory, structure, naming, additive changes, renames, deprecation,
  output stability.
- [Robustness and configuration](references/robustness-and-configuration.md):
  validation, progress, timeouts, signals, config precedence, XDG,
  environment variables, distribution, analytics.

## Completion evidence

The report lists the interface changes; `check_cli.py` output before and
after; the tests run and their result; the help diff; and any card not
applied, with the reason.

[evolution]: references/subcommands-and-evolution.md#renaming-a-command-or-flag
[inventory]: references/subcommands-and-evolution.md#inventory-the-interface-before-changing-it
