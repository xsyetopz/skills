# PCSX2 PS2 emulator: inspect guest execution

Implementation baseline: PCSX2 v2.8.2. Verify the target build before using
version-specific interfaces.

## Guest debugging

Enable **Tools → Show Advanced Settings**, then **Debug → Open Debugger**.
`-debugger` can request the debugger and paused boot from the command line. The
default R5900 layout targets the EE CPU; R3000 targets the IOP. A layout has a
target and individual dock windows can override it, so verify the target of the
actual memory/register pane. Layout customization is documented since v2.3.213.
[Debugger guide][ref-debugger-guide].

Before setting a breakpoint, identify the exact game/ELF revision, loaded module
and address domain. EE and IOP addresses are not interchangeable. Virtual CPU
addresses, physical RAM/device addresses, ELF offsets and host pointers describe
different things. Use load segments and a known instruction to map file data to
the guest; do not subtract a guessed constant across all regions. A host
debugger attached to PCSX2 observes emulator implementation state, not
automatically the guest symbol space.

Pause, inspect the PC and surrounding instructions, set a breakpoint at a known
function and continue to the intended trigger. For data discovery, search a
known value, change it in the guest, then filter by the new value. Repeat before
editing memory to rule out copies or unrelated counters. Conditional expressions
are hexadecimal by default: `a0==10` compares against 0x10, not decimal ten;
`[v1]` reads four bytes at the address in `v1`, while `[v1,1]` reads one byte.
Record CPU, address, width and condition with each finding.

Function stubbing replaces the function entry with a return and delay-slot NOP;
it is a mutation, not passive tracing. Restore it or restart from the baseline
before concluding that unmodified emulation behaves the same. Register edits and
memory writes need the same treatment.

## Symbols and overlays

PCSX2 imports symbols from the boot ELF by default and can import external
symbols conditionally for dynamically loaded code. Documented formats include
ELF `.symtab`/`.strtab`, MIPS `.mdebug` and SNDLL `.sndata`; the guide says
DWARF symbol tables are not currently supported. Do not promise source-level
DWARF debugging merely because an ELF has debug data.

A text `.sym` file can define hexadecimal addresses and labels. For example:

```text
00100000 entry_label
00130000 .byt:100
00140000 .wrd:100
```

The `.wrd` directive means two-byte elements in this format, unlike a four-byte
MIPS word; `.dbl` means four-byte elements. Use the format's documented
semantics rather than CPU terminology. For overlays, rerun appropriate analysis
when code changes and use function hashing/overwritten-symbol indications to
avoid stale names. Keep external symbol conditions and module revision with the
capture. [Symbol and expression documentation][source-1-1].

[source-1-1]: https://pcsx2.net/docs/advanced/debugger/

## Capture and GS replay

Use the configured screenshot/video/GS-dump actions at a named checkpoint and
record their bindings/settings; copied user profiles may change hotkeys. Verify
the actual output file and its contents. A GS dump captures graphics work for
replay, whereas video records presentation and a save state captures broader VM
state. Do not substitute one for another when defining the expected
guest-program result.

Use the local [source-build procedure](source-builds.md) when `pcsx2-gsrunner`
must be built. From the source tree's `pcsx2-gsrunner` directory, the upstream
scripts support this structural comparison:

```sh
python3 test_run_dumps.py -runner /case/base/pcsx2-gsrunner -dumpdir \
  /case/results/base -gsdir /fixtures/gs -renderer vulkan
python3 test_run_dumps.py -runner /case/new/pcsx2-gsrunner -dumpdir \
  /case/results/new -gsdir /fixtures/gs -renderer vulkan
python3 test_check_dumps.py -baselinedir /case/results/base -testdir \
  /case/results/new /case/results/changes.html
```

In v2.8.2, the script creates one child directory per dump directly below
`-dumpdir`; the website's extra runner-basename directory does not match this
pinned script. Use fresh output directories: an existing per-dump directory is
skipped, even if a previous run failed. The script suppresses subprocess output
and does not turn every runner failure into a failing script exit, so inspect
each `emulog.txt` and expected frame set. `-parallel 4` runs multiple dumps
concurrently, useful for throughput but unsuitable for interpreting isolated
performance latency. Renderer choices include `auto`, `dx11`, `dx12`, `gl`,
`vulkan` and `sw`; choose one supported by the host. Hardware-hack selection
uses `-renderhacks`, with codes such as `af` for AutoFlush and `cpufb` for CPU
framebuffer conversion; keep the same selection on both sides unless it is the
experimental variable. Sources: [GS dump guide][ref-gs-dump-guide], [runner
script][source-2-1], [comparison script][source-2-2].

The comparison hashes complete PNG file bytes, not decoded pixels. Different
compression or metadata can therefore report a difference without changed
rendering. It walks baseline frames only: an empty baseline can pass, and extra
test frames are ignored. Validate expected nonempty frame sets on both sides
before accepting success. A changed result retains an HTML report; an unchanged
result deletes it. The report references local images and the source tree's
`comparer.css`/`comparer.js` through absolute file URLs, so it is not a
standalone portable artifact. Preserve those assets/paths or adapt packaging
deliberately.

Check per-dump completion, missing outputs and child-process failures before
interpreting differences. Replay does not reproduce EE/IOP execution, gameplay
inputs or disc timing. For a full-game claim, run a representative guest
sequence independently.

[source-2-1]:
https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-gsrunner/test_run_dumps.py
[source-2-2]:
https://github.com/PCSX2/pcsx2/blob/v2.8.2/pcsx2-gsrunner/test_check_dumps.py

## Reproducibility record

Keep emulator build/hash, BIOS/media/ELF hashes, guest checkpoint, copied
memory-card/state identity, settings, patches, textures, renderer/resolution,
host GPU/driver and input sequence. Save states can change compatibility across
builds; prefer cold boot or an in-game save when comparing incompatible states.
Establish a baseline with enhancements disabled when they may explain the
defect, then change one variable.

Report process launch, renderer initialization and guest-program correctness
check separately. Record timeout/forced termination, logging overhead and host
load. Verify guest correctness at the recorded checkpoint.

[ref-debugger-guide]: https://pcsx2.net/docs/advanced/debugger/
[ref-gs-dump-guide]: https://pcsx2.net/docs/advanced/gsdumprunner/
