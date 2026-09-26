# Debug the guest, the renderer, and the host process

Cards for the built-in debugger, symbols, the GS renderer as an oracle, GS
dumps, and lldb on the emulator process. Guest-side cards cannot run here,
because every VM boot needs a PS2 BIOS and none may be obtained. Their
examples are upstream procedures, each with the log line or artifact that
proves the step happened. Sources: the [debugger guide][debugger], the
[GS dump runner guide][gsrunner], and commit `2c804670`.

## Contents

- Debugger layouts and breakpoints
- Debugger expressions
- Symbol import and .sym files
- Function stubbing
- No GDB stub
- GS renderer choice with the software renderer as oracle
- GS dump capture
- GS dump replay comparison
- lldb on host crashes

## Debugger layouts and breakpoints

**Definition.** The debugger opens from **Debug > Open Debugger** once
**Tools > Show Advanced Settings** is ticked, or from the command line
with `-debugger`, which breaks on the entry point. The `R5900` layout
targets the Emotion Engine (EE) and the `R3000` layout the IOP. **Set
Target** overrides a dock window's layout target. Layouts exist since
v2.3.213. The breakpoint dialog has these types:

- **Execute**, at an address.
- **Memory**, with Read, Write or Change and a Size.

Both types take an optional **Condition** expression. At `v2.9.84` the
dialog also has **Log When Hit** with a format such as `ra={ra}
val={[sp,4]}`, **Continue on hit**, and **Max Hits**. `v2.8.2` lacks all
three; they came with commit `0862e3e`.

**Use when.**

- You need the guest instruction or data access that changes a value.
  Search memory for the value, filter after it changes, then set a
  **Memory > Write** breakpoint on the surviving address.

**Do not use when.**

- The question is about the host emulator: a crash, a hang in Qt, or a
  renderer thread. Use lldb.
- The address came from an ELF file offset or a host pointer. EE virtual
  addresses, IOP addresses, ELF offsets and host pointers are different
  spaces.

**Example.** Not runnable here (needs a BIOS). The procedure for a
homebrew ELF:

```text
PCSX2 -datapath CASE/data -logfile CASE/emu.log -debugger -elf test.elf
Debugger: R5900 layout > Memory Search: Value 64, type 4 bytes, Search
Guest changes the value to 63 > Value 63 > Filter Search -> 0x00123450
Breakpoints > New: Type Memory, Write, Address 00123450, Size 4,
  Condition v0==3f
Run > breaks at the store instruction; Disassembly shows the PC
```

**Cost removed.** Guessing which instruction writes a value. Count:
candidate addresses left after each filter (target 1).

**Verify.**

1. The Breakpoints list shows the hit count rising, and the PC at the break
   is a store to the target address.
1. Delete the breakpoint and run to the same point: the value changes
   without a stop, so the breakpoint did not cause the change.

## Debugger expressions

**Definition.** Address, condition, and go-to fields take expressions.
Bare integers are hexadecimal, so `10` means 0x10. `0o` or a trailing `o`
means octal. Registers use their names (`v0`, `a0`). `[a]` reads 4 bytes
and `[a,n]` reads 1, 2, 4 or 8 bytes. C operators and `a?b:c` work.

**Use when.**

- Writing breakpoint conditions or computing an address from a register.

**Do not use when.**

- Writing decimal constants: `a0==10` compares with sixteen, not ten.

**Example.** Values from the [guide][debugger]:

```text
100       -> 0x100 (256)
[v1]      -> 4-byte value at the address in v1
[v1,1]    -> 1-byte value at the address in v1
a0==10    -> 1 if a0 is 0x10 (16)
(1+1)*2   -> 4
```

**Cost removed.** Conditions that never fire because of the base. Count:
conditions with decimal literals meant as decimal (target 0).

**Verify.**

1. Type the expression into **Go to** in the Memory view; the resolved
   address matches.
1. The breakpoint's hit count is greater than 0 once the condition is met.

## Symbol import and .sym files

**Definition.** Analysis imports symbols from the boot ELF's
`.symtab`/`.strtab`, `.mdebug` (since v2.1.113), and SNDLL `.sndata`
(since v2.1.113), but not DWARF. Extra files can be imported, each with an
optional condition expression. A `.sym` text file has one
symbol per line in hexadecimal: `<address> <name>[:<size>]`, or a data
directive. `.byt` and `.asc` have 1-byte elements, `.wrd` 2-byte, and
`.dbl` 4-byte. These sizes differ from MIPS word (4) and doubleword (8).

**Use when.**

- The homebrew ELF is stripped, or code is loaded at runtime and needs
  names.

**Do not use when.**

- You expect source-level debugging from DWARF line tables, which PCSX2
  cannot use.

