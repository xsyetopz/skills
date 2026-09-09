---
name: pcsx2-emulator-operations
description:
  Construct PCSX2 commands or perform isolated PS2 ELF/disc, debugging, capture,
  and reproducibility work using verified build-specific interfaces.
---

# PCSX2 Emulator Operations

Identify the build and requested operation: command construction, ELF/disc boot,
debugging, capture, patches, textures, or source build.

Read [commands and data paths][ref-1] before constructing launches. Use
single-hyphen options and positional disc images. `-disc` selects a physical
drive. Pair `-statefile` with a boot target in the examined parser.

The [command builder](scripts/build_command.py) prints POSIX shell text without
launching. Construct state-file-plus-image and ELF-plus-image combinations
directly.

Use `-datapath` with a disposable directory and copied fixtures. Do not combine
it with `-portable`, which overrides it. Check copied settings for paths to
ordinary saves.

Read [debugging and capture][ref-2] for EE/IOP, symbols, and GS replay; [patches
and textures][ref-3] for modifications;
[source builds](references/source-builds.md) for compilation.

Record build/hash, command, fixture identity, settings, and guest outcome.
Record forced termination. `-nogui` retains Qt/rendering dependencies;
configuration success does not establish guest progress.

[ref-1]: references/commands-and-data-paths.md
[ref-2]: references/debugging-and-evidence.md
[ref-3]: references/patches-and-textures.md
