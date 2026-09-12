---
name: operate-pcsx2
description: >-
  Construct or run isolated PCSX2 PS2 launches, debug guest behavior, and
  verify captures, texture replacements, or patches against a known build
  and game revision. Use when operating PCSX2 or diagnosing a PlayStation 2
  guest; not for compiling the emulator or DuckStation tasks.
---

# Operate PCSX2

Select this workflow automatically when the task matches its description.
Selection supplies guidance only; it does not authorize operations beyond the
user's request.

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
