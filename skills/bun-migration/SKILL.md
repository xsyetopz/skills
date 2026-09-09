---
name: bun-migration
description:
  Migrate the requested Bun version, package-management, or runtime/tooling
  surfaces while preserving project compatibility. Excludes unrelated formatter
  adoption and ordinary dependency updates.
---

# Bun Migration

Identify the current and target Bun versions and affected surfaces: pins,
installation, runtime, scripts, tests, or bundling. Use the latest stable
baseline for an unspecified target. Check target-specific documentation when
that version differs.

Read [migration decisions][ref-1] for pins, lockfiles, registries, lifecycle
scripts, and workspaces. Read [runtime and tooling][ref-2] for Node
compatibility, test-runner changes, and builds.

Change every consumer of the migrated surface. Generate lockfiles with Bun and
compare dependency resolution before retiring the old lockfile. Keep a lockfile
only while a supported installer consumes it.

Bun transpilation does not type-check. Run the affected frozen installation,
scripts, type checks, tests, or packaged entrypoint with the target version.
Resolve failures before completing the switch. A Bun migration does not require
unrelated formatter or compiler changes.

[ref-1]: references/migration-decisions.md
[ref-2]: references/runtime-and-tooling.md
