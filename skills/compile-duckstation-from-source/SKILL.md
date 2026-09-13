---
name: compile-duckstation-from-source
description: >-
  Build and verify DuckStation from a pinned source checkout with reproducible
  artifact evidence. Excludes game operation and guest debugging.
---

# Compile DuckStation from Source

Build in a separate checkout and build directory; do not replace the installed
emulator. Record the requested source revision, target platform, and
dependency-pack hashes. Before building, read the target platform's procedure
in [source compilation](references/source-builds.md).

Record compiler, configuration, local patches, and executable path/hash. Verify
the build and process launch, reporting the first failed stage and diagnostic.
Check renderer initialization and guest progress only when guest execution is
requested; neither follows from a successful build.
