# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Failure depends on large input | Delta-debug fields/bytes while preserving signature and sanity. | Replacing input with an unrelated crash. |
| Failure depends on many services | Reduce to the lowest real boundary that still fails; use real protocol fixtures when mocks would hide it. | Mocking the failed integration away. |
| Race is intermittent | Use repeat count/controlled schedule and report observed rate/conditions. | One lucky failure or arbitrary sleep. |
| Build defect depends on repository generator | Include the generator/input or a complete minimal equivalent. | Checking in generated bad output only. |
| Customer data is involved | Create synthetic data that reproduces the same parser/state condition and verify equivalence. | Redacting fields without rerunning. |

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
