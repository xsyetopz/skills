# Commands and isolated data paths

Research: 2026-09-09. Latest stable examined: **PCSX2 v2.8.2**. The
[release][ref-1], [CLI guide](https://pcsx2.net/docs/advanced/cli/) and [pinned
Qt parser][ref-2] establish this baseline. Command combinations below follow the
pinned parser.

## Interface and combinations

- **`-help`, `-version`** Meaning in the examined parser: Print
  interface/version information and stop normal startup.

- **`-batch`** Meaning in the examined parser: Exit after VM shutdown; requires
  a retained boot request unless big-picture mode applies.

- **`-nogui`** Meaning in the examined parser: Hide the main window and imply
  batch behavior; does not remove Qt or GPU dependencies.

- **`-bigpicture`** Meaning in the examined parser: Start the full-screen
  frontend; may be used without a game.

- **`-fastboot`, `-slowboot`** Meaning in the examined parser: Override boot
  speed/BIOS-intro choice; use one.

- **`-bios`** Meaning in the examined parser: Boot BIOS without disc media.

- **`-elf FILE`** Meaning in the examined parser: Override the boot executable;
  can be used alone or with disc media.

- **`-disc DRIVE`** Meaning in the examined parser: Select a physical DVD drive,
  not an ISO filename.

- **`-gameargs STRING`** Meaning in the examined parser: Supply one argument
  string for the game executable. Shell quoting must preserve it as one host
  argument.

- **`-state N`** Meaning in the examined parser: Select a numbered state; pair
  with the game's boot target.

- **`-statefile FILE`** Meaning in the examined parser: Set an explicit state
  path, but by itself does not retain an autoboot request in this parser.

- **`-datapath DIR`** Meaning in the examined parser: Override the data root.

- **`-portable`** Meaning in the examined parser: Use portable storage; takes
  precedence over `-datapath`.

- **`-logfile FILE`** Meaning in the examined parser: Override the log
  destination.

- **`-testconfig`** Meaning in the examined parser: Initialize configuration and
  exit; does not boot a guest.

- **`-setupwizard`** Meaning in the examined parser: Request setup UI; not an
  unattended guest check.

- **`-debugger`** Meaning in the examined parser: Open debugger and request
  paused boot.

- **`-fullscreen`, `-nofullscreen`** Meaning in the examined parser: Override
  initial window presentation.

- **`-turbo`, `-unlimited`** Meaning in the examined parser: Both select
  unlimited mode in this parser; do not infer a distinct configured turbo
  multiplier from the option name.

Options use single hyphens; `--` marks a positional boot filename. The parser
retains autoboot for a source type, filename or ELF override. A save-state
filename alone is not included in that retention test: pair it with the
appropriate game. The restricted helper can print a standalone `-statefile`
command but cannot express that combined target. Construct the combined command
directly.

## Launch recipes

```sh
/case/pcsx2-qt -batch -nogui -datapath /case/data -logfile \
  /case/data/emulog.txt -- /fixtures/game.iso
/case/pcsx2-qt -datapath /case/data -elf /fixtures/test.elf -gameargs \
  'level=2 mode=test'
/case/pcsx2-qt -datapath /case/data -elf /fixtures/test.elf -- \
  /fixtures/game.iso
/case/pcsx2-qt -datapath /case/data -elf /fixtures/test.elf -disc /dev/sr0
/case/pcsx2-qt -datapath /case/data -statefile \
  /case/data/sstates/checkpoint.p2s -- /fixtures/game.iso
/case/pcsx2-qt -datapath /case/data -state 1 -- /fixtures/game.iso
/case/pcsx2-qt -datapath /case/data -bios
/case/pcsx2-qt -datapath /case/data -testconfig
```

The ELF-plus-image recipe mounts media for an executable that needs disc assets.
`-disc` selects a host drive; do not append a positional ISO to a drive launch,
because both feed the boot filename field. The drive example requires that
device and permission on the actual host. Use `-testconfig` without batch/no-GUI
flags, which impose a boot-target requirement. It validates configuration
initialization only.

A disc image must match the fixture revision and contain the expected boot
executable. For ELF work, record identity, entry point, and required assets.
BIOS presence, region and settings remain relevant to guest startup. For disc
swapping, use the VM's disc change action and verify the expected second-disc
checkpoint; starting a new ISO process is not equivalent to a guest-requested
swap.

## Command builder

```sh
python3 scripts/build_command.py --exe /case/pcsx2-qt --batch --no-gui \
  --data-path /case/data --log-file /case/data/emulog.txt --boot \
  /fixtures/game.iso
python3 scripts/build_command.py --exe /case/pcsx2-qt --data-path /case/data \
  --elf /fixtures/test.elf --game-args 'level=2 mode=test'
python3 scripts/build_command.py --exe /case/pcsx2-qt --data-path /case/data \
  --test-config
```

Run from the skill directory. The builder prints POSIX-quoted shell text and
never launches. Its target alternatives, speed flags and storage strategies are
deliberately restricted; these restrictions are not the emulator's complete
grammar. Its `--disc` combination is limited to ELF use. Construct
ELF-plus-image and state-file-plus-image commands directly for this parser.
Prefer argument arrays in code, and apply Windows shell quoting when using a
Windows shell. Check boot compatibility with the selected executable and guest
fixture.

## Data isolation and host requirements

Create an owned writable root before launch. Copy required BIOS, configuration,
memory cards, states, patches and texture fixtures into it. Check configured
paths and per-game overrides; a new root can still contain copied settings
pointing at ordinary user saves. Keep logs and generated captures in the case
tree. Avoid launching the normal installation with portable mode, which changes
where it writes. `-datapath` is the explicit strategy for these examples; do not
combine it with `-portable`.

Complete first-run setup and select the copied BIOS where necessary. A timeout
while a setup dialog waits is not a hung guest. `-nogui` still needs a working
host arrangement for Qt, rendering, audio and input. Use a bounded external
timeout, retain stdout/stderr/logs and distinguish VM shutdown from a signal or
forced kill. Terminate only the owned process tree. Continue with
[debugging and evidence](debugging-and-evidence.md),
[patches and textures](patches-and-textures.md) or
[source builds](source-builds.md).

[ref-1]: https://github.com/PCSX2/pcsx2/releases/tag/v2.8.2
[ref-2]: https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-qt/QtHost.cpp
