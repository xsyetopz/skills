---
name: compile-duckstation-from-source
description: >-
  Build and verify DuckStation from a pinned source checkout with reproducible
  artifact evidence. Excludes game operation and guest debugging.
---

# Compile DuckStation from Source

Pin the source revision and dependency-pack hashes in a separate checkout and
build directory. Read [source compilation](references/source-builds.md) for
platform requirements and verification stages.

Do not replace the installed emulator. Record compiler, dependency hashes,
configuration, local patches, and executable hash. Treat compilation, launch,
renderer initialization, and guest progress as separate checks.
