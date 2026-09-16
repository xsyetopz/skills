# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Intermediate revision does not build because of expected historical toolchain | Use repository-pinned historical toolchain if available; otherwise skip and record. | Mark bad. |
| Oracle is flaky | Stabilize/repeat with a documented rule before bisect. | Let one run classify each commit. |
| Merge history matters | Choose ancestry/first-parent/full history according to the question and explain it. | Defaulting silently. |
| Many adjacent skips remain | Report ambiguous range or improve environment. | Claiming nearest tested bad as first bad. |
| Submodule/generated dependency changes | Record and reproduce dependency state per revision. | Testing all revisions with current external state. |

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
