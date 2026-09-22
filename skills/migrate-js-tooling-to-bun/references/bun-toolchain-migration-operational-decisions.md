# Operational decisions for Bun Toolchain Migration

Use this guide after inspecting the request and target system for Bun migration.
It selects an evidence path; it does not grant permission for an external write
or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Only install speed/package management requested | Migrate install commands/lockfile after graph comparison; retain Node runtime/tests/build if requested. | Replacing every `node` invocation. |
| Test runner migration requested | Compare discovery, globals, isolation, mocks, snapshots, coverage, reporters, watch, and exit codes. | Assuming syntax compatibility equals behavior. |
| Native addon/install scripts present | Test target platforms and lifecycle policy in isolation. | Disabling scripts to get install success. |
| Resolved versions differ | Investigate lockfile/algorithm/constraint cause and require an authorized dependency change. | Accepting drift as migration noise. |
| CI cache keyed to old lockfile/tool | Update cache key/path only for migrated responsibility and prove cache miss correctness. | Sharing incompatible cache state. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
Bun migration remains user-owned when repository evidence does not settle it.
Present concrete alternatives and consequences. Resolve routine internal details
that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the Bun
migration. If none exists, report measurements or uncertainty. Do not invent a
timeout, reviewer count, confidence score, target, or error budget and then
treat it as a requirement.
