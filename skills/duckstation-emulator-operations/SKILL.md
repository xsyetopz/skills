---
name: duckstation-emulator-operations
description:
  Construct DuckStation commands or perform isolated PS1 emulation, debugging,
  capture, and reproducibility work using verified build-specific interfaces.
---

# DuckStation Emulator Operations

Identify the requested build and operation: command construction, emulation,
debugging, capture, textures, or source build.

Read [commands and isolation][ref-1] before constructing launches. Options use
single hyphens. Use a positional executable for standalone boot: `-exe FILE`
alone loses autoboot in the examined parser.

The [command builder](scripts/build_command.py) prints POSIX shell text without
launching. Use `--boot` for a standalone PS-X executable. Construct
disc-plus-override directly.

Use a disposable portable copy and verify its resolved data directory before
runtime work. Copy fixtures and saves into that tree. Label guest
virtual/physical addresses, file offsets, and host pointers explicitly.

Read [debugging and capture][ref-2] for GDB, PCDrv, checkpoints, and replay.
Read [textures and builds][ref-3] for replacements, patches, and compilation.

Record build/hash, command, fixtures, settings, and guest outcome. Record forced
termination. `-nogui` still requires host services; an exit code alone does not
establish guest correctness.

[ref-1]: references/commands-and-isolation.md
[ref-2]: references/debugging-and-evidence.md
[ref-3]: references/textures-and-builds.md
