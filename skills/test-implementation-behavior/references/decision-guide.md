# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Pure deterministic unit with stable contract | Use focused unit/property tests and boundary values. | Full end-to-end environment for every case. |
| Defect crosses serialization/database/network/host boundary | Keep a realistic integration/contract test at that boundary. | Mocking it away. |
| Current behavior is unknown and refactor is planned | Use characterization tests labeled as current behavior, then decide desired changes separately. | Calling passing characterization TDD red/green. |
| Timing/concurrency matters | Control clocks/schedulers/barriers or use repeat/statistical rule with explicit evidence. | Arbitrary sleeps. |
| Hardware unavailable | Run build/static/simulator evidence and report physical layer unexecuted. | Claiming hardware validation. |
| Snapshot changes | Inspect semantic change and update only when desired contract changed. | Blind regeneration. |

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
