# Run PCSX2 in isolation and log to a file

Cards for isolated user data, portable mode, the first-run wizard, launch
arguments, exit status, and file logging. "Executed" means the official
`v2.8.2` macOS release (`pcsx2-v2.8.2-macos-Qt.tar.xz`, sha256 `3ed9eb40…`,
x86-64 under Rosetta) ran on this machine through
`assets/examples/verify.sh release`. Source references are to commit
`2c804670` unless a card names `v2.8.2`. No BIOS or game was used.

## Contents

- Isolated data root with -datapath
- Portable mode
- First-run wizard flag
- Launch arguments for an ELF or disc image
- Exit status is not a boot oracle
- Logging to a file

## Isolated data root with -datapath

**Definition.** `-datapath DIR` sets `EmuConfig.CustomDataPath`, and
`EmuFolders::SetDataDirectory` then uses `DIR/PCSX2` as the data root, not
`DIR` itself (`pcsx2/Pcsx2Config.cpp`). Settings go to
`DIR/PCSX2/inis/PCSX2.ini`, with `bios`, `memcards`, `sstates`, `snaps`,
`logs`, `cheats`, `patches` and `textures` created beside it. Without
the flag, the root is `~/Library/Application Support/PCSX2` on macOS,
`$XDG_CONFIG_HOME/PCSX2` or `~/.config/PCSX2` on Linux, and
`Documents\PCSX2` on Windows.

**Use when.**

- Any experiment that would otherwise write to the user's settings, memory
  cards, save states, or logs.

**Do not use when.**

- Portable mode is active (`portable.txt`, `portable.ini`, or `-portable`):
  it overrides `-datapath`, as `-help` states.
- The directory does not exist: `v2.8.2` then exits 1 and creates nothing.

**Example.** Executed.

```sh
mkdir -p "$CASE/data"
"$APP/Contents/MacOS/PCSX2" -datapath "$CASE/data" \
  -logfile "$CASE/tc.log" -testconfig
test -f "$CASE/data/PCSX2/inis/PCSX2.ini"
grep 'DataRoot Directory' "$CASE/tc.log"
```

Result: exit 0, `DataRoot Directory: …/data/PCSX2`. With a missing
`$CASE/missing`, the same command exited 1, the log stopped after the
`DataRoot` line, and no directory was created.

**Cost removed.** Writes to the user's real profile. Observable: `find
"$HOME/Library/Application Support/PCSX2" -newer STAMP` prints nothing, as
it did here on a machine with a real profile.

**Verify.**

1. `grep 'DataRoot Directory' LOG` shows the case path followed by
   `/PCSX2`.
1. `touch STAMP` before the run, then `find "$PROFILE" -newer STAMP | head
   -1` prints nothing afterwards.

## Portable mode

**Definition.** Portable mode is on when `portable.ini` or `portable.txt`
exists in the application root, or when `-portable` is passed
(`EmuFolders::ShouldUsePortableMode`). The data root is then the
application root joined with the whitespace-stripped contents of
`portable.txt`; an empty file means the root itself. On macOS the
application root is the directory containing the `.app`
(`EmuFolders::SetAppRoot`); for a Linux AppImage, the directory containing
the AppImage.

**Use when.**

- Keeping a second PCSX2 version self-contained, for example one copy per
  bisect step.

**Do not use when.**

- The copy is the user's normal installation: `portable.txt` beside it
  moves where it reads settings, and the profile looks empty.
- The data root would be inside a read-only or translocated location.

**Example.** Executed.

```sh
mkdir -p "$CASE/portable"
cp -R PCSX2-v2.8.2.app "$CASE/portable/"
printf 'userdata\n' >"$CASE/portable/portable.txt"
"$CASE/portable/PCSX2-v2.8.2.app/Contents/MacOS/PCSX2" -testconfig
test -f "$CASE/portable/userdata/inis/PCSX2.ini"
```

Portable mode adds no extra `PCSX2/` level, unlike `-datapath`.

**Cost removed.** Shared state between PCSX2 versions. Observable: each
copy's `userdata/inis/PCSX2.ini` exists, and the global profile's
modification time is unchanged.

**Verify.**

1. `test -f "$CASE/portable/userdata/inis/PCSX2.ini"`.
1. The `find -newer` check from the previous card prints nothing.

## First-run wizard flag

**Definition.** A fresh data root gets `[UI] SetupWizardIncomplete =
true`. At startup `QtHost` runs the setup wizard when that flag is true or
`-setupwizard` was passed (`pcsx2-qt/QtHost.cpp`). The wizard is a GUI
dialog and appears even with `-nogui`.

**Use when.**

- Running unattended against a new `-datapath` or portable root. Create
  the root with `-testconfig`, then set the flag to `false`.

**Do not use when.**

- The user needs the wizard to pick a BIOS, controller, or game folders:
  run it interactively.

**Example.** Executed.

```sh
"$BIN" -datapath "$CASE/data" -testconfig
sed -i '' 's/^SetupWizardIncomplete = true/SetupWizardIncomplete = false/' \
  "$CASE/data/PCSX2/inis/PCSX2.ini"
