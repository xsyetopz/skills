---
name: compile-pcsx2-from-source
description: >-
  Build and verify PCSX2 from a pinned source checkout with packaged-resource
  evidence. Excludes game operation and guest debugging.
---

# Compile PCSX2 from Source

Use a separate checkout and build directory at a recorded revision. Read
[source compilation](references/source-builds.md) for Linux, Windows, macOS, GS
runner, and packaged-resource requirements.

Do not replace the installed emulator. Record toolchain, dependency revisions,
configuration, local patches, and artifact hash. Verify compilation, packaged
resources, and process launch. Run a guest checkpoint only when guest execution
is part of the request.
