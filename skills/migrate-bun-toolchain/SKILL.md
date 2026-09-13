---
name: migrate-bun-toolchain
description: >-
  Adopt Bun for package management, runtime, tests, or bundling, or migrate a
  project to a requested Bun version. Not for Bun performance tuning.
---

# Migrate Bun Toolchain

Identify the current and requested target version and the surfaces being
changed: installation, runtime, scripts, tests, bundling, or deployment. Package
manager adoption is not permission to replace the runtime or test runner. A
Bun-only version upgrade does not require adopting more Bun APIs.

Read [version and installation](references/migration-decisions.md) for pins,
lockfile migration, dependency lifecycle trust, registries, and workspaces. Read
[runtime and tooling](references/runtime-and-tooling.md) only when the runtime,
tests, or bundler changes.

Use the latest stable release for an unspecified target, verified from upstream
and the installed executable. Preserve an explicit target. Change every consumer
of the migrated surface, not unrelated tools. Let Bun generate its lockfile and
compare resolved dependencies before retiring an old installer's lockfile. Keep
Node for supported scripts or dependencies that still require it.

Validate the affected frozen install, scripts, type check, tests, and deployed
or packaged entrypoint using the target executable. Bun transpilation does not
type-check. Report observed compatibility differences and any unverified
platforms. Do not turn a migration into an application rewrite or scaffolding
task.
