# Operational decisions for Behavioral Requirements

Use this guide after inspecting the request and target system for behavioral
requirement set. It selects an evidence path; it does not grant permission for
an external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Behavior is fully specified and only implementation is requested | Do not rewrite requirements; use the existing contract. | A new spec or approval ceremony. |
| Current behavior conflicts with the explicit request | Specify the requested behavior and identify migration/compatibility as a separate decision. | Preserving current behavior by default. |
| One example could imply several policies | State the example and ask/present options for the material policy. | Generalizing it silently. |
| A quality adjective lacks a measure | Replace it with an observation or leave it unresolved. | Inventing a threshold. |
| Internal structure has no external effect | Leave it to design/implementation. | A requirement naming classes, functions, or files. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
behavioral requirement set remains user-owned when repository evidence does not
settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
behavioral requirement set. If none exists, report measurements or uncertainty.
Do not invent a timeout, reviewer count, confidence score, target, or error
budget and then treat it as a requirement.