**Example.** A `.sym` file for a homebrew fixture:

```text
00100000 entry_label
00120000 main_loop:100
00130000 .byt:100
00140000 .wrd:100
00150000 .dbl:100
```

**Cost removed.** Reading raw addresses. Count: named functions in the
Symbol Tree after analysis.

**Verify.**

1. After **Analysis Options > Import Symbols** and a rerun, `main_loop`
   appears in the Functions tree at `00120000`.
1. With **Gray Out Symbols For Overwritten Functions** on, overlays that
   replace code show their stale names greyed.

## Function stubbing

**Definition.** **Stub (NOP) Function** in the Disassembly view replaces a
function's first two instructions with `jr ra` and `nop`. **Restore
Function** puts the originals back. This writes guest memory; it is not a
trace.

**Use when.**

- Testing what a function does, for example whether the player still takes
  damage with a suspected damage routine stubbed.

**Do not use when.**

- The caller uses the return value: `v0` then holds a stale value.
- The run will serve as evidence about unmodified behaviour.

**Example.** Not runnable here.

```text
Disassembly > right-click function at 00120000 > Stub (NOP) Function
Observe behaviour > Restore Function > restart the VM for baselines
```

**Cost removed.** Reading a function's code to guess its purpose. Count:
functions ruled in or out per hypothesis.

**Verify.**

1. After stubbing, the Disassembly view shows `jr ra` and `nop` at the
   entry.
1. After **Restore Function**, the original two instructions return, and a
   fresh boot reproduces the baseline.

## No GDB stub

**Definition.** Commit `2c804670` has no GDB remote stub:
`rg -il gdb pcsx2 pcsx2-qt common` finds no stub source. Guest debugging
uses the Qt debugger only; `gdb` and `lldb` attach to the host process, not
the PS2 guest.

**Use when.**

- Someone proposes `target remote :port` or an IDE's MIPS gdb debugging
  against PCSX2.

**Do not use when.**

- A PCSX2 fork or newer commit adds a stub: re-run the check below.

**Example.** Executed on the pinned checkout:

```sh
rg -il 'gdb' pcsx2 pcsx2-qt common | head
```

It prints nothing.

**Cost removed.** Configuring a remote debugger that cannot connect.
Count: the command above printing 0 files.

**Verify.**

1. The `rg` command prints nothing on the checkout under test.
1. `-help` of the binary under test lists no gdb or port option.

## GS renderer choice with the software renderer as oracle

**Definition.** `[EmuCore/GS] Renderer` in `PCSX2.ini` selects the
renderer (`GSRendererType` in `pcsx2/Config.h`):

- `-1` Auto
- `3` DX11
- `15` DX12
- `12` OpenGL
- `14` Vulkan
- `17` Metal
- `13` Software
- `11` Null

Software draws on the CPU, independent of the GPU driver, upscaling, and
hardware fixes. The default hotkey `F9` toggles software and hardware
(`ToggleSoftwareRendering`). A per-game INI in `gamesettings/` can
override the global value.

**Use when.**

- Deciding whether a graphics bug belongs to the hardware renderer or
  driver, or to the core or guest.

**Do not use when.**

- Measuring performance: software rendering is CPU-bound, and its speed
  says nothing about the hardware path.
- The artefact comes from upscaling: software renders at native
  resolution only.

**Example.** Not runnable here. The decision table:

| Software | Hardware | Owning layer |
| --- | --- | --- |
| correct | wrong | HW renderer, texture cache, driver, or HW fixes |
| wrong | wrong | GS emulation, EE/VU core, or the guest itself |
| correct | correct at 1x, wrong upscaled | upscaling path |

```ini
[EmuCore/GS]
Renderer = 13
```

**Cost removed.** Fixes aimed at the wrong layer. Count: bug reports
without a software-renderer result (target 0).

**Verify.**

1. `grep '^Renderer' DATA/PCSX2/inis/PCSX2.ini` shows the intended value,
   and the game's `gamesettings/*.ini` does not override it.
1. Captures of the same scene under both renderers differ only where the
   bug is.

## GS dump capture

**Definition.** A GS dump records the GS register and memory traffic of
one frame (**Tools > Save Single Frame GS Dump**, default `Shift+F8`) or
of several frames (`Ctrl+Shift+F8`) into `snaps/`. `GSDumpCompression`
sets the compression. Per the [reporting guide][identify], graphics
settings do not affect the dump.

**Use when.**

- Reporting or regression-testing a graphics bug visible on screen.

**Do not use when.**

- The bug is in timing, audio, input, or CPU: the dump holds none of
  that.

**Example.** Not runnable here.

```text
Reach the frame where the glitch is visible > Shift+F8
ls DATA/PCSX2/snaps/*.gs*
```

