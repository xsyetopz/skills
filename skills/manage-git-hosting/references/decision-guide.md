# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| User asks to review a PR | Inspect and report/submit the requested review type; do not approve or merge unless explicit. | An approving review by default. |
| Release notes requested without publish request | Prepare draft text/artifacts only. | Publishing a release. |
| Write response is lost/times out | Read exact resource and de-duplicate before retry. | Blind repeated POST. |
| Bulk resources require pagination | Follow provider pagination and record coverage. | First page treated as complete. |
| Provider-specific setting has no equivalent elsewhere | Use native field or error explicitly. | Silently dropping it in a generic abstraction. |

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
