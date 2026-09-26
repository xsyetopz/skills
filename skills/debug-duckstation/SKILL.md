---
name: debug-duckstation
description: >-
  Runs and debugs official DuckStation (PS1 emulator) releases with isolated
  data, logs, the CPU debugger, and crash capture. Use for DuckStation crashes
  or rendering and save-state problems. Not for building it from source,
  PCSX2, or obtaining BIOS or games.
---

# Run and Debug DuckStation Releases

Run an official DuckStation release in a throwaway portable copy, collect
evidence (log file, debugger state, crash report), and decide whether a
symptom belongs to the host process, the inputs, the renderer, or the
PlayStation guest program. This skill does not build DuckStation: its
licence (CC-BY-NC-ND-4.0 plus a packaging restriction on build files) and
the repository's `CLAUDE.md` ask AI assistants not to build or modify it.

## Workflow

1. Read the [licence card][licence-card]. If the request is to build,
   patch, or package DuckStation, answer with that card's response and
   stop.
1. Pick a numbered release tag, download the asset for the host, and
   record tag, asset name, SHA-256 digest, and the `-version` string
   ([pinned release][pinned-release]).
1. Copy the app into a scratch directory and create `portable.txt` next
   to the executable (`Contents/MacOS` on macOS). Record the modification
   time of the default user directory
   ([portable](references/isolation-and-launch.md#portable-user-directory)).
1. Capture `-help` from that binary (it prints to stderr and exits 1).
   Use only flags it lists, and build launch lines with
   `scripts/build_command.py --help-file`.
1. `settings.ini` does not exist until the first launch, so do one bounded
   warm-up run on a dummy boot file (`-batch -nogui -- dummy.exe`, about
   12 s), stop the process, then enable file logging in `settings.ini` and
   validate the edit with `scripts/check_formats.py settings`.
1. Launch with a hard time limit
   ([bounded run](references/isolation-and-launch.md#bounded-batch-run)).
   Exit status and "still running" are not boot evidence; quote log
   lines.
1. Classify the symptom with the
   [layer triage](references/guest-vs-emulator.md#layer-triage) table and
   open the card for the owning layer.
1. Change one variable per run (renderer, one setting, one release), keep
   everything else copied from the baseline, and compare the same
   checkpoint.
1. Before finishing, check the default user directory's modification
   time again and list what the runs left behind.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| "Build / compile / package DuckStation", CMake, dependencies | [Licence and AI policy](references/licence-and-releases.md#licence-and-ai-assistant-policy) |
| Which binary to test; reproducible identity | [Pinned release](references/licence-and-releases.md#pinned-official-release) |
| Worked in an older release, broken now | [Release comparison](references/licence-and-releases.md#regression-comparison-across-official-releases) |
| Keep the user's saves and settings untouched | [Portable directory](references/isolation-and-launch.md#portable-user-directory) |
| Where a user's log or settings live | [Default directories](references/isolation-and-launch.md#default-user-directories) |
| Change a setting from a script | [Settings edit](references/isolation-and-launch.md#settings-changes-by-file-edit) |
| Boot a disc image or homebrew EXE from a shell | [Launch flags](references/isolation-and-launch.md#command-line-launch-flags) |
| `-state`, `-resume`, `-statefile` | [Save-state flags](references/isolation-and-launch.md#save-state-launch-flags) |
| Unattended run, CI smoke check, hang | [Bounded run](references/isolation-and-launch.md#bounded-batch-run) |
| Generate a quoted launch line | [Command builder](references/isolation-and-launch.md#launch-command-builder) |
| Need a log for a report | [Log to file](references/logging-and-debugging.md#log-to-file) |
| Process dies before the log starts | [Console logging](references/logging-and-debugging.md#console-logging-and-early-console) |
| Step guest code, breakpoints | [CPU debugger](references/logging-and-debugging.md#cpu-debugger-window) |
| Scripted guest debugging with an ELF | [GDB server](references/logging-and-debugging.md#gdb-server) |
| Emulator process hangs | [lldb attach](references/logging-and-debugging.md#lldb-attach-to-a-running-release) |
| Emulator process crashes on launch | [lldb launch](references/logging-and-debugging.md#lldb-launch-of-a-release) |
| Exit status 134/139, `.ips` report | [Crash report](references/logging-and-debugging.md#macos-crash-report) |
| "Is it DuckStation or the game?" | [Layer triage](references/guest-vs-emulator.md#layer-triage) |
| Graphics glitch | [Software renderer](references/guest-vs-emulator.md#software-renderer-as-an-oracle) |
| Only one game misbehaves | [Per-game settings](references/guest-vs-emulator.md#per-game-settings-file) |
| Comparing runs with save states | [Save states](references/guest-vs-emulator.md#save-states-are-not-a-regression-oracle) |
| Dump textures | [Texture dumping](references/textures-patches-cheats.md#texture-dumping) |
| Replace textures, aliases | [Replacement](references/textures-patches-cheats.md#texture-replacement-and-aliases) |
| Textures dump as duplicates or not at all | [Texture options](references/textures-patches-cheats.md#per-game-texture-options) |
| Cheats, patches, `.cht` files | [Patches and cheats](references/textures-patches-cheats.md#patches-and-cheats-file) |

## Rules

- Do not clone, read, build, or modify DuckStation source or build files,
  and do not write build recipes. Point users to the upstream README's
  "Building" section and the releases page.
- Never download, generate, or share BIOS images or commercial game
  images. Guest runs use only a BIOS and media the user dumped and
  supplied, or homebrew whose licence allows the use. Without them, mark
  guest steps "Not runnable here".
- Every run uses a portable copy. Never launch the user's installed app
  for an experiment, and never attach a debugger to a process you did not
  start.
- Use only flags listed by the tested binary's `-help`. There is no
  `-portable`, `-datapath`, or headless flag in 0.1-11826.
- Edit `settings.ini` only while DuckStation is stopped, and use only keys
  and values the same release wrote. For an unknown value, set it once in
  the UI and copy the changed line.
- Bound every unattended run with an external timeout. Record SIGKILL as
  forced termination, not as a clean exit.
- Do not use save states across releases or as proof of a fix.
- Disable cheats, patches, texture replacements, and enhancements before
  attributing a symptom to the emulator core.
- Name the release tag and digest in every claim; `latest` and `preview`
  move.

## Bundled tools

- `scripts/build_command.py`: prints a launch argv (JSON or POSIX) and
  never runs it; `--help-file` rejects flags missing from `-help`.
- `scripts/check_formats.py settings|cht|texture-name`: checks
  `settings.ini` keys against `assets/examples/settings/keys-0.1-11826.txt`,
  chtdb `.cht` syntax, and wiki texture file names; exit 1 on findings.
- `assets/examples/verify.sh`: offline script tests and fixtures.
  `verify.sh release` (macOS, opt-in) downloads the 91 MB v0.1-11826 zip,
  checks its digest and `-help`, runs it in portable mode for about 30 s,
  checks first-run keys against the bundled list, attaches lldb, and
  checks that the default user directory is unchanged.

## References

- [Licence and releases](references/licence-and-releases.md): licence
  and AI-assistant policy, pinned release, release-range comparison.
- [Isolation and launch](references/isolation-and-launch.md): portable
  and default directories, settings edits, flags, state flags, bounded
  runs, command builder.
- [Logging and debugging](references/logging-and-debugging.md): file
  and console logs, CPU debugger, GDB server, lldb attach and launch,
  macOS crash reports.
- [Emulator or guest](references/guest-vs-emulator.md): layer triage,
  software renderer, per-game settings, save-state limits.
- [Textures, patches, cheats](references/textures-patches-cheats.md):
  dumping, replacement and aliases, texture options, `.cht` files.

## Completion evidence

The report contains:

- release tag, asset name, SHA-256 digest, and `-version` output;
- the portable directory path, and the default user directory's
  modification time before and after;
- each command run with its time limit, how it ended (exit status or
  forced), and the log lines used as evidence;
- the owning layer from the triage table and the one variable changed
  per comparison;
- for crashes, the `.ips` file name, signal, and top symbolicated frames;
- each step marked Executed, or Not runnable here with the reason (for
  example "no BIOS available").

[licence-card]:
references/licence-and-releases.md#licence-and-ai-assistant-policy
[pinned-release]: references/licence-and-releases.md#pinned-official-release