```

Before the edit, `-batch -nogui -elf dummy.elf` logged no boot lines and
the 40 s alarm killed it (exit 142). After the edit, it reached
`Loading BIOS...` in 0.6 s.

**Cost removed.** Hung unattended runs. Observable: time until the log
shows `Loading BIOS...`.

**Verify.**

1. `grep SetupWizardIncomplete "$CASE/data/PCSX2/inis/PCSX2.ini"` shows
   `false`.
1. The bounded run finishes before its alarm, with an exit other than 142.

## Launch arguments for an ELF or disc image

**Definition.** `QtHost::ParseCommandLineOptions` takes single-dash
options. A positional argument, or everything after `--`, becomes the boot
filename. `-elf FILE` overrides the boot ELF. `-disc PATH` selects a host
DVD drive, not an image. `-bios` boots the system menu.
`-state N` and `-statefile F` load a state. `-fastboot` and `-slowboot`
choose the boot mode. `-fullscreen`, `-nofullscreen` and `-bigpicture`
choose the window. `-batch` exits when the VM shuts down, and `-nogui`
implies it. `-debugger` breaks on the entry point. `-turbo` and
`-unlimited` set speed; given both, `-unlimited` wins. An unknown option
raises an "Unknown parameter" error, and `-batch` without a boot target is
refused. With `v2.8.2` here, both exited 1 within 20 s; the error dialog
did not block. `-gamecfg FILE` (override game settings from an
INI) exists at `v2.9.84` and not in `v2.8.2`.

**Use when.**

- Starting a homebrew or test ELF, or an image the user legally owns,
  reproducibly from a script.

**Do not use when.**

- `-statefile` or `-fullscreen` is given without `-elf`, `-bios`, `-disc`,
  or a filename. The parser logs "Skipping autoboot due to no boot
  parameters" and boots nothing.
- The input is a BIOS or game image the user does not own. Do not obtain
  one.

**Example.** The helper prints the argv and never launches it. It models
the `v2.8.2` parser; pass newer options such as `-gamecfg` through
`--native`.

```sh
python3 scripts/build_command.py --format posix --exe "$BIN" \
  --batch --no-gui --data-path "$CASE/data" \
  --log-file "$CASE/emu.log" --elf "$CASE/test.elf"
python3 scripts/build_command.py --format posix --exe "$BIN" \
  --data-path "$CASE/data" --boot "/games/My Disc (USA).iso"
```

**Cost removed.** Runs that never boot because of a parser rule. Count:
builder rejections (exit 2) for combinations the parser would drop.

**Verify.**

1. `python3 scripts/test_build_command.py` passes, covering 11 cases.
1. `"$BIN" -help` (exit 1) lists every option the helper emits. When
   changing versions, diff it against the helper's `--help`.

## Exit status is not a boot oracle

**Definition.** In batch mode a startup error goes through
`ReportErrorAsync`, and the process then exits normally. Exit status 0
means only that the process shut down cleanly.

**Use when.**

- A scripted run claims that a guest booted or behaved correctly.

**Do not use when.**

- The claim is only that the process starts, for example a `-testconfig`
  smoke check.

**Example.** Executed with no BIOS present:

```sh
"$BIN" -datapath "$CASE/data" -logfile "$CASE/boot.log" \
  -batch -nogui -elf "$CASE/dummy.elf"; echo "exit=$?"
grep 'Startup Error' "$CASE/boot.log"
```

Output: `exit=0` and `ReportErrorAsync: Startup Error: PCSX2 requires a
PlayStation 2 BIOS in order to run.` A guest oracle must match a positive
log line or a produced artifact: a screenshot, a GS dump, or a value
checked in the debugger.

**Cost removed.** False "boots fine" reports. Count: runs reported as
passing whose log contains `Startup Error` (target 0).

**Verify.**

1. `! grep -q 'Startup Error' "$CASE/boot.log"` holds for a run reported
   as a boot.
1. A line that only a running guest can produce is present, for example
   the test ELF's own printf with `EnableEEConsole = true`.

## Logging to a file

**Definition.** `-logfile PATH` calls `VMManager::Internal::SetFileLogPath`,
which forces file logging at debug level to `PATH` from process start.
Without it, `[Logging] EnableFileLogging` (default `true`) writes
`logs/emulog.txt` under the data root. Each launch replaces that file, so
the troubleshooting guide says to close PCSX2 before copying it. Other
`[Logging]` keys: `EnableVerbose`, `EnableTimestamps` (default true),
`EnableEEConsole`, `EnableIOPConsole` (guest printf output),
`EnableSystemConsole`, and `EnableLogWindow`. When a VM starts, the log
contains `PCSX2 <version>` and `Savestate version: 0x…`. `-testconfig`
logs only the directory lines.

**Use when.**

- Every scripted run: startup errors appear only in the log.
- Guest printf debugging of a homebrew ELF: set `EnableEEConsole = true`.

**Do not use when.**

- Two processes would share one `-logfile` path: they overwrite each
  other.

**Example.** Executed. `v2.8.2` printed:

```text
[    0.1907] PCSX2 v2.8.2
[    0.1909] Savestate version: 0x9a590000
[    0.2568] DataRoot Directory: …/data/PCSX2
```

**Cost removed.** Lost evidence: the file persists after the process
exits, and a run with its own `-logfile` path is not overwritten by the
next launch. Observable: the file exists and contains the version line.

**Verify.**

1. `grep -m1 '^\[ *[0-9.]*\] PCSX2 v' "$CASE/emu.log"` shows the expected
   version.
1. Read `grep -c 'Startup Error\|Error' "$CASE/emu.log"` before claiming
   pass or fail.
