# Isolation and command-line launch

Cards for running an official release without touching the user's own
DuckStation data, and for launching it from a shell. Observations come
from release `v0.1-11826` on macOS 27 arm64, run from a copy of the
app in a scratch directory with no BIOS and no game image.

## Contents

- Portable user directory
- Default user directories
- Settings changes by file edit
- Command-line launch flags
- Save-state launch flags
- Bounded batch run
- Launch command builder

## Portable user directory

**Definition.** When an empty file named `portable.txt` sits beside the
DuckStation executable, the user directory (settings,
BIOS search path, memory cards, save states, logs, textures, cheats) is
that executable directory ([README, User Directories][readme-dirs]). On
macOS the executable directory is `DuckStation.app/Contents/MacOS`.

**Use when.**

- Every agent-driven run. The user may already have DuckStation data: on
  this machine `~/Library/Application Support/DuckStation` held `bios`,
  `memcards`, and `savestates`, and an installed copy was running.

**Do not use when.**

- You need resource overrides: the [wiki][wiki-res] says overrides do not
  work in portable mode because the user and program `resources`
  directories overlap.
- You would put `portable.txt` beside `DuckStation.app` instead of inside
  `Contents/MacOS`: untested here, and a miss writes into the user's real
  directory.
- The copy will be shared: a release plus settings counts as a
  modification under the README licence note.

**Example.**

```sh
CASE=$(mktemp -d)
ditto ./app/DuckStation.app "$CASE/DuckStation.app"
touch "$CASE/DuckStation.app/Contents/MacOS/portable.txt"
stat -f %m "$HOME/Library/Application Support/DuckStation" || true
printf 'not a PS-X EXE\n' > "$CASE/dummy.exe"
"$CASE/DuckStation.app/Contents/MacOS/DuckStation" \
  -batch -nogui -- "$CASE/dummy.exe" & PID=$!
sleep 12; kill "$PID"; sleep 1; kill -9 "$PID" 2>/dev/null || true
ls "$CASE/DuckStation.app/Contents/MacOS"
```

Observed: the first run created `settings.ini`, `bios/`, `cache/`,
`cheats/`, `covers/`, `gameicons/`, `gamesettings/`, `inputprofiles/`,
`memcards/`, `patches/`, `resources/`, `savestates/`, `screenshots/`,
`shaders/`, `subchannels/`, `textures/`, `videos/`, and `playtime.dat`
next to the executable, and the `[Folders]` section held relative names
(`SaveStates = savestates`). `-help` and `-version` created nothing.
Runnable: `assets/examples/verify.sh release`.

On Windows, create `portable.txt` beside
`duckstation-qt-x64-ReleaseLTCG.exe` in the extracted zip (README). The
Linux AppImage keeps the executable inside the image; portable use is
undocumented there and was Not runnable here.

**Cost removed.** Writes to the user's real saves and settings. Observable:
the modification time of the default user directory is unchanged, and the
portable directory gains `settings.ini`.

**Verify.**

1. `test -f .../Contents/MacOS/settings.ini` after the first run.
1. `stat -f %m "$HOME/Library/Application Support/DuckStation"` prints
   the same value before and after (or the directory stays absent). Take
   both readings immediately around your own run: on this machine the
   user's installed copy updated itself and wrote there between two runs.

## Default user directories

**Definition.** Without `portable.txt`, the user directory is
`AppData\Local\DuckStation` on Windows (older installs:
`Documents\DuckStation`), `$XDG_DATA_HOME/duckstation` or
`~/.local/share/duckstation` on Linux, and
`~/Library/Application Support/DuckStation` on macOS
([README][readme-dirs]). **Tools > Open Data Directory** in the Qt UI
opens it.

**Use when.**

- Finding a user-supplied log or crash, or checking that an isolated run
  left the real directory alone.

**Do not use when.**

- You would write into it for an experiment: use a portable copy.
  Changing the working directory does not move it.

**Example.**

```sh
case $(uname -s) in
  Darwin) D="$HOME/Library/Application Support/DuckStation" ;;
  Linux) D="${XDG_DATA_HOME:-$HOME/.local/share}/duckstation" ;;
esac
ls -la "$D" 2>/dev/null || echo "no default user directory"
```

