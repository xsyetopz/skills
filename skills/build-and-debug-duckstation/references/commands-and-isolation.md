# DuckStation PS1 emulator: construct launch arguments

Implementation baseline: DuckStation commit
`cbe7951be624a3fd69c81858647a8f84e4a1d06b`. Verify the target build before using
version-specific interfaces.

## Launch interface

Options use one hyphen. `--` ends option parsing and the remainder forms the
positional boot path; quote a path as one argument rather than relying on token
concatenation.

- **`-help`, `-version`** Examined behavior: Print interface/build information
  and stop normal startup; do not assume a conventional success exit code
  without observing this build.

- **`-batch`** Examined behavior: Exit when emulation shuts down.

- **`-nogui`** Examined behavior: Suppress the main window; implies batch except
  with big-picture mode. Still initializes Qt/host rendering services.

- **`-bigpicture`** Examined behavior: Start the full-screen frontend, including
  its no-autoboot use case.

- **`-fastboot`, `-slowboot`** Examined behavior: Override the configured
  BIOS-intro boot choice. Use one.

- **`-bios`** Examined behavior: Retain an autoboot request without a disc path
  and start BIOS.

- **`-exe FILE`** Examined behavior: Set an executable override; it does **not
  by itself retain autoboot** in this parser.

- **`-state N`** Examined behavior: Load a numbered per-game state with a boot
  filename, otherwise a global state.

- **`-resume`** Examined behavior: Load a per-game resume state with a filename,
  otherwise the most recent resume state.

- **`-statefile FILE`** Examined behavior: Load the specified existing state
  file. This keeps the autoboot request.

- **`-fullscreen`, `-nofullscreen`** Examined behavior: Override initial display
  state; use one.

- **`-earlyconsole`** Examined behavior: Create/attach the early console on
  applicable hosts for startup diagnosis.

A batch launch without a retained boot target fails unless big-picture mode
applies. A missing state file fails before boot. For a different build, check
its parser/help. This parser has no `-datapath`, `-portable`, or headless
switch.

## Disc, executable and state recipes

```sh
/case/duckstation-qt -batch -nogui -- /fixtures/game.cue
/case/duckstation-qt -batch -- /fixtures/test.exe
/case/duckstation-qt -batch -exe /fixtures/test.exe -- /fixtures/game.cue
/case/duckstation-qt -bios
/case/duckstation-qt -state 1 -- /fixtures/game.cue
/case/duckstation-qt -resume -- /fixtures/game.cue
/case/duckstation-qt -statefile /case/savestates/checkpoint.sav
```

The second recipe uses the positional executable path: the boot implementation
recognizes executable extensions and chooses executable boot. The third keeps
the disc mounted while overriding its boot executable, useful for a fixture that
reads disc assets. Do not use `-exe FILE` alone as a standalone launch recipe.
Validate executable contents as well as the extension.

For multi-track CD images, use the cue sheet so track layout is preserved. Keep
referenced tracks in the expected relative locations. CHD can preserve a
compressed disc representation; a raw first-track BIN may omit audio/layout
information. An M3U can describe a multi-disc set, but verify each member path
and disc-switch checkpoint. BIOS region, media revision, controller
configuration and memory-card policy can affect results; record them for runtime
work. The README lists supported formats, including CUE/BIN, CHD, MDS/MDF, CCD,
ECM and unencrypted PBP.

## Command builder

```sh
python3 scripts/build_command.py --exe /case/duckstation-qt --batch --no-gui \
  --boot /fixtures/game.cue
python3 scripts/build_command.py --exe /case/duckstation-qt --batch --boot \
  /fixtures/test.exe
```

Run from the skill directory. The helper prints POSIX shell quoting and never
launches. Its boot/BIOS/state-file/PS-X-EXE targets are mutually exclusive. Its
`--psx-exe` and `--boot` both emit a positional boot path, preserving standalone
executable autoboot. Disc-plus-override must be constructed directly as an
argument array or quoted command. The helper also rejects some frontend
combinations accepted by the host. Use argument arrays for programmatic launch
and shell-specific quoting for Windows.

## Isolation procedure

1. Copy a supported portable package into an owned writable case directory,
   including its required libraries/resources. Create empty `portable.txt`
   beside that copy's executable, not beside the normal installation.
1. Open **Tools → Open Data Directory** and verify that the resolved location is
   the case tree. Packaged AppImage/app-bundle layouts can place the real
   executable differently; use a disposable extracted/package copy and verify
   rather than guessing where the marker is resolved.
1. Copy only required BIOS, settings, memory cards, states and texture fixtures.
   Configure paths to those copies. Inspect per-game overrides and
   shared/per-game card selection so the run cannot accidentally use ordinary
   saves.
1. Complete required first-run configuration in the isolated copy before
   expecting unattended boot. Keep original media and saves unchanged.
1. Launch the owned process with a bounded external timeout and capture logs. On
   a hang, terminate only its process tree and record forced termination; a
   killed process is not a normal VM shutdown.

Without portable mode, documented defaults are Windows local AppData (older
installations may use Documents), Linux `$XDG_DATA_HOME/duckstation` or
`~/.local/share/duckstation`, and macOS `~/Library/Application
Support/DuckStation`. Changing working directory alone does not isolate these
stores.

With `-nogui`, provide required Qt platform, GPU, audio, and input services.
Verify guest progress at a defined checkpoint. Read the relevant reference for
debugging, patches or textures; source compilation has its own build workflow.

Parser behavior is pinned to the [Qt command parser][parser-source]; executable
boot dispatch is defined by the [core boot implementation][boot-source].

[parser-source]:
https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/duckstation-qt/qthost.cpp
[boot-source]:
https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/system.cpp
