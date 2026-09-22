# Operational decisions for Git Regression Search

Use this guide after inspecting the request and target system for regression
search. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Intermediate revision does not build because of expected historical toolchain | Use repository-pinned historical toolchain if available; otherwise skip and record. | Mark bad. |
| Oracle is flaky | Stabilize/repeat with a documented rule before bisect. | Let one run classify each commit. |
| Merge history matters | Choose ancestry/first-parent/full history according to the question and explain it. | Defaulting silently. |
| Many adjacent skips remain | Report ambiguous range or improve environment. | Claiming nearest tested bad as first bad. |
| Submodule/generated dependency changes | Record and reproduce dependency state per revision. | Testing all revisions with current external state. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
regression search remains user-owned when repository evidence does not settle
it. Present concrete alternatives and consequences. Resolve routine internal
details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
regression search. If none exists, report measurements or uncertainty. Do not
invent a timeout, reviewer count, confidence score, target, or error budget and
then treat it as a requirement.
