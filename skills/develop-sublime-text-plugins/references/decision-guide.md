# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Mutation needs edit token | Perform inside TextCommand or invoke command with serialized args. | Saving `Edit` for later. |
| Long I/O/analysis | Run on async worker, publish via host scheduling after revalidation. | Blocking UI thread. |
| Pure logic can be isolated | Unit test outside host plus host integration for API boundary. | Calling stubs a host test. |
| Resource shipped in package | Load through Sublime resource APIs and package-relative path. | Assuming writable filesystem path. |
| Plugin reload supported | Implement `plugin_unloaded` cleanup and idempotent load. | Global duplicate listeners/processes. |
| System Python feature differs | Use embedded runtime syntax/stdlib/dependency packaging. | Passing only system Python tests. |

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
