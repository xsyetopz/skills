# Operational decisions for System Boundaries

Use this guide after inspecting the request and target system for architecture
decision. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| One component owns the state and deployment | Prefer a module/package boundary unless separate operation or fault isolation is required. | A network service for organizational fashion. |
| Independent scaling, trust, deployment, or availability is required | Evaluate a service boundary including operational cost and failure semantics. | Pretending an in-process interface and network call are equivalent. |
| Several providers expose shared concepts plus unique controls | Define a common core and an explicit provider-native escape hatch. | Dropping unsupported settings silently. |
| Read model differs from write model | Use a projection only when query/load needs justify duplication and define rebuild/consistency. | A second database as speculative flexibility. |
| A retry is proposed | Require a genuinely transient failure, safe idempotency semantics, bounds, and backoff. | Generic resilience wrapping every error. |
| Similar code has different invariants or owners | Keep it separate or share only stable lower-level mechanisms. | An abstraction based on visual duplication. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
architecture decision remains user-owned when repository evidence does not
settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
architecture decision. If none exists, report measurements or uncertainty. Do
not invent a timeout, reviewer count, confidence score, target, or error budget
and then treat it as a requirement.
