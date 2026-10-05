# DuckStation Gotchas

Commands are POSIX sh; on Windows run them in Git Bash or WSL.

Checked against official release `v0.1-11826` (`0.1-11826-gfe2306b1f`) on macOS arm64 with no BIOS
and no game image. Re-check a flag or key against `-help` of the build under test.

## Contents

- [Releases and Policy](#releases-and-policy)
- [Isolation and Settings](#isolation-and-settings)
- [Launch](#launch)
- [Logging and Debugging](#logging-and-debugging)
- [Layer Triage](#layer-triage)
- [Textures](#textures)
- [Cheats and Patches](#cheats-and-patches)

## Releases and Policy

- Mistake: building, patching, or packaging DuckStation. The licence is CC-BY-NC-ND-4.0, the
  [`CMakeLists.txt`][cmakelists] header adds "you may not use this file to create packages or build
  recipes", and the repository [`CLAUDE.md`][claude-md] asks AI assistants not to read, build, or
  run anything in it. Do not clone it or write a build recipe. Point to the upstream README
  "Building" section and the releases page, and debug an official release.
- Mistake: redistributing a release with bundled settings, BIOS, or games. The [README][readme]
  allows "unmodified releases and code" only and calls pre-configured settings and packages
  modifications.
- Mistake: identifying the binary by `latest` or `preview`. Those tags move. Use a numbered tag such
  as `v0.1-11826`, record the asset's SHA-256 (`gh release view TAG -R stenzek/duckstation --json
  assets --jq '.assets[] | "\(.name) \(.digest)"'`), and the `-version` string, which goes to stderr
  with exit 1. The releases page keeps the last 30; older ones are in
  [duckstation/old-releases][old-releases].
- Mistake: blaming DuckStation when the binary does not start on an old host. The README minimums
  are macOS 13.3, Windows 10 1809, and a distribution like Ubuntu 22.04 for AppImages.
- Mistake: building an intermediate commit to find a regression. Halve the range of numbered release
  tags instead, with the same settings and inputs, and read each release's notes for the commits it
  adds (`gh release view TAG -R stenzek/duckstation --json body`). Report the last good tag, the
  first bad tag, and the commits between them.

## Isolation and Settings

- Mistake: running an experiment against the default user directory
  (`~/Library/Application Support/DuckStation`, `$XDG_DATA_HOME/duckstation` or
  `~/.local/share/duckstation`, `AppData\Local\DuckStation`). Copy the app to a scratch directory
  and create an empty `portable.txt` beside the executable, which is
  `DuckStation.app/Contents/MacOS` on macOS. A misplaced file writes to the real directory, so
  compare its modification time around your run (macOS `stat -f %m`; PowerShell
  `(Get-Item PATH).LastWriteTime`). An installed copy may update itself in between, so take both
  readings immediately around the run.
- Mistake: expecting a flag to choose the data directory. 0.1-11826 lists no `-portable`,
  `-datapath`, or headless flag. `portable.txt` is the only switch, and the [wiki][wiki-res] says
  resource overrides do not work in portable mode.
- Mistake: editing `settings.ini` before it exists. `-help` and `-version` create nothing. Do one
  bounded warm-up launch on a dummy boot file, stop it, then edit.
- Mistake: editing `settings.ini` while DuckStation runs. It rewrites the file on exit, so the edit
  is lost.
- Mistake: guessing a value, for example the software renderer string. Set it once in the UI of the
  same release, quit, and copy the changed line. Run `scripts/check_settings_keys.py` on every edit:
  it catches typos such as `LogToFiles`, duplicates, and non-boolean values.
- Mistake: sharing a portable copy that contains your settings. That is a modification under the
  README licence note.

## Launch

- Mistake: using a flag from memory or from another emulator. Flags take one hyphen: `-batch`,
  `-nogui`, `-fastboot`, `-slowboot`, `-bios`, `-resume`, `-state INDEX`, `-statefile FILE`,
  `-exe FILE`, `-fullscreen`, `-nofullscreen`, `-bigpicture`, `-earlyconsole`, and `--` before a
  boot file whose name has spaces or a leading dash. Capture `-help` from the binary under test
  (stderr, exit 1).
- Mistake: reading `-nogui` as "needs no display". The Qt event loop and `com.apple.NSEventThread`
  still run.
- Mistake: combining `-resume`, `-state`, and `-statefile`. The help text defines no precedence.
- Mistake: leaving `[Main] SaveStateOnExit = true`, the default. A normal exit writes a resume state
  into `savestates/`. Set it to `false` for clean comparisons.
- Mistake: trusting exit status or exit timing. With no BIOS and a dummy `.exe`, one fresh copy
  exited 0 within 30 s, another was still running at 30 s, one aborted with 134, and SIGINT did not
  stop one after 8 s. Run `"$DS" -batch -nogui -- dummy.exe`, wait, send SIGTERM, wait, then SIGKILL
  (Windows: `Stop-Process`, then `Stop-Process -Force`), and record "forced". Quote a log line for
  the checkpoint.

## Logging and Debugging

- Mistake: reporting a run without a log. Set `[Logging] LogToFile = true` and `LogLevel = Debug`
  (default `Info`), which writes `duckstation.log` in the user directory. Its first lines include
  `I/Core: Version: 0.1-11826-gfe2306b1f [dev]`. Turn logging off for timing runs, as the
  [wiki][wiki-log] advises.
- Mistake: concluding boot failed because `Boot Path` or `BIOS` lines are missing. They were absent
  within 12 s in some runs. Wait for a line only a running guest produces.
- Mistake: debugging a process that dies before the file log starts. Set `LogToConsole = true` or
  pass `-earlyconsole`. Console lines carry ANSI colors (strip with `sed 's/\x1b\[[0-9;]*m//g'`),
  info lines go to stdout, and `E(...)` and `W(...)` lines go to stderr on macOS.
- Mistake: using lldb for guest code. Host frames are emulator code. Use the integrated CPU debugger
  (toolbar Debugger, pause first), and restart cold after "Patch Instruction" or "Nop Instruction",
  because the patch changes the experiment. The call stack view arrived after 0.1-11826, so check
  the release notes for the feature you need.
- Mistake: connecting a GDB client with no guest running. With `[Debug] EnableGDBServer = true`
  (port `GDBServerPort`, default `2345`) and no BIOS, nothing listened. Confirm with
  `lsof -nP -iTCP:2345 -sTCP:LISTEN` (macOS; Windows:
  `Get-NetTCPConnection -LocalPort 2345 -State Listen`), connect from the same host, and use a
  MIPS-capable GDB such as `gdb-multiarch`. Host `lldb` cannot debug the guest.
- Mistake: attaching lldb to the user's running DuckStation. Attach only to your own PID:
  `lldb --batch -p "$PID" -o 'bt all' -o detach`. The ad-hoc signed 0.1-11826 macOS binary attached
  without extra entitlements.
- Mistake: stopping on the first `EXC_BAD_ACCESS` in JIT code. The release uses fastmem and may
  handle such faults itself (inference). Continue once, or start lldb with
  `settings set platform.plugin.darwin.ignored-exceptions EXC_BAD_ACCESS`, and drop the setting once
  the fault is real, because it also skips a genuine segfault.
- Mistake: rerunning to catch a crash that already left a report. On macOS, read
  `~/Library/Logs/DiagnosticReports/DuckStation-*.ips` (one JSON header line, then a JSON body) for
  `app_version`, the signal, and the faulting thread's frames. On POSIX hosts, exit status 134 is
  SIGABRT and 139 is SIGSEGV; Windows crash exit codes are NTSTATUS values such as 0xC0000005. A
  guest crash with the process alive writes no report. One fresh-copy first run aborted at shutdown
  in `INISettingsInterface::Save`, a host crash unrelated to the guest.

## Layer Triage

- Mistake: calling a missing input an emulator bug. Walk the layers and stop at the first failing
  one: host process starts and logs its version; inputs are found (BIOS search, boot path, `.sbi`
  data); the guest reaches a named checkpoint; the checkpoint looks right under reference settings.
  No `I/Core: Version:` line or an `.ips` report is the host process,
  `I/BIOS: Searching for a ... BIOS` then nothing is the BIOS, a PAL LibCrypt title that hangs with
  no same-name `.sbi` beside the image is disc data, and a glitch that goes away with codes off is
  guest data.
- Mistake: ignoring region. The README warns that mismatched game and BIOS regions "may have
  compatibility issues". The log line `Console Region:` records the choice.
- Mistake: judging a rendering glitch on one hardware renderer. Rerun the same checkpoint with the
  software renderer at native resolution and `DisableAllEnhancements` on. If the glitch disappears,
  suspect the backend, driver, or an enhancement. If it stays, suspect the core or the guest. Do not
  use it as the reference for performance, upscaling, or texture replacement, which it lacks.
  Compare F10 screenshots.
- Mistake: leaving per-game overrides in a comparison. `gamesettings/` holds one ini per serial
  (`HASH-...` for a serial-less file). The log shows `No game settings found (tried 'NAME.ini')`.
  Keep the directory empty in every copy unless the override is the variable.
- Mistake: using save states across releases or as proof of a fix. The README and wiki document no
  compatibility, and release notes show the contents changing. Use a replayable checkpoint: cold
  boot, `-fastboot`, no state flags, copied `settings.ini`, a fixed wait, and a screenshot plus a
  log line. A memory card written by the game carries progress.

## Textures

- Mistake: dumping with the software renderer. Texture replacement is a hardware-renderer feature.
  Set `[GPU] EnableTextureCache = true` and `[TextureReplacements] DumpTextures = true` (defaults
  `false`) and stop the virtual machine before counting files in `textures/SERIAL/dumps`.
- Mistake: renaming dumps. The loader matches the generated name
  (`texupload-P4-DATAHASH-PALHASH-WxH-x-y-WxH-Pfirst-last`). Map several names to one edited file
  with `Aliases:` in `textures/SERIAL/config.yaml` ([wiki][wiki-tex]). The wiki gives no literal
  replacements path, so confirm it through Tools > Open Data Directory.
- Mistake: changing several per-game texture options per redump. The options are
  `ReducePaletteRange` (8-bit duplicates), `ConvertCopiesToWrites` (animated VRAM copies),
  `MaxVRAMWriteSplits` (vanishing partial uploads), `MaxVRAMWriteCoalesceWidth` or `Height` = 1 (log
  repeats "tracking VRAM write of Nx1"), `DumpC16Textures` (missing direct-colour textures), and
  `DumpTexturePages` (incompatible write tracking, more duplicates). Change one, redump, and compare
  the dump count.
- Mistake: raising cache limits just in case. The wiki warns that too many texture objects break
  mobile drivers and too much VRAM use causes swapping.

## Cheats and Patches

- Mistake: blaming the emulator with codes on. Patches (`patches/`) and cheats (`cheats/`) change
  guest memory, so disable all codes and rerun first. A patch never proves an emulator fix.

[cmakelists]:
https://github.com/stenzek/duckstation/blob/0d8dda34d3785d8a5c9e910b9ef50caa85fcde0c/CMakeLists.txt
[claude-md]:
https://github.com/stenzek/duckstation/blob/0d8dda34d3785d8a5c9e910b9ef50caa85fcde0c/CLAUDE.md
[readme]: https://github.com/stenzek/duckstation/blob/master/README.md
[old-releases]: https://github.com/duckstation/old-releases/releases
[wiki-res]: https://github.com/stenzek/duckstation/wiki/Resource-Overrides
[wiki-log]: https://github.com/stenzek/duckstation/wiki/Enabling-Logging
[wiki-tex]: https://github.com/stenzek/duckstation/wiki/Texture-Replacement