**Cost removed.** Rebooting the game for every renderer experiment.
Observable: one dump file per capture.

**Verify.**

1. The new dump file is in `snaps/`; record its size and time.
1. Replaying it with the GS runner shows the glitch.

## GS dump replay comparison

**Definition.** In `pcsx2-gsrunner/`, `test_run_dumps.py -runner R
-gsdir DUMPS -dumpdir OUT [-renderer X] [-renderhacks af,cpufb]
[-parallel N]` runs each dump into `OUT/<dumpname>/` with `-loop 2
-surfaceless`. `test_check_dumps.py -baselinedir A -testdir B
report.html` compares the results. At `2c804670`, four script behaviours
matter:

- An existing `OUT/<dumpname>` is skipped.
- Runner output is discarded (sent to `DEVNULL`).
- Frames are compared by MD5 of the PNG file bytes.
- Only frames present in the baseline are compared.

The guide's `-baselinedir …/baseline/pcsx2-gsrunner` has an extra
directory level that the script does not create.

**Use when.**

- Checking that a renderer change alters no frames on a dump corpus.

**Do not use when.**

- The baseline directory is empty: the check then passes vacuously.

**Example.** Not runnable here: no runner binary and no dumps.

```sh
python3 test_run_dumps.py -runner base/pcsx2-gsrunner -gsdir dumps \
  -dumpdir out/base -renderer sw
python3 test_run_dumps.py -runner new/pcsx2-gsrunner -gsdir dumps \
  -dumpdir out/new -renderer sw
find out/base -name '*_frame*.png' | wc -l
python3 test_check_dumps.py -baselinedir out/base -testdir out/new \
  out/changes.html
```

**Cost removed.** Manual screenshot comparison. Count: frames reported
different.

**Verify.**

1. Both `find … | wc -l` counts are non-zero and equal, and no
   `out/*/<dump>/emulog.txt` has `Error` lines.
1. Every run used a fresh `-dumpdir` directory, because the script skips
   any per-dump directory that already exists.

## lldb on host crashes

**Definition.** lldb attaches to the PCSX2 process and debugs host code,
not the guest. The official macOS release has the hardened runtime
(`flags=0x10000(runtime)`) without `get-task-allow`, so lldb cannot attach
to it. PCSX2 raises `EXC_BAD_ACCESS` (SIGBUS or SIGSEGV) on purpose for
its fastmem page-fault handler (`common/Darwin/DarwinMisc.cpp`), so lldb
must pass those to the process; lldb's
`platform.plugin.darwin.ignored-exceptions` setting
([property source][lldb-prop]) does this. On Linux, use `process handle
SIGSEGV -n false -p true -s false`.

**Use when.**

- The emulator itself crashes or hangs, not the guest.

**Do not use when.**

- The guest misbehaves but the emulator keeps running: use the PCSX2
  debugger.

**Example.** Executed on a scratch copy of `v2.8.2` with its signature
removed (the copy is unsigned; never do this to the user's install):

```sh
cp -R PCSX2-v2.8.2.app scratch.app
codesign --remove-signature scratch.app/Contents/MacOS/PCSX2
LLDB=/Applications/Xcode.app/Contents/Developer/usr/bin/lldb
"$LLDB" --batch \
  -o 'settings set platform.plugin.darwin.ignored-exceptions EXC_BAD_ACCESS' \
  -o 'b QtHost::PrintCommandLineVersion' -o run -o 'bt 4' -o kill \
  -- scratch.app/Contents/MacOS/PCSX2 -version
```

Observed: on the signed original, `error: process exited with status -1
(lost connection)`. On the copy, the breakpoint resolved and `bt` showed
frame #1 as `main + 11282` in PCSX2. The release keeps local symbols but
ships no dSYM, so frames have names but no line numbers; for line numbers,
build `Debug` or `Devel` from source.

**Cost removed.** Attach failures on signed builds (executed above) and
spurious stops on fastmem faults. The second is inferred from the source
and the lldb property text; no VM ran here to produce a fastmem fault.
Observable: lldb reaches the real crash frame instead of stopping at the
first `EXC_BAD_ACCESS`.

**Verify.**

1. `codesign -d --entitlements - APP` shows whether
   `com.apple.security.get-task-allow` is present; without it, expect the
   `lost connection` failure.
1. `bt` shows `PCSX2` frames with symbol names at the stop.

[debugger]: https://pcsx2.net/docs/advanced/debugger/
[gsrunner]: https://pcsx2.net/docs/advanced/gsdumprunner/
[identify]: https://pcsx2.net/docs/troubleshooting/identify/
[lldb-prop]: https://github.com/llvm/llvm-project/blob/main/lldb/source/Plugins/Platform/MacOSX/PlatformMacOSXProperties.td
