# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Plan names exact files/APIs | Open and verify them. | Assuming paths and signatures from the plan. |
| Plan leaves a routine implementation detail to the implementer | Accept it when acceptance and boundaries are sufficient. | Demanding pseudocode for every line. |
| Plan makes an externally visible choice without authority | Flag decision theft and list the unresolved options. | Selecting one in the review. |
| Plan proposes broad cleanup | Require necessity for the requested outcome or remove from scope. | Treating cleanup as free. |
| Check cannot observe the changed boundary | Require an appropriate check. | Adding more unrelated unit tests. |

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
