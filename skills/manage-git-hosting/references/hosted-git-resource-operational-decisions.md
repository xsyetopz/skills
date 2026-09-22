# Operational decisions for Hosted Git Resource

Use this guide after inspecting the request and target system for hosted Git
operation. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| User asks to review a PR | Inspect and report/submit the requested review type; do not approve or merge unless explicit. | An approving review by default. |
| Release notes requested without publish request | Prepare draft text/artifacts only. | Publishing a release. |
| Write response is lost/times out | Read exact resource and de-duplicate before retry. | Blind repeated POST. |
| Bulk resources require pagination | Follow provider pagination and record coverage. | First page treated as complete. |
| Provider-specific setting has no equivalent elsewhere | Use native field or error explicitly. | Silently dropping it in a generic abstraction. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
hosted Git operation remains user-owned when repository evidence does not settle
it. Present concrete alternatives and consequences. Resolve routine internal
details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the hosted
Git operation. If none exists, report measurements or uncertainty. Do not invent
a timeout, reviewer count, confidence score, target, or error budget and then
treat it as a requirement.
