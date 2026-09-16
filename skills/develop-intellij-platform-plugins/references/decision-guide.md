# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Operation reads PSI synchronously | Use the appropriate read action or platform nonblocking API. | Unsynchronized background PSI access. |
| Operation modifies documents/PSI | Use write command/action with undo semantics. | Direct mutation from pooled thread. |
| Long computation follows PSI read | Capture stable data, compute outside lock, then revalidate before write. | Holding read lock for long work. |
| Index-dependent feature during indexing | Declare dumb-aware only if truly safe or defer until smart mode. | Catching index exceptions as fallback. |
| Project-scoped resource | Bind to project/service disposable and cancel on disposal. | Static global singleton. |
| Compatibility range changes | Test actual target IDEs and APIs before editing since/until build. | Broadening range to make publication possible. |

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
