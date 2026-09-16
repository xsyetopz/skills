# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| One component owns the state and deployment | Prefer a module/package boundary unless separate operation or fault isolation is required. | A network service for organizational fashion. |
| Independent scaling, trust, deployment, or availability is required | Evaluate a service boundary including operational cost and failure semantics. | Pretending an in-process interface and network call are equivalent. |
| Several providers expose shared concepts plus unique controls | Define a common core and an explicit provider-native escape hatch. | Dropping unsupported settings silently. |
| Read model differs from write model | Use a projection only when query/load needs justify duplication and define rebuild/consistency. | A second database as speculative flexibility. |
| A retry is proposed | Require a genuinely transient failure, safe idempotency semantics, bounds, and backoff. | Generic resilience wrapping every error. |
| Similar code has different invariants or owners | Keep it separate or share only stable lower-level mechanisms. | An abstraction based on visual duplication. |

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
