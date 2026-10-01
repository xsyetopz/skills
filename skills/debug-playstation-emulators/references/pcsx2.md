# PCSX2 gotchas

Commands are POSIX sh; on Windows run them in Git Bash or WSL.

Checked against PCSX2 commit `2c804670` (`v2.9.84`) and the official
`v2.8.2` macOS release. Re-check a flag or key against `-help` and the source
of the build under test.

## Contents

- [Build](#build)
- [Data root and launch](#data-root-and-launch)
- [Logging](#logging)
- [Debugger](#debugger)
- [Renderer and GS dumps](#renderer-and-gs-dumps)
- [Host crashes with lldb](#host-crashes-with-lldb)
- [Patches and pnach files](#patches-and-pnach-files)
- [Textures](#textures)
- [Save states](#save-states)
- [Bisecting a regression](#bisecting-a-regression)

## Build

- Mistake: building with GCC. CMake prints `UNSUPPORTED CONFIGURATION`. Use
  clang and lld. Linux: run
  `.github/workflows/scripts/linux/build-dependencies-qt.sh DIR`, which
  builds pinned libraries and matches CI.
- Mistake: using Homebrew or arm64 libraries on Apple Silicon. CMake warns
  "no EE/VU/IOP recompilers" for arm64, and KDDockWidgets fails to link
  against `/opt/homebrew` spdlog. Run
  `.github/workflows/scripts/macos/build-dependencies.sh DIR` (x86-64,
  runs under Rosetta), keep `/opt/homebrew` out of the prefix path, and
  configure with `-DCMAKE_OSX_ARCHITECTURES=x86_64`. `BUILD_FFMPEG=0` skips
  FFmpeg. The script needs Xcode, `nasm`, and ccache.
- Mistake: checking out a branch tip when a report names a build. Take a
  shallow checkout of the exact tag or commit so dependency scripts match
  the binary. `.gitmodules` is empty and third-party code is in
  `3rdparty/`. For an official release, download the asset and record its
  sha256 instead of building.
- Windows: extract the `pcsx2-windows-dependencies` release to `deps\` in
  the repo root and open `PCSX2_qt.slnx`. Visual Studio older than 17.10
  cannot open `.slnx`.
- Build type: unset means `Devel`. Use `Debug` or `Devel` for lldb or
  trace logs, `Release` with LTO (`clang-release` preset) for timing. Never
  compare timing between a `Debug` build and a release binary.
- Setting `-DCMAKE_CXX_COMPILER_LAUNCHER=ccache` without ccache installed
  configures fine and fails every compile with `ccache: command not found`.
- `ninja unittests` builds and runs `common_test` and `core_test`,
  including 60 `Patch.*` tests. Use it to check patch-engine or `common/`
  changes when a full build is blocked. It does not boot a VM, so it proves
  nothing about guest behavior or rendering.
- `pcsx2-gsrunner` is excluded from `all` unless `-DENABLE_GSRUNNER=ON`.
  Apple builds accept `-renderer metal`, which the docs omit.

## Data root and launch

- `-datapath DIR` needs an existing `DIR`, else `v2.8.2` exits 1 and
  creates nothing. The data root is `DIR/PCSX2`, so copying a BIOS to
  `DIR/bios` is never found. Put it in `DIR/PCSX2/bios`.
- Portable mode (`portable.ini`, `portable.txt`, or `-portable`) overrides
  `-datapath` and adds no `PCSX2/` level. The root is the app root joined
  with the trimmed contents of `portable.txt`. On macOS the app root is the
  directory holding the `.app`.
- A new root has `[UI] SetupWizardIncomplete = true`, which opens a GUI
  wizard even with `-nogui` and hangs an unattended run. Create the root
  with `-testconfig`, then set the flag to `false`. Verify with a bounded
  run that reaches `Loading BIOS...`.
- Options take a single dash. A positional argument or everything after
  `--` is the boot file. `-elf FILE` overrides the boot ELF. `-disc` selects
  a host DVD drive, not an image. `-batch` without a boot target is
  refused, and `-nogui` implies `-batch`. `-statefile` or `-fullscreen`
  without `-elf`, `-bios`, `-disc`, or a file logs "Skipping autoboot" and
  boots nothing. `-gamecfg FILE` exists at `v2.9.84`, not in `v2.8.2`.
  `-unlimited` wins over `-turbo`. An unknown option exits 1 after
  "Unknown parameter".

## Logging

- `-logfile PATH` forces debug-level file logging from process start.
  Without it, `[Logging] EnableFileLogging` writes `logs/emulog.txt`, which
  each launch replaces. Two processes sharing one `-logfile` overwrite each
  other.
- Guest printf needs `[Logging] EnableEEConsole = true` (IOP:
  `EnableIOPConsole`). Without it a homebrew ELF's own output never
  appears.
- A running VM logs `PCSX2 <version>` and `Savestate version: 0x...`.
  `-testconfig` logs only directory lines, so it proves the config loads
  and nothing more.
- Evidence of a failed start:
  `grep -m1 -E 'CMake Error|FAILED:|Startup Error|Error Parsing' LOGFILE`
  (PowerShell:
  `Select-String 'Startup Error' LOGFILE | Select-Object -First 1`).
  `Startup Error: ... BIOS` comes with exit 0.

## Debugger

- Open it from Debug > Open Debugger after ticking Tools > Show Advanced
  Settings, or pass `-debugger` to break at the entry point. Layout `R5900`
  targets the EE and `R3000` the IOP. EE addresses, IOP addresses, ELF file
  offsets, and host pointers are different spaces.
- Breakpoint types are Execute and Memory (Read, Write, Change). To find
  what writes a value, search memory, filter after it changes, then set a
  Memory > Write breakpoint on the surviving address. Log When Hit,
  Continue on hit, and Max Hits exist at `v2.9.84`, not in `v2.8.2`.
- Bare integers in expressions are hexadecimal: `a0==10` compares with
  sixteen. Use `0o` or a trailing `o` for octal. `[a]` reads 4 bytes and
  `[a,n]` reads 1, 2, 4, or 8.
- Symbols come from the ELF `.symtab`, `.mdebug`, and SNDLL `.sndata`, not
  DWARF. A `.sym` file has `<hex address> <name>[:<size>]` lines. Its
  `.byt` and `.asc` elements are 1 byte, `.wrd` 2, and `.dbl` 4, which
  differs from MIPS word and doubleword.
- Stub (NOP) Function writes `jr ra; nop` over the first two instructions.
  It breaks any caller that uses the return value (`v0` stays stale), and
  the run no longer shows unmodified behavior. Use Restore Function after.
- There is no GDB remote stub: `target remote :port` does not work.
  `gdb` and `lldb` attach to the host process, not the guest.

## Renderer and GS dumps

- `[EmuCore/GS] Renderer`: `-1` Auto, `3` DX11, `15` DX12, `12` OpenGL, `14`
  Vulkan, `17` Metal, `13` Software, `11` Null. A per-game ini in
  `gamesettings/` overrides the global value, so a copied
  `gamesettings/` can silently keep the old renderer. `F9` toggles
  software and hardware.
- Software is the oracle for a visual bug: if the defect vanishes, suspect
  the hardware backend, driver, or upscaling. It renders at native
  resolution only and is CPU-bound, so it cannot judge upscaling artifacts
  or performance.
- A GS dump (Shift+F8 single frame, Ctrl+Shift+F8 several, into `snaps/`)
  holds GS traffic only and ignores graphics settings. It cannot reproduce
  timing, audio, input, or CPU bugs.
- `test_run_dumps.py` skips an existing `OUT/<dumpname>`, discards runner
  output, and `test_check_dumps.py` compares PNG MD5s for frames present in
  the baseline only. An empty baseline passes vacuously. The docs' extra
  `/pcsx2-gsrunner` level in `-baselinedir` does not exist.

## Host crashes with lldb

- The official macOS release has the hardened runtime without
  `get-task-allow`, so lldb cannot attach. Attach to a scratch copy after
  `codesign --remove-signature scratch.app/Contents/MacOS/PCSX2` (never the
  user's install), or use a `Debug` or `Devel` build. The release build has
  symbols but no line numbers.
- PCSX2 raises `EXC_BAD_ACCESS` on purpose for its fastmem handler. Make
  lldb pass those on with `settings set
  platform.plugin.darwin.ignored-exceptions EXC_BAD_ACCESS`. On Linux use
  `process handle SIGSEGV -n false -p true -s false`. Otherwise every
  first stop is a false crash.

## Patches and pnach files

- Patches load from `patches/`, cheats from `cheats/` and only with Enable
  Cheats on, bundled ones from `resources/patches.zip`. The loader globs
  `SERIAL_CRC*.pnach`, then `CRC*.pnach`. The CRC is 8 hex digits, matched
  case-insensitively. Addresses and CRCs differ per region and revision.
- A `patch=` line before the first `[group]` is legacy and always on. One in
  `patches/` also stops the loader from reading `patches.zip` for that
  game. A `[group]` name already loaded is skipped. Groups `Widescreen
  16:9` and `No-Interlacing` apply automatically with the matching global
  settings.
- Format: `patch=<place>,<cpu>,<address>,<type>,<data>`. `place` is `0`
  startup, `1` every vsync, `2` both, `3` startup and when enabled. `cpu` is
  `EE` or `IOP`, case-sensitive. `address` is at most 8 hex digits with no
  `0x`. `type` is lowercase: `byte`, `short`, `word`, `double`, `extended`,
  `beshort`, `beword`, `bedouble`, `bytes`. `data` is bare hex. Whitespace
  around fields is fine. A value wider than the type is truncated. A bad
  line logs `(Patch) Error Parsing: ...` and is dropped while the game
  runs.
- `gsaspectratio` takes only `N:M`. `Stretch` and `Auto 4:3/3:2` appear in
  the docs but log `is an unknown aspect ratio`.
- `type=extended` RAW codes use the high nibble of `address`: `0`-`2`
  writes, `3` increment, `4` strided, `5` copy, `6` pointer, `7`
  OR/AND/XOR, `D` and `E` conditionals. `9` and `C` are unsupported.
  Multi-line codes use consecutive `patch=` lines. Do not mix conditionals
  with non-extended lines. A `D` code `Daaaaaaa,nntsvvvv` skips the next
  `max(n,1)` commands when false. Pointer codes of three or more lines were
  misread up to `v2.7.168`, and `bytes` patches were not applied from
  `v2.7.169` to `v2.7.185`.
- `dpatch=0,<P>,<R>,<off>,<val>,...` (P pattern pairs, then R replacement
  pairs, hex) patches code that loads at varying addresses. It only runs
  under the EE recompiler, and a pattern with an absolute address immediate
  stops matching after relocation.
- A patch that should reach every user belongs upstream in GameDB or
  `pcsx2_patches`, which is a contribution. Do not open the PR.

## Textures

- `[EmuCore/GS] DumpReplaceableTextures` writes PNGs to
  `textures/<SERIAL>/dumps/`. `LoadTextureReplacements` reads `.png` or
  `.dds` from `textures/<SERIAL>/replacements/`. Both need a hardware
  renderer and a game serial. Names encode hashes
  (`<TEX0hash>[-<CLUThash>][-r<W>x<H>]-<bits>[-mip<N>].png`), so a renamed
  file never matches. Turn dumping off for performance comparisons.

## Save states

- A state (`.p2s`) loads only when its version is not newer and the upper
  16 bits match (`g_SaveVersion`; `0x9A590000` at both pinned builds).
  Commits that bump it carry `[SAVEVERSION+]` in the message. A state is
  never the only evidence of a bug. Reproduce from a cold boot or a
  memory-card save.

## Bisecting a regression

- Release bisect: list tags with
  `gh api 'repos/PCSX2/pcsx2/releases?per_page=100' --jq '.[].tag_name'`,
  download each release's asset for the host OS (`*macos-Qt.tar.xz` on
  macOS), extract, and give
  each its own `portable.txt`. Halve the range with one oracle that quotes
  a log line. Re-run the final pair to confirm it.
- Source bisect: `git bisect run` scripts exit 0 good, 1-124 bad, 125
  skip. Exit 125 for commits that do not build, or the bisect blames a
  build break. Use it only for oracles without a GUI, such as
  `ninja unittests` or a GS runner comparison, and use ccache.
