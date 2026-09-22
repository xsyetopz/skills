# Operational decisions for Behavioral Testing

Use this guide after inspecting the request and target system for behavioral
test. It selects an evidence path; it does not grant permission for an external
write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Pure deterministic unit with stable contract | Use focused unit/property tests and boundary values. | Full end-to-end environment for every case. |
| Defect crosses serialization/database/network/host boundary | Keep a realistic integration/contract test at that boundary. | Mocking it away. |
| Current behavior is unknown and refactor is planned | Use characterization tests labeled as current behavior, then decide desired changes separately. | Calling passing characterization TDD red/green. |
| Timing/concurrency matters | Control clocks/schedulers/barriers or use repeat/statistical rule with explicit evidence. | Arbitrary sleeps. |
| Hardware unavailable | Run build/static/simulator evidence and report physical layer unexecuted. | Claiming hardware validation. |
| Snapshot changes | Inspect semantic change and update only when desired contract changed. | Blind regeneration. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
behavioral test remains user-owned when repository evidence does not settle it.
Present concrete alternatives and consequences. Resolve routine internal details
that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
behavioral test. If none exists, report measurements or uncertainty. Do not
invent a timeout, reviewer count, confidence score, target, or error budget and
then treat it as a requirement.
