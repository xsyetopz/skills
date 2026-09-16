# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Only install speed/package management requested | Migrate install commands/lockfile after graph comparison; retain Node runtime/tests/build if requested. | Replacing every `node` invocation. |
| Test runner migration requested | Compare discovery, globals, isolation, mocks, snapshots, coverage, reporters, watch, and exit codes. | Assuming syntax compatibility equals behavior. |
| Native addon/install scripts present | Test target platforms and lifecycle policy in isolation. | Disabling scripts to get install success. |
| Resolved versions differ | Investigate lockfile/algorithm/constraint cause and require an authorized dependency change. | Accepting drift as migration noise. |
| CI cache keyed to old lockfile/tool | Update cache key/path only for migrated responsibility and prove cache miss correctness. | Sharing incompatible cache state. |

## Unresolved decisions

A material product, compatibility, public-interface, deployment, or policy
choice remains user-owned when repository evidence does not settle it. Present
the concrete alternatives and consequences. Routine implementation details that
do not change an external contract remain the agent's responsibility.

## Avoiding false precision

Use project-defined thresholds, limits, versions, and acceptance criteria. When
none exists, report measurements or uncertainty; do not invent a timeout,
reviewer count, confidence score, supported version, performance target, or
error budget and then treat it as a requirement.
