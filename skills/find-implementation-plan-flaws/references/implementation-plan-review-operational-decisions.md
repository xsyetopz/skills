# Operational decisions for Implementation Plan Review

Use this guide after inspecting the request and target system for
implementation-plan review. It selects an evidence path; it does not grant
permission for an external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Plan names exact files/APIs | Open and verify them. | Assuming paths and signatures from the plan. |
| Plan leaves a routine implementation detail to the implementer | Accept it when acceptance and boundaries are sufficient. | Demanding pseudocode for every line. |
| Plan makes an externally visible choice without authority | Flag decision theft and list the unresolved options. | Selecting one in the review. |
| Plan proposes broad cleanup | Require necessity for the requested outcome or remove from scope. | Treating cleanup as free. |
| Check cannot observe the changed boundary | Require an appropriate check. | Adding more unrelated unit tests. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
implementation-plan review remains user-owned when repository evidence does not
settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
implementation-plan review. If none exists, report measurements or uncertainty.
Do not invent a timeout, reviewer count, confidence score, target, or error
budget and then treat it as a requirement.
