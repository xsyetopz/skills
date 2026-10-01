---
name: debug-playstation-emulators
description: >-
  Builds and debugs PCSX2 and DuckStation, including game patches, pnach
  files, settings, and emulator logging. Use for PlayStation emulator bugs or
  patches.
---

# Debug PlayStation Emulators

Run PCSX2 (PS2) and DuckStation (PS1) against a throwaway data root with a file log, and decide
which layer owns a failure before changing anything. Without this, agents touch the user's real
profile and report a boot from an exit status.

## Rules

- Never download or generate a BIOS, a game image, or keys. Copy them only from files the user
  supplies and owns (for example into the throwaway data root), or use self-built homebrew. Without
  them write "Not runnable here" for guest-level steps.
- Never run an emulator against the default profile (`~/Library/Application Support/PCSX2` or
  `DuckStation`, `~/.config/PCSX2`, `~/.local/share/duckstation`, `Documents\PCSX2`,
  `AppData\Local\DuckStation`). Use PCSX2 `-datapath` or `portable.txt`, DuckStation `portable.txt`.
  Touch a stamp file first and run `find DIR -newer STAMP` afterwards to prove the profile is
  untouched (PowerShell: `Get-ChildItem DIR -Recurse -File | Where-Object LastWriteTime -gt
  (Get-Item STAMP).LastWriteTime`).
- Do not treat a green build, exit 0, or "still running" as a boot. Both emulators exit 0 after a
  startup error, for example a missing BIOS. Quote a log line only a running guest can produce, or
  an artifact.
- Bound every unattended run with an external timeout and always write a log file. A first-run
  wizard or an error dialog hangs the run otherwise. Record a forced kill (SIGKILL, or
  `Stop-Process -Force` on Windows) as forced termination.
- Classify the failure by layer and quote the log line that proves it. The layers are configure,
  compile, package, process start, setup (wizard, BIOS), guest boot, guest behavior, renderer, host
  crash. Evidence from one layer says nothing about a later one.
- Change one variable per run (renderer, one patch, one setting, one release) and keep an unmodified
  baseline. Disable cheats, patches, texture replacements, and enhancements before blaming the
  emulator core.
- Name the release tag or commit and its sha256 in every claim. `latest`, `preview`, and nightly
  names move. Label each flag or setting with the version it was seen in. Flags differ between
  releases and between the two emulators, and there is no `-portable` or `-datapath` for
  DuckStation.
- Edit an emulator's ini only while it is stopped, because it rewrites the file on exit. Use only
  keys and values the same release wrote. For an unknown value, set it once in the UI and copy the
  changed line.
- Do not use save states across releases or as proof of a fix. They capture emulator internals and
  skip the boot path.
- Do not hand-check a `.pnach`. The PCSX2 loader drops a bad line with only a console error, so run
  `python3 scripts/check_pnach.py FILE...` before booting.
- Do not build, modify, or package DuckStation itself; writing `.cht` and game patch files is
  allowed. Its licence (CC-BY-NC-ND-4.0 plus a packaging restriction on build files) and its
  repository `CLAUDE.md` ask AI assistants not to. Say so, point to the upstream README and releases
  page, and offer to debug an official numbered release.
- Do not open PCSX2 PRs, issues, or comments, and do not write their text (upstream `AGENTS.md`).
  Building, running, and writing `.pnach` files for personal use are allowed.
- Use host `lldb` or `gdb` (Windows: WinDbg or `cdb -p PID -c "~*k; qd"`) only for emulator crashes
  and hangs, and attach only to a process you started. Guest code is debugged with the emulator's
  own debugger. PCSX2 has no GDB stub. DuckStation has one only while a guest runs.

## Workflow

1. Record the exact build: release tag and sha256, or `git rev-parse HEAD` of the PCSX2 checkout.
1. Make a case directory and an isolated data root. PCSX2: `-datapath DIR` needs an existing `DIR`
   and writes to `DIR/PCSX2`. Portable mode overrides it. DuckStation: empty `portable.txt` next to
   the executable (`Contents/MacOS` on macOS).
1. Create the settings file with one bounded warm-up launch, then enable file logging. PCSX2 also
   needs `SetupWizardIncomplete = false` in `inis/PCSX2.ini`. Check a DuckStation `settings.ini`
   edit with `python3 scripts/check_settings_keys.py`.
1. Capture the binary's own `-help` (DuckStation prints it to stderr and exits 1) and use only flags
   it lists.
1. Launch with a hard time limit, read the log, and name the failing layer.
1. Change one variable, rerun the same oracle, and report each claim with its layer and the quoted
   line.

## Scripts

- On Windows, use `py -3` for `python3`.
- `python3 scripts/check_pnach.py FILE... [--json] [--limit N]` reports the errors and warnings
  PCSX2's patch loader would raise. Exit 0 no errors, 1 errors, 2 usage or unreadable input.
- `python3 scripts/check_settings_keys.py FILE... [--keys LIST]` checks a DuckStation `settings.ini`
  against the keys release 0.1-11826 wrote (`assets/duckstation-settings-keys-0.1-11826.txt`):
  typos, duplicates, and non-boolean values. Exit 0 clean, 1 findings, 2 usage or unreadable input.
- `scripts/testdata/pnach/`: good, warn, and bad `.pnach` samples for the checker's tests.

## References

- Read [`references/pcsx2.md`](references/pcsx2.md) for PCSX2: building, data root, launch flags,
  logging, debugger, renderer, `.pnach` codes, textures, save states, and bisecting.
- Read [`references/duckstation.md`](references/duckstation.md) for DuckStation: releases, portable
  copy, settings, launch flags, logging, lldb and crash reports, textures, and `.cht` files.
