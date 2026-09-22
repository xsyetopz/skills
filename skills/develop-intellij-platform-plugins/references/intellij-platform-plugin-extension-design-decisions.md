# Extension design decisions for Intellij Platform Plugin

Use this guide after inspecting the request and target system for IntelliJ
Platform plugin. It selects an evidence path; it does not grant permission for
an external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Operation reads PSI synchronously | Use the appropriate read action or platform nonblocking API. | Unsynchronized background PSI access. |
| Operation modifies documents/PSI | Use write command/action with undo semantics. | Direct mutation from pooled thread. |
| Long computation follows PSI read | Capture stable data, compute outside lock, then revalidate before write. | Holding read lock for long work. |
| Index-dependent feature during indexing | Declare dumb-aware only if truly safe or defer until smart mode. | Catching index exceptions as fallback. |
| Project-scoped resource | Bind to project/service disposable and cancel on disposal. | Static global singleton. |
| Compatibility range changes | Test actual target IDEs and APIs before editing since/until build. | Broadening range to make publication possible. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
IntelliJ Platform plugin remains user-owned when repository evidence does not
settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
IntelliJ Platform plugin. If none exists, report measurements or uncertainty. Do
not invent a timeout, reviewer count, confidence score, target, or error budget
and then treat it as a requirement.
