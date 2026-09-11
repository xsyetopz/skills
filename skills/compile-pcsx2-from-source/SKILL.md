---
name: compile-pcsx2-from-source
description: >-
  Use only when explicitly invoked by name. Compile a PCSX2 executable from a
  pinned source checkout with platform dependencies and reproducible packaged-
  resource evidence. Excludes installing release binaries, game launches, guest
  debugging, patches, and texture packs.
---

# Compile PCSX2 from Source

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

Use a separate checkout and build directory at a recorded revision. Read
[source compilation](references/source-builds.md) for Linux, Windows, macOS, GS
runner, and packaged-resource requirements.

Do not replace the installed emulator. Record toolchain, dependency revisions,
configuration, local patches, and artifact hash. Verify compilation, packaged
resources, launch, and a guest checkpoint separately.
