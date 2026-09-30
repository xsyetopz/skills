# Robustness, signals, configuration, and distribution

How a command behaves under bad input, slow work, interruption, and
different environments. Guidance adapted from the
[Command Line Interface Guidelines][clig] (CC BY-SA 4.0), sections
Robustness, Signals, Configuration, Environment variables, Distribution,
and Analytics.

## Contents

- [Validate early](#validate-early)
- [Responsive before fast; progress for long work][toc-1]
- [Timeouts and recoverable runs](#timeouts-and-recoverable-runs)
- [Ctrl-C and crash-only design](#ctrl-c-and-crash-only-design)
- [Configuration precedence](#configuration-precedence)
- [Where configuration lives](#where-configuration-lives)
- [Environment variables](#environment-variables)
- [Distribution and uninstall](#distribution-and-uninstall)
- [Analytics only with consent](#analytics-only-with-consent)

[toc-1]: #responsive-before-fast-progress-for-long-work

## Validate early

**Definition.** Check all user input (arguments, flags, config values,
files) before doing any work, and stop with an explanation on the first
problem.

**Use when.** Every command that changes state or runs long.

**Do not use when.** Validation needs the result of the work itself; then
validate each step before its side effect.

**Example.** A migration command checks that the target database URL
parses and the migration directory exists before opening a connection.

**Cost removed.** Half-applied changes after a late failure.

**Verify.** Pass one invalid value; the command exits non-zero and nothing
changed.

## Responsive before fast; progress for long work

**Definition.** Print something within about 100 ms, before any network
request. For long work, show progress (a spinner, a bar with an estimate)
on stderr and only on a terminal. When work fails behind a progress bar,
print the hidden logs. Parallel progress needs a library that keeps lines
from interleaving (tqdm, schollz/progressbar).

**Use when.** Any step that can take more than about a second.

**Do not use when.** stderr is not a terminal: print occasional plain lines
instead of animation, so CI logs stay readable.

**Example.** `docker pull` shows one progress line per layer.

**Cost removed.** Users killing a working command because it looked hung.

**Verify.** `CMD 2>&1 | cat` contains no carriage-return animation frames;
on a terminal the first output appears before the slow step.

## Timeouts and recoverable runs

**Definition.** Every network call has a default timeout and a flag or
setting to change it. After a transient failure, running the same command
again continues where it stopped (idempotent steps, resumable downloads).

**Use when.** Network or other I/O that can stall.

**Do not use when.** Never skip; a missing timeout means a possible hang
forever.

**Example.** `fetch --timeout 30s`; a re-run skips files whose checksums
already match.

**Cost removed.** Hung CI jobs; re-doing an hour of work after a dropped
connection.

**Verify.** Point the command at a non-routable address (`10.255.255.1`);
it fails within the timeout with a clear message.

## Ctrl-C and crash-only design

**Definition.** On SIGINT, say something at once, then exit quickly; give
cleanup a time limit. A second Ctrl-C skips cleanup, and the first message
says so if that is destructive. Design so that a run can start after one
that never cleaned up (crash-only): write to a temporary file and rename
it, keep state that the next run can repair.

**Use when.** Commands that write files, hold locks, or start child
processes.

**Do not use when.** A wrapper where Ctrl-C belongs to the child (ssh,
tmux); document the escape key instead.

**Example.** `docker-compose up` prints
`Gracefully stopping... (press Ctrl+C again to force)`. `todo.py` writes to
`tasks.tmp` and renames it over `tasks.json`, so an interrupted save never
leaves half a file, and it exits 130 on `KeyboardInterrupt`.

**Cost removed.** Corrupt state and commands that ignore Ctrl-C.

**Verify.** Send SIGINT mid-run with GNU `timeout -s INT 1 CMD ...` (on macOS,
`brew install coreutils` provides it as `gtimeout`), then run
again; the second run succeeds and the exit status of the first is 130.

## Configuration precedence

**Definition.** From highest to lowest: flags, the shell's environment
variables, project configuration (for example `.env` or a project file),
user configuration, system configuration.

**Use when.** A setting can come from more than one place.

**Do not use when.** Adding more layers than the setting needs; a
per-invocation setting is a flag only.

**Example.** `todo.py`: `--store` beats `TODO_STORE`, which beats
`$XDG_DATA_HOME/todo/tasks.json`. `verify.sh` checks the first two.

**Cost removed.** Surprise about which value applied.

**Verify.** Set the same key at two levels with different values; the
higher level wins, and `--debug` or a `config show` command reports the
source.

## Where configuration lives

**Definition.** Choose by stability: values that vary per invocation are
flags; per-machine or per-user values are flags plus environment variables
(or a user config file under `$XDG_CONFIG_HOME`, default `~/.config`);
values shared by a project belong in a version-controlled project file.
Follow the [XDG Base Directory Specification][xdg] for config, data, and
cache paths. If you must change configuration owned by another program,
ask first, say exactly what you change, prefer a new file (`/etc/cron.d/app`)
over editing a shared one, and mark your lines with a dated comment.

**Use when.** Adding any setting or file the tool writes.

**Do not use when.** A platform convention differs (macOS
`~/Library/Application Support`, Windows `%APPDATA%`) and the project
already follows it; stay consistent with the project.

**Example.** `todo.py` stores data in `$XDG_DATA_HOME/todo/` (default
`~/.local/share/todo/`).

**Cost removed.** Dotfile clutter in `$HOME` and silent edits to other
tools' files.

**Verify.** Run with `XDG_CONFIG_HOME` and `XDG_DATA_HOME` set to a
temporary directory; nothing is written outside it.

## Environment variables

**Definition.** Environment variables hold settings that vary with the
context the command runs in. Names use only uppercase letters, digits, and
underscores, and do not start with a digit; values stay on one line. Do not
take names POSIX or common tools already use. Honor the general ones where
relevant: `NO_COLOR`, `FORCE_COLOR`, `DEBUG`, `EDITOR`, `HTTP_PROXY`,
`HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`, `SHELL`, `TERM`, `TMPDIR`, `HOME`,
`PAGER`, `LINES`, `COLUMNS`. Reading `.env` in the project directory is
fine for per-project values, but `.env` is no substitute for a real,
version-controlled config file (strings only, often untracked, often full
of secrets).

**Use when.** Adding a setting that differs between shells, machines, or CI.

**Do not use when.** The value is a secret (see [secrets][secrets]).

**Example.** `TODO_STORE` names an alternative task file; the app prefix
avoids collisions.

**Cost removed.** Collisions with other tools' variables; multi-line values
that break `env`.

**Verify.** `rg -n 'getenv|environ|process\.env|env::var' src/` lists
every variable, and each appears in the docs.

## Distribution and uninstall

**Definition.** Ship a single executable where the language allows it, or
use the platform's package manager, and document uninstalling next to
installing.

**Use when.** Publishing a tool for people outside the project.

**Do not use when.** The tool is language-specific (a Python linter); users
already have the runtime, so a normal package is fine.

**Example.** Go and Rust binaries; PyInstaller for Python applications.

**Cost removed.** Files scattered on disk that nobody can remove.

**Verify.** Install and uninstall on a clean machine or container; no files
remain.

## Analytics only with consent

**Definition.** Do not send usage or crash data without consent. Prefer
opt-in. If opt-out, say so on first run and in the docs, and make disabling
it one command or variable. Document what is collected, why, how it is
anonymized, and how long it is kept. Alternatives: instrument web docs and
downloads, and ask users.

**Use when.** Any telemetry, crash reporting, or update ping.

**Do not use when.** Never send data silently.

**Example.** Homebrew documents its analytics and how to disable them;
Next.js announces telemetry and documents opting out.

**Cost removed.** Loss of user trust; blocked corporate installs.

**Verify.** With networking monitored and analytics not enabled, the
command makes no request to the analytics endpoint.

[clig]: https://clig.dev/
[xdg]: https://specifications.freedesktop.org/basedir-spec/latest/
[secrets]: arguments-and-flags.md#secrets-never-in-flags-or-environment-variables
