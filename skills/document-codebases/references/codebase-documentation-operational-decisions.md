# Operational decisions for Codebase Documentation

Use this guide after inspecting the request and target system for codebase
documentation. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| A command exists in package scripts/Just/Make/CMake | Document the existing command and its working directory. | Reconstructing a different command from memory. |
| Several equivalent setup paths exist | Choose the project-supported canonical path; include alternatives only for real distinct use cases. | Listing every possible tool. |
| An example needs credentials | Use environment-variable placeholders and link the approved secret mechanism. | Hardcoded token or fabricated login flow. |
| A workflow or state relationship is complex | Use Mermaid with precise node labels and text explanation. | ASCII art that is hard to update. |
| A step cannot be executed in the environment | Verify syntax/source and label runtime status as unexecuted. | Fabricated output. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
codebase documentation remains user-owned when repository evidence does not
settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
codebase documentation. If none exists, report measurements or uncertainty. Do
not invent a timeout, reviewer count, confidence score, target, or error budget
and then treat it as a requirement.
