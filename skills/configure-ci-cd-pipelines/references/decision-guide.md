# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Only local build/test automation is requested | Keep project commands local; do not add CI configuration. | A new pipeline merely because CI is common. |
| Untrusted pull request needs tests | Run without privileged secrets and minimize write permissions. | pull_request_target or equivalent executing checkout content. |
| A verified artifact must be promoted | Build once, store immutably, verify identity, then promote under approval. | Rebuilding different source or dependencies in the deploy job. |
| A third-party action/include is needed | Follow repository pinning and review policy; inspect required permissions/network. | Floating unreviewed tags. |
| The provider cannot express a required security boundary safely | Use an approved external control or surface the limitation. | Silent best-effort behavior marketed as secure. |

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
