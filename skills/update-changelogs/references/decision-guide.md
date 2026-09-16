# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Change affects only internal refactor with no audience impact | Omit or place only if the repository explicitly tracks internals. | Marketing it as improvement. |
| Commit label says breaking but public contract is unchanged | Describe actual effect; do not force a major bump. | Trusting the label alone. |
| Security fix has disclosure constraints | Follow approved advisory wording/timing. | Exposing exploit details prematurely. |
| Release version not specified | Update Unreleased/draft and surface version decision. | Choosing next version. |
| Already published note is wrong | Correct according to project policy and preserve historical transparency. | Silently rewriting history where immutable notes are expected. |

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
