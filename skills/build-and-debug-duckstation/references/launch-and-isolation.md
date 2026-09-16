# DuckStation PS1 emulator: isolate launch data

First inspect the selected binary's help and matching parser. The historical
source anchor below documents the command patterns carried forward from the
supplied repository; it is not a claim that every installed version supports
them.

```sh
# Disc image/descriptor; preserve every referenced track.
duckstation-qt -batch -- /fixtures/game.cue
# Standalone PS-X executable as the boot target.
duckstation-qt -batch -- /fixtures/test.exe
# Executable override while retaining a disc as the boot context.
duckstation-qt -batch -exe /fixtures/test.exe -- /fixtures/game.cue
```

At the linked parser revision, `-exe FILE` is an executable override and is not
by itself a complete standalone autoboot request. Do not replace the positional
standalone executable example with that incomplete form. Use `--` to end options
when the selected parser supports it, and pass each path as a distinct argument
rather than concatenating shell text.

`-nogui` hides the main window; it does not establish a display-server-free,
GPU-free, or Qt-free headless runtime. Check actual platform, graphics, input,
and audio prerequisites before diagnosing no-window operation as a guest hang.
Do not import PCSX2's `-datapath` or `-portable` switches into DuckStation
without verifying they exist in the selected parser.

When the chosen version supports portable mode via `portable.txt`, copy the
complete application package to a disposable writable location and place the
marker where that version expects it, normally beside the actual executable. A
symlink to the installed binary is not necessarily an isolated package. Verify
the effective data directory through the application's native facility or logs.
Check copied configuration for absolute paths still pointing to normal memory
cards, saves, or texture directories.

Save-state slot, resume, and state-file behavior depend on the version and boot
identity. Select only the requested mode and inspect the native help; do not
combine contradictory selectors or assume a state from another revision/game is
compatible.

Source anchor: [DuckStation command parser,
cbe7951be624a3fd69c81858647a8f84e4a1d06b][ref-duckstation-command-parser].
Verify the actual selected binary before execution.

[ref-duckstation-command-parser]: https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/duckstation-qt/qthost.cpp
