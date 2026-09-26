---
name: build-and-debug-pcsx2
description: >-
  Builds PCSX2 (PS2 emulator) at a pinned commit and debugs it and its games
  with isolated data, logs, breakpoints, and bisection. Use for PCSX2 build
  failures, crashes, or rendering bugs. Not for DuckStation or obtaining BIOS
  or games.
---

# Build and Debug PCSX2

Build PCSX2 from an exact commit, or take an official release. Run it
against a throwaway data root with a file log, and decide which layer owns
a failure (build, setup, guest, renderer, or host) before changing
anything. The cards are pinned to PCSX2 commit `2c804670` (`v2.9.84`) and
the official `v2.8.2` macOS release ([sources](references/sources.md)).

## Workflow

1. Read [upstream policy][policy] first when the task touches PCSX2
   source or GitHub. Agents must not open PRs, issues, or comments. New
   contributors must not submit LLM-generated code.
1. Record the exact build: a release tag and sha256, or
   `git rev-parse HEAD` of a
   [pinned checkout](references/build-from-source.md#pinned-source-checkout).
1. Make a case directory. Run with
   [`-datapath`](references/run-and-log.md#isolated-data-root-with--datapath)
   or [portable mode](references/run-and-log.md#portable-mode), and always
   add `-logfile`. Before the first unattended run, set
   [the wizard flag](references/run-and-log.md#first-run-wizard-flag) to
   false.
1. Build the argv with `scripts/build_command.py` ([launch][launch]), and
   bound the run with an external alarm.
1. Classify the failure by [layer][layer], and quote the log line that
   proves each layer. The [exit status is not a boot oracle][exit].
1. Change one variable at a time: the renderer, one patch group, one
   build. Keep an unmodified baseline run.
1. Re-run the same oracle. Report each claim with its layer and
   verification tier.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| Build on Linux, macOS, Windows | [Linux](references/build-from-source.md#linux-dependency-script), [macOS](references/build-from-source.md#macos-dependency-script), [Windows](references/build-from-source.md#windows-dependency-pack) |
| Pick Release, Devel, Debug, LTO | [CMake configure](references/build-from-source.md#cmake-configure-and-build-types) |
| Faster rebuilds | [ccache](references/build-from-source.md#ccache-compiler-launcher) |
| Check core code without a BIOS | [Unit tests](references/build-from-source.md#unit-tests-target) |
| Build the GS dump runner | [GS runner](references/build-from-source.md#gs-runner-target) |
| Run without touching the user's profile | [-datapath](references/run-and-log.md#isolated-data-root-with--datapath), [portable](references/run-and-log.md#portable-mode) |
| Unattended run hangs on a new root | [Wizard flag](references/run-and-log.md#first-run-wizard-flag) |
| Boot an ELF, ISO, BIOS, or state | [Launch arguments](references/run-and-log.md#launch-arguments-for-an-elf-or-disc-image) |
| "It exited 0, so it booted" | [Exit status](references/run-and-log.md#exit-status-is-not-a-boot-oracle) |
| Need emulog or guest printf | [Logging](references/run-and-log.md#logging-to-a-file) |
| Find what writes a guest value | [Breakpoints](references/debug-and-render.md#debugger-layouts-and-breakpoints), [expressions](references/debug-and-render.md#debugger-expressions) |
| Names for a stripped ELF | [Symbols](references/debug-and-render.md#symbol-import-and-sym-files) |
| Test what a function does | [Stubbing](references/debug-and-render.md#function-stubbing) |
| Someone wants `target remote` | [No GDB stub](references/debug-and-render.md#no-gdb-stub) |
| Graphics glitch | [Software oracle](references/debug-and-render.md#gs-renderer-choice-with-the-software-renderer-as-oracle), [GS dump](references/debug-and-render.md#gs-dump-capture), [replay](references/debug-and-render.md#gs-dump-replay-comparison) |
| Emulator process crashes or hangs | [lldb](references/debug-and-render.md#lldb-on-host-crashes) |
| Patch does not load or apply | [Naming](references/patches-textures-states.md#pnach-file-placement-and-naming), [patch](references/patches-textures-states.md#patch-command) |
| Conditional or pointer cheat | [RAW codes](references/patches-textures-states.md#raw-extended-codes) |
| Code moves between loads | [dpatch](references/patches-textures-states.md#dpatch-dynamic-patch) |
| Replace textures | [Textures](references/patches-textures-states.md#texture-dump-and-replacement) |
| State refuses to load, or reuse across builds | [Save states](references/patches-textures-states.md#save-state-version-caveats) |
| Worked in version A, broken in B | [Release bisect](references/triage-and-bisect.md#bisecting-over-release-builds), [git bisect](references/triage-and-bisect.md#bisecting-source-commits-with-git-bisect) |

## Rules

- Never download, generate, or copy a PS2 BIOS, a game image, or keys. Use
  only files the user supplies and owns, or self-built homebrew. Without a
  BIOS, guest-level checks are "Not runnable here". Report them that way.
- Never run PCSX2 against the default profile
  (`~/Library/Application Support/PCSX2`, `~/.config/PCSX2`,
  `Documents\PCSX2`). Use a stamp file and `find -newer` to prove it is
  untouched.
- `-datapath DIR` needs an existing `DIR` and writes to `DIR/PCSX2`.
  Portable mode overrides it.
- A green build, `-testconfig`, or exit 0 does not prove a boot. Quote a
  guest-produced log line or an artifact.
- Check every `.pnach` with `scripts/check_pnach.py` before booting. The
  loader drops bad lines with only a console error.
- Label each command with the version it applies to. `-gamecfg` and the
  breakpoint Log When Hit option exist at `v2.9.84`, not in `v2.8.2`.
- On Apple Silicon, build x86-64 dependencies only (the arm64 recompilers
  are missing). Keep `/opt/homebrew` libraries out of the dependency
  prefix.
- Do not open PCSX2 PRs, issues, or comments, and do not write their text
  (upstream `AGENTS.md`).

## Bundled tools

- `scripts/check_pnach.py FILE... [--json] [--limit N]`: loader-equivalent
  PNACH errors and warnings. Exits 1 on any error.
- `scripts/build_command.py --exe BIN [options]`: prints a checked argv
  for the `v2.8.2` CLI and never launches. Use `--native` to pass other
  options through.
- `assets/examples/verify.sh [offline|release|build]`: offline checks by
  default. The opt-in `release` and `build` modes exercise a real v2.8.2
  binary and the upstream build; the script header states each mode's
  cost.

## References

- [Build from source](references/build-from-source.md): policy, checkout,
  per-platform dependencies, CMake, ccache, unit tests, GS runner.
- [Run and log](references/run-and-log.md): data isolation, portable mode,
  wizard flag, launch arguments, exit status, logging.
- [Debug and render](references/debug-and-render.md): debugger,
  expressions, symbols, stubbing, GDB, renderer oracle, GS dumps, lldb.
- [Patches, textures, states](references/patches-textures-states.md):
  PNACH naming, `patch`, RAW codes, `dpatch`, textures, save states.
- [Triage and bisect](references/triage-and-bisect.md): layer
  classification, release bisect, git bisect.
- [Sources](references/sources.md): pinned revisions, doc and source
  conflicts, verification tiers.

## Completion evidence

The final report contains:

- the PCSX2 version, tag, or SHA and the release sha256;
- the host, and the case directory with its data root;
- each command with its exit status and the quoted log line that proves
  its layer;
- the checker output for any PNACH;
- the profile-untouched check;
- which checks were Executed, Compiled, or Not runnable here, with the
  exact error for the last group.

[policy]: references/build-from-source.md#licence-and-ai-assistant-policy
[launch]: references/run-and-log.md#launch-arguments-for-an-elf-or-disc-image
[layer]: references/triage-and-bisect.md#build-failure-versus-guest-behaviour
[exit]: references/run-and-log.md#exit-status-is-not-a-boot-oracle
