# Extension design decisions for Sublime Python Plugin

Use this guide after inspecting the request and target system for Sublime Text
plugin. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Mutation needs edit token | Perform inside TextCommand or invoke command with serialized args. | Saving `Edit` for later. |
| Long I/O/analysis | Run on async worker, publish via host scheduling after revalidation. | Blocking UI thread. |
| Pure logic can be isolated | Unit test outside host plus host integration for API boundary. | Calling stubs a host test. |
| Resource shipped in package | Load through Sublime resource APIs and package-relative path. | Assuming writable filesystem path. |
| Plugin reload supported | Implement `plugin_unloaded` cleanup and idempotent load. | Global duplicate listeners/processes. |
| System Python feature differs | Use embedded runtime syntax/stdlib/dependency packaging. | Passing only system Python tests. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
Sublime Text plugin remains user-owned when repository evidence does not settle
it. Present concrete alternatives and consequences. Resolve routine internal
details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
Sublime Text plugin. If none exists, report measurements or uncertainty. Do not
invent a timeout, reviewer count, confidence score, target, or error budget and
then treat it as a requirement.
