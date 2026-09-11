---
name: compile-duckstation-from-source
description: >-
  Use only when explicitly invoked by name. Compile a DuckStation executable
  from a pinned source checkout with platform dependencies and reproducible
  artifact evidence. Excludes installing release binaries, running games, guest
  debugging, patches, and texture authoring.
---

# Compile DuckStation from Source

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

Pin the source revision and dependency-pack hashes in a separate checkout and
build directory. Read [source compilation](references/source-builds.md) for
platform requirements and verification stages.

Do not replace the installed emulator. Record compiler, dependency hashes,
configuration, local patches, and executable hash. Treat compilation, launch,
renderer initialization, and guest progress as separate checks.