**Cost removed.** Guessing where logs, BIOS, and saves live. Observable:
`ls` lists `settings.ini` or the subdirectories named in the portable
card.

**Verify.**

1. The listed path contains `settings.ini` once DuckStation has run
   non-portably (inspected only; this session did not write there).

## Settings changes by file edit

**Definition.** `settings.ini` in the user directory holds `[Section]`
headers and `Key = Value` lines; booleans are `true` or `false`. Release
`v0.1-11826` wrote 402 keys in 32 sections on a first run, plus
`[Main] SetupWizardIncomplete = false` in some runs. The bundled list
`assets/examples/settings/keys-0.1-11826.txt` records each `Section.Key`
and its default.

**Use when.**

- A diagnostic run needs logging, the GDB server, texture dumping, or a
  renderer choice without the UI.

**Do not use when.**

- DuckStation is running: it rewrites `settings.ini` (observed at exit
  in the crash stack `INISettingsInterface::Save`), so edits can be lost.
- The key or value is not in the bundled list (for example the exact
  value string for the software renderer): select it once in the UI of
  the same release, quit, and copy the changed line. Do not guess values.

**Example.** `settings.ini` appears only after a first launch (`-help`
and `-version` do not create it), so first run the bounded warm-up from
the portable card. Then merge
`assets/examples/settings/debug-overlay.ini` into the stopped copy and
check it:

```sh
INI="$CASE/DuckStation.app/Contents/MacOS/settings.ini"
cp "$INI" "$INI.orig"
sed -i '' -e 's/^LogToFile = false/LogToFile = true/' \
  -e 's/^LogLevel = Info/LogLevel = Debug/' "$INI"
diff "$INI.orig" "$INI"
python3 scripts/check_formats.py settings "$INI"
```

**Cost removed.** Silent typos (`LogToFiles`), non-boolean values, and
duplicate keys. Observable: `check_formats.py settings` prints `OK`; on
`assets/examples/settings/bad-overlay.ini` it prints 3 findings.

**Verify.**

1. `diff` shows only the intended lines.
1. `check_formats.py settings` exits 0 on the edited file.

## Command-line launch flags

**Definition.** Release `v0.1-11826` prints its flags with `-help` (to
stderr, exit status 1). Flags take one hyphen: `-help`, `-version`,
`-batch` (exit after powering off), `-fastboot`, `-slowboot`, `-bios`,
`-resume`, `-state <index>`, `-statefile <filename>`, `-exe <filename>`
("Boot the specified exe instead of loading from disc"), `-fullscreen`,
`-nofullscreen`, `-nogui` (no main window, exits on shutdown),
`-bigpicture`, `-earlyconsole`, and `--` (the rest is the boot filename,
for names with spaces or a leading dash). The [wiki][wiki-cli] shows the
same list for 0.1-11324. Fixture: `assets/examples/help-0.1-11826.txt`.

**Use when.**

- Launching a disc image (`.cue`, `.chd`, and other README formats), a
  homebrew PS-X EXE, or a PSF file from a script.

**Do not use when.**

- You want a flag another emulator has (`-portable`, `-datapath`,
  `--headless`): 0.1-11826 lists none of them; use `portable.txt`.
- You want `-nogui` to mean "no display needed": the process still runs
  the Qt event loop and `com.apple.NSEventThread` (observed in lldb).
  Whether it opens a dialog on boot errors is unconfirmed.

**Example.**

```sh
DS="$CASE/DuckStation.app/Contents/MacOS/DuckStation"
"$DS" -help 2>&1 | grep '^  -'
"$DS" -batch -nogui -fastboot -- "/path/with space/test.cue"
"$DS" -batch -nogui -- ./homebrew/hello.exe
```

The last two lines need a BIOS in the portable `bios/` directory and
were Not runnable here.

**Cost removed.** Invented flags. Observable: `build_command.py
--help-file` exits 2 and names any flag missing from the binary's
`-help`.

**Verify.**

1. `"$DS" -help 2>&1 | grep -c '^  -'` prints 16 for 0.1-11826.
1. `diff` of the `^  -` lines against the fixture is empty
   (`verify.sh release`).

## Save-state launch flags

