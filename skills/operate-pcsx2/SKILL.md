---
name: operate-pcsx2
description: >-
  Run isolated PCSX2 launches and diagnose PS2 guest behavior, captures,
  texture replacements, or patches. Not for compiling PCSX2.
---

# Operate PCSX2

Resolve the exact emulator build, media/executable revision and requested guest
checkpoint. Preserve an unchanged baseline and use an isolated data tree with
copied fixtures and saves. Verify the resolved paths rather than assuming a
changed working directory isolates the installation.

Read only the relevant reference:

- [Commands and isolation](references/commands-and-data-paths.md): launches,
  executable overrides, state files and the non-executing command builder.
- [Debugging and evidence](references/debugging-and-evidence.md): guest/host
  address domains, EE/IOP symbols, overlays, captures and GS replay.
- [Textures and patches](references/patches-and-textures.md): dump identities,
  replacement matching, PNACH timing and dynamic code patches.

The [command builder](scripts/build_command.py) prints POSIX shell text and
never launches. Use argument arrays for execution. Do not equate generating a
command with permission to run or mutate user state.

Compare the same checkpoint before and after a change. Record build/hash,
command, settings, fixtures, observed guest result and forced termination.
Process exit, renderer initialization and GPU replay do not independently prove
gameplay correctness. Source compilation remains a separate toolchain task.
