# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Behavior is fully specified and only implementation is requested | Do not rewrite requirements; use the existing contract. | A new spec or approval ceremony. |
| Current behavior conflicts with the explicit request | Specify the requested behavior and identify migration/compatibility as a separate decision. | Preserving current behavior by default. |
| One example could imply several policies | State the example and ask/present options for the material policy. | Generalizing it silently. |
| A quality adjective lacks a measure | Replace it with an observation or leave it unresolved. | Inventing a threshold. |
| Internal structure has no external effect | Leave it to design/implementation. | A requirement naming classes, functions, or files. |

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
