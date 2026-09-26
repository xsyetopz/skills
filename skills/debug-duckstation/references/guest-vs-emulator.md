# Emulator fault or guest behavior

Cards for deciding which layer owns a symptom: the host process, the
emulator core, the renderer, the inputs (BIOS, disc image, patches), or
the guest program. Observations come from release `v0.1-11826` on macOS 27
arm64 with no BIOS and no game image.

## Contents

- Layer triage
- Software renderer as an oracle
- Per-game settings file
- Save states are not a regression oracle

## Layer triage

**Definition.** Walk the layers in order and stop at the first one whose
evidence fails: (1) host process starts and logs its version; (2) inputs
are found (BIOS search, boot path, SBI/subchannel data); (3) the guest
reaches a named checkpoint; (4) the checkpoint looks right under the
reference settings. The lowest failing layer owns the failure.

**Use when.**

- Any report of "DuckStation crashes / hangs / renders wrong / game
  broken".

**Do not use when.**

- The run is not isolated in a portable copy: per-game settings, cheats,
  and texture packs from the user's real directory change every layer
  above (1).

**Example.**

| Evidence | Owner | Next step |
| --- | --- | --- |
| No `I/Core: Version:` line; macOS `.ips` report | host process | [crash report](logging-and-debugging.md#macos-crash-report) |
| `I/BIOS: Searching for a ... BIOS` then nothing | input: BIOS | user supplies a dumped BIOS (README) |
| PAL LibCrypt title hangs; no `.sbi` next to image | input: disc data | same-name `.sbi` beside the image (README) |
| Hang or glitch only with cheats/patches on | guest data change | disable all codes, re-run |
| Glitch gone with software renderer | renderer path | [software renderer](#software-renderer-as-an-oracle) |
| Same fault on real hardware or in other releases | guest program | guest debugger / GDB server |

The README warns that mismatched game and BIOS regions "may have
compatibility issues"; the log line `Console Region:` records the region
DuckStation chose. Observed for a non-PS-X text file named `.exe`:
`EXE/PSF Region: Other` and `Console Region: NTSC-U/C`, then the BIOS
search.

Read the first two rows from the run's log and crash reports, as
`assets/examples/verify.sh` does (the `release` mode, run against a
portable copy with `LogToFile = true`):

```sh
    grep -m1 'I/Core: Version:' "$macos/duckstation.log"
    # Boot progress lines (Boot Path, BIOS search) appeared in some runs
    # only, so they are printed, not asserted.
    grep -m2 -E 'I/System: Boot Path|I/BIOS: Searching' \
        "$macos/duckstation.log" || echo 'no boot line logged this run'
    echo 'PASS log file written next to the executable'
    find "$HOME/Library/Logs/DiagnosticReports" -name 'DuckStation-*.ips' \
        -newer "$work/ds.zip" 2>/dev/null | sed 's/^/crash report: /'
```

**Cost removed.** Emulator bug reports that are really missing inputs or
user settings. Observable: the report names the lowest failing layer and
quotes its log line.

**Verify.**

1. The quoted log line appears in `duckstation.log` of the run.
1. Changing only the owning layer's input, and nothing else, changes the
   result.

## Software renderer as an oracle

**Definition.** DuckStation has hardware renderers (D3D11, D3D12,
OpenGL, Vulkan, Metal) and a "vectorized and multi-threaded software
renderer" ([README][readme]). The README lists upscaling, texture
filtering, true colour, and texture replacement as hardware-renderer
features. The renderer key is `[GPU] Renderer` (default `Automatic` in
0.1-11826);
`[Main] DisableAllEnhancements` (default `false`) and
`[GPU] UseSoftwareRendererForReadbacks` (default `false`) also exist.

**Use when.**

- A visual defect: run the same checkpoint with the software renderer at
  native resolution and enhancements off. If the defect disappears,
  suspect the hardware backend, driver, or an enhancement; if it stays,
  suspect the core or the guest.

**Do not use when.**

- The defect is performance, upscaling, or texture replacement: the
  software renderer lacks them, so it cannot be the reference.
- You would write the renderer value from memory: the software value
  string was not observed. Select Software once in **Settings > Graphics**
  of the same release, quit, and copy the changed `Renderer = ...` line
  (see
  [settings changes](isolation-and-launch.md#settings-changes-by-file-edit)).

**Example.**

```sh
M="$CASE/DuckStation.app/Contents/MacOS"
cp "$M/settings.ini" hw.ini          # hardware run settings
# In the UI: Graphics > Renderer > Software; quit DuckStation.
diff hw.ini "$M/settings.ini"         # shows the exact Renderer line
python3 scripts/check_formats.py settings "$M/settings.ini"
```

Then capture the same checkpoint in both configurations (F10 saves a
screenshot by default) and compare the images.

**Cost removed.** Driver bugs filed as core bugs, and the reverse.
Observable: two screenshots of one checkpoint with the `Renderer` line
recorded for each.

**Verify.**

1. `diff` shows only the renderer-related lines between the two runs.
1. Tier: Not runnable here (needs a booted guest).

## Per-game settings file

**Definition.** Per-game overrides live in `gamesettings/` in the user
directory (`[Folders] GameSettings = gamesettings`), one ini per game,
named by serial. A boot file without a serial gets a hash serial:
observed `No game settings found (tried 'HASH-6C16B2EABF1E2FD.ini')` for
a dummy `.exe`, and `Game: not-an-exe | HASH-6C16B2EABF1E2FD`.

**Use when.**

- Checking whether a user's per-game override explains a symptom that a
  fresh portable copy does not show.

**Do not use when.**

- Comparing releases or renderers: keep `gamesettings/` empty in every
  copy unless the override is the variable under test.

**Example.**

```sh
grep -h 'No game settings found\|Game: ' "$M/duckstation.log"
ls "$M/gamesettings"
python3 scripts/check_formats.py settings "$M"/gamesettings/*.ini
```

**Cost removed.** Hidden per-game overrides. Observable: the log names
the ini file it tried, and `gamesettings/` lists what exists.

**Verify.**

1. The log's `tried '<name>.ini'` matches a file you created, or no
   file.

## Save states are not a regression oracle

**Definition.** A save state is a snapshot of emulator internals in
`savestates/`, compressed per `[Main] SaveStateCompression` (default
`ZstDefault`), with `CreateSaveStateBackups = true` and
`LoadDevicesFromSaveStates = false` by default in 0.1-11826. The README
and wiki document no cross-release compatibility, and release notes show
the contents changing: "GPU: Don't save settings to save state"
(`v0.1-10091`), "System: Handle corrupted save states when resuming"
(`v0.1-10903`).

**Use when.**

- Returning to a scene on the same release with the same settings.

**Do not use when.**

- Comparing two releases: a state may not load, or may load internals
  the newer release computes differently, so a difference can come from
  the state rather than the regression.
- Proving a fix: a state skips the boot path and the code that produced
  it.

**Example.** Use a replayable checkpoint instead:

```text
Checkpoint "title-screen" for homebrew hello.exe
- Binary: v0.1-11826 macOS zip, digest 1870ef7c...
- Settings: copied settings.ini (sha256 recorded); gamesettings empty
- Start: cold boot, -fastboot, no state flags
- Input: none; wait 10 s
- Evidence: F10 screenshot + duckstation.log line with the boot path
```

A memory-card save written by the game is PlayStation data, not an
emulator snapshot, and is the portable way to carry progress (a statement
about formats, not tested here).

**Cost removed.** False regressions from stale states. Observable:
the comparison report contains no `-state`, `-resume`, or `-statefile`.

**Verify.**

1. `grep -E -- '-state|-resume|-statefile' <run script>` prints nothing
   for cross-release comparisons.
1. Tier: settings defaults Executed; cross-release loading Not runnable
   here.

[readme]: https://github.com/stenzek/duckstation/blob/master/README.md
