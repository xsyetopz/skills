---
name: compile-pcsx2-from-source
description: >-
  Build and verify PCSX2 from a pinned source checkout with packaged-resource
  evidence. Excludes game operation and guest debugging.
---

# Compile PCSX2 from Source

Build in a separate checkout and build directory at a recorded revision; do not
replace the installed emulator. Before building, read the target platform's
procedure and packaged-resource requirements in
[source compilation](references/source-builds.md). Use its GS runner procedure
only when graphics replay is requested.

Record toolchain, dependency revisions,
configuration, local patches, and artifact hash. Verify compilation, packaged
resources, and process launch. Run a guest checkpoint only when guest execution
is part of the request. Report the artifact path and the first failed stage and
diagnostic, if any.
