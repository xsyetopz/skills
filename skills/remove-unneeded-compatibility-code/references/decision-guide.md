# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Agent added alias/fallback and test without requirement | Remove both within authorized change after checking no real consumer adopted them. | Inventing a deprecation cycle. |
| Documented stable public API is deprecated but policy window remains open | Preserve until actual retirement conditions are met. | Deleting because usage is low. |
| Private internal shim has no callers/history purpose | Remove with focused checks. | Keeping it because “compatibility is safer.” |
| Serialized data may contain old form | Design/verify migration or keep reader until data obligation ends. | Removing parser from empty source search. |
| Support status cannot be proven | Surface unresolved decision and impact. | Choosing based on taste. |

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
