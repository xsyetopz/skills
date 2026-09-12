---
name: compile-duckstation-from-source
description: >-
  Compile and verify a DuckStation executable from a pinned source checkout
  with platform dependencies and reproducible artifact evidence. Use when
  building DuckStation from source; not for release installation, game
  operation, guest debugging, patches, or textures.
---

# Compile DuckStation from Source

Select this workflow automatically when the task matches its description.
Selection supplies guidance only; it does not authorize operations beyond the
user's request.

Pin the source revision and dependency-pack hashes in a separate checkout and
build directory. Read [source compilation](references/source-builds.md) for
platform requirements and verification stages.

Do not replace the installed emulator. Record compiler, dependency hashes,
configuration, local patches, and executable hash. Treat compilation, launch,
renderer initialization, and guest progress as separate checks.
