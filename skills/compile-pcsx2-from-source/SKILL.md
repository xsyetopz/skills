---
name: compile-pcsx2-from-source
description: >-
  Compile and verify a PCSX2 executable from a pinned source checkout with
  platform dependencies and packaged-resource evidence. Use when building
  PCSX2 from source; not for release installation, game operation, guest
  debugging, patches, or texture packs.
---

# Compile PCSX2 from Source

Select this workflow automatically when the task matches its description.
Selection supplies guidance only; it does not authorize operations beyond the
user's request.

Use a separate checkout and build directory at a recorded revision. Read
[source compilation](references/source-builds.md) for Linux, Windows, macOS, GS
runner, and packaged-resource requirements.

Do not replace the installed emulator. Record toolchain, dependency revisions,
configuration, local patches, and artifact hash. Verify compilation, packaged
resources, launch, and a guest checkpoint separately.
