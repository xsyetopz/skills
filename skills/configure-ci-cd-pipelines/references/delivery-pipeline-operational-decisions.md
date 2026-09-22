# Operational decisions for Delivery Pipeline

Use this guide after inspecting the request and target system for CI/CD workflow
change. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Only local build/test automation is requested | Keep project commands local; do not add CI configuration. | A new pipeline merely because CI is common. |
| Untrusted pull request needs tests | Run without privileged secrets and minimize write permissions. | pull_request_target or equivalent executing checkout content. |
| A verified artifact must be promoted | Build once, store immutably, verify identity, then promote under approval. | Rebuilding different source or dependencies in the deploy job. |
| A third-party action/include is needed | Follow repository pinning and review policy; inspect required permissions/network. | Floating unreviewed tags. |
| The provider cannot express a required security boundary safely | Use an approved external control or surface the limitation. | Silent best-effort behavior marketed as secure. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
CI/CD workflow change remains user-owned when repository evidence does not
settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the CI/CD
workflow change. If none exists, report measurements or uncertainty. Do not
invent a timeout, reviewer count, confidence score, target, or error budget and
then treat it as a requirement.
