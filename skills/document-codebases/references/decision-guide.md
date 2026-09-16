# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| A command exists in package scripts/Just/Make/CMake | Document the existing command and its working directory. | Reconstructing a different command from memory. |
| Several equivalent setup paths exist | Choose the project-supported canonical path; include alternatives only for real distinct use cases. | Listing every possible tool. |
| An example needs credentials | Use environment-variable placeholders and link the approved secret mechanism. | Hardcoded token or fabricated login flow. |
| A workflow or state relationship is complex | Use Mermaid with precise node labels and text explanation. | ASCII art that is hard to update. |
| A step cannot be executed in the environment | Verify syntax/source and label runtime status as unexecuted. | Fabricated output. |

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