**Definition.** Per the help text: `-resume` loads the resume state of the
given boot file, or the most recent resume state without one;
`-state <index>` loads a numbered per-game state with a boot file, or a
global state without one; `-statefile <filename>` loads that file and
needs no boot filename. Release notes for `v0.1-11515` say "Disable
global save states by default". The observed default is
`[Main] SaveStateOnExit = true`, so a normal exit writes a resume state.

**Use when.**

- Taking a quick look at a scene from a state file the same release
  produced.

**Do not use when.**

- The state came from another release or other settings; see
  [save states](guest-vs-emulator.md#save-states-are-not-a-regression-oracle).
- You combine two of `-resume`, `-state`, and `-statefile`: the help
  text defines no precedence, and the bundled builder rejects the mix.

**Example.**

```sh
"$DS" -statefile "$CASE/states/checkpoint.sav"
"$DS" -state 1 -- ./homebrew/hello.exe
sed -i '' 's/^SaveStateOnExit = true/SaveStateOnExit = false/' \
  "$CASE/DuckStation.app/Contents/MacOS/settings.ini"
```

**Cost removed.** State files overwritten or silently created at exit.
Observable: `ls -l savestates/` before and after a run.

**Verify.**

1. With `SaveStateOnExit = false`, `savestates/` gains no file after a
   clean exit (Not runnable here: needs a booted system).

## Bounded batch run

**Definition.** A scripted run with a hard external time limit: start the
process, wait N seconds, send SIGTERM, wait, then SIGKILL, and read the
log. Needed because the exit status and exit timing of 0.1-11826 did not
indicate boot success in observed runs.

**Use when.**

- Any unattended launch, including CI-style smoke checks.

**Do not use when.**

- A person is using the window: stop it from the UI.

**Example.** Observed with no BIOS and a dummy `.exe` boot file:

| Run | Result |
| --- | --- |
| 1st, fresh copy (A) | exited within 30 s, status 0 |
| 2nd, same copy | still running at 30 s; SIGALRM ended it (142) |
| 1st, fresh copy (verify.sh) | SIGABRT 134; crash report in `INISettingsInterface::Save` |
| 1st, fresh copy (C) | still running at 12 s; SIGTERM printed "Received CTRL+C, attempting graceful shutdown" |
| 3rd, copy C, SIGINT after 8 s | still running 3 s later; SIGKILL needed |

```sh
"$DS" -batch -nogui -- "$CASE/dummy.exe" >run.log 2>&1 & PID=$!
sleep 12
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"; sleep 2; kill -9 "$PID" 2>/dev/null && echo forced
else
  wait "$PID"; echo "exit $?"
fi
```

**Cost removed.** Hung agent sessions and false "boot passed" claims.
Observable: the script always returns within N+2 seconds and records
"forced" when SIGKILL was needed.

**Verify.**

1. `pgrep -f "$CASE"` prints nothing after the script.
1. The report quotes a log line for the checkpoint, not the exit status.

## Launch command builder

**Definition.** `scripts/build_command.py` prints, but never runs, a
DuckStation argument vector (JSON by default, `--format posix` for a
shell line). It rejects contradictory modes (`--resume` with `--state`,
`--state-file` with `--state`, two boot targets) and, with `--help-file`,
any emitted flag absent from a saved `-help` output.

**Use when.**

- Generating a launch line for a script or report, especially with paths
  that contain spaces or start with `-`.

**Do not use when.**

- You need `-exe FILE` together with a disc: build that argv directly;
  the builder's `--psx-exe` emits the positional boot path instead.

**Example.**

```sh
"$DS" -help 2>help.txt
python3 scripts/build_command.py --format posix --help-file help.txt \
  --exe "$DS" --batch --no-gui --fast-boot --boot=-odd-name.cue
python3 scripts/build_command.py --help-file help.txt --exe "$DS" \
  --native -portable      # exits 2: flag not listed
```

**Cost removed.** Quoting errors and invented flags. Observable: exit
status 2 with "flags not listed" for an unknown flag.

**Verify.**

1. `python3 scripts/test_build_command.py` prints `OK` (12 tests).
1. `sh -n -c "<line>"` parses the printed line without error.

[readme-dirs]:
https://github.com/stenzek/duckstation/blob/master/README.md#user-directories
[wiki-res]: https://github.com/stenzek/duckstation/wiki/Resource-Overrides
[wiki-cli]: https://github.com/stenzek/duckstation/wiki/Command-Line-Arguments
