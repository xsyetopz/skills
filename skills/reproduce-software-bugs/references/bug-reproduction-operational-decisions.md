# Operational decisions for Bug Reproduction

Use this guide after inspecting the request and target system for bug
reproducer. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Failure depends on large input | Delta-debug fields/bytes while preserving signature and sanity. | Replacing input with an unrelated crash. |
| Failure depends on many services | Reduce to the lowest real boundary that still fails; use real protocol fixtures when mocks would hide it. | Mocking the failed integration away. |
| Race is intermittent | Use repeat count/controlled schedule and report observed rate/conditions. | One lucky failure or arbitrary sleep. |
| Build defect depends on repository generator | Include the generator/input or a complete minimal equivalent. | Checking in generated bad output only. |
| Customer data is involved | Create synthetic data that reproduces the same parser/state condition and verify equivalence. | Redacting fields without rerunning. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
bug reproducer remains user-owned when repository evidence does not settle it.
Present concrete alternatives and consequences. Resolve routine internal details
that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the bug
reproducer. If none exists, report measurements or uncertainty. Do not invent a
timeout, reviewer count, confidence score, target, or error budget and then
treat it as a requirement.
