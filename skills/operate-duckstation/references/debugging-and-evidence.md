# Debugging and reproducibility

Implementation baseline: DuckStation commit
`cbe7951be624a3fd69c81858647a8f84e4a1d06b`. Verify the target build before using
version-specific interfaces.

## Define the guest checkpoint

Record executable version/hash, source commit if known, host OS/CPU/GPU/driver,
BIOS/media/executable hashes, renderer, internal resolution, CPU execution mode,
PGXP/enhancements, controller mapping, memory-card policy and input sequence.
Name the checkpoint: cold boot, in-game save or emulator state. States may
depend on build/settings and contain transient device/CPU state; a cold boot or
copied in-game save is a stronger cross-version comparison when state
compatibility is uncertain.

Use an observable outcome: a known PC reached, expected guest memory value,
screen at a named scene, output file or completed input sequence. Use an in-game
checkpoint for gameplay claims. Capture an unchanged baseline, modify one
suspected variable and reproduce the same sequence. Disable relevant
enhancement/patch/texture changes before attributing an issue to core emulation.

## CPU debugger and address domains

Pause at a known instruction before trusting symbols or breakpoints. Keep these
domains explicit:

- Guest executable file offset: where bytes reside in a PS-X EXE/ELF; it is not
  automatically the load address.
- Guest virtual CPU address: instruction/data address used by the emulated MIPS
  CPU, including mapped aliases.
- Guest physical RAM, scratchpad, BIOS or device address: different memory
  regions with different behavior.
- Host pointer: address in the emulator process, meaningful to a host debugger
  rather than guest symbols.

Use the executable's load metadata and a known instruction to establish a
mapping; do not apply a blanket offset subtraction across RAM, BIOS and devices.
Overlays, runtime relocation and regional revisions can invalidate a symbol map.
Check breakpoints after those transitions. Memory writes or register edits alter
the experiment; restart from the saved baseline before a compatibility claim.

## GDB remote interface

The examined desktop source loads these INI settings; edit only an isolated
configuration while its process is stopped:

```ini
[Debug]
EnableGDBServer = true
GDBServerPort = 2345
```

The default port is 2345 and the server binds IPv4 loopback `127.0.0.1`. Choose
another free port explicitly if necessary. Start the guest, then connect a GDB
build that supports the guest MIPS target, with symbols for that guest
executable:

```gdb
file /fixtures/test.elf
target remote 127.0.0.1:2345
info registers
x/4i $pc
break main
continue
```

`main` requires a matching symbol; PS-X EXE files commonly need separately
supplied ELF symbols. The implementation supports register/memory read and
write, continue, single-step, breakpoint packets and target/memory-map queries.
It is not a promise of all GDB remote features. If attachment fails, separate
disabled configuration, port collision, wrong GDB architecture and missing
running guest. Keep the debugger local; attaching a native host debugger instead
observes a different address domain. Sources: [settings][source-2-1],
[defaults][source-2-2], [GDB implementation][source-2-3].

[source-2-1]:
  https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/settings.cpp
[source-2-2]:
  https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/settings.h
[source-2-3]:
  https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/gdb_server.cpp

## PCDrv host-file fixtures

```ini
[PCDrv]
Enabled = true
EnableWrites = false
Root = /case/pcdrv
```

PCDrv services guest file operations against the configured host root. Read-only
is the initial choice; enable writes only for an output fixture that needs them.
The implementation canonicalizes paths and checks the root prefix, but
explicitly does not claim a security sandbox. Use an isolated directory
containing only intended fixtures. It limits open handles, rejects directory
creation through this interface, and returns guest errors for invalid
paths/handles or disallowed writes. A guest PCDrv error is distinct from a
failed emulation boot. Reset/shutdown closes tracked handles. Source: [PCDrv
implementation][source-3-1].

[source-3-1]:
  https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/pcdrv.cpp

## Logs and capture

Enable file logging for the isolated run through its logging settings and retain
the path reported by the application. Select the log level for the failure.
Record verbose-logging overhead in timing comparisons. Early-console output
helps diagnose failures before normal logging is ready. [Logging
guidance][source-4-2].

The default screenshot hotkey is F10; bindings may have been changed. The
examined hotkey table also exposes audio/video capture toggles and
single-/multi-frame GPU trace actions. Assign an unused binding in the isolated
profile when none is assigned. Single-frame trace starts a one-frame recording;
the multi-frame action starts on press and stops on release. Record capture
settings and confirm the output file exists and opens before claiming success.
[Hotkey implementation][source-4-3].

The boot implementation accepts `.psxgpu`, `.psxgpu.zst` and `.psxgpu.xz` for
GPU replay via a positional path. Replay isolates graphics command processing;
it does not repeat the full CPU/input workload. Use screenshots for rendered
checkpoints, video for sequences, and GPU dumps for graphics replay. [Boot
dispatch][source-4-1].

Report the exact command, checkpoint, observed result and any forced
termination. Report only observed stages: command validation, process launch,
renderer initialization, and guest checkpoint.

[source-4-1]:
  https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/system.cpp
[source-4-2]: https://github.com/stenzek/duckstation/wiki/Enabling-Logging
[source-4-3]:
  https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/hotkeys.cpp
