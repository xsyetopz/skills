# Operational decisions for Compatibility Retirement

Use this guide after inspecting the request and target system for compatibility
removal. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Agent added alias/fallback and test without requirement | Remove both within authorized change after checking no real consumer adopted them. | Inventing a deprecation cycle. |
| Documented stable public API is deprecated but policy window remains open | Preserve until actual retirement conditions are met. | Deleting because usage is low. |
| Private internal shim has no callers/history purpose | Remove with focused checks. | Keeping it because “compatibility is safer.” |
| Serialized data may contain old form | Design/verify migration or keep reader until data obligation ends. | Removing parser from empty source search. |
| Support status cannot be proven | Surface unresolved decision and impact. | Choosing based on taste. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
compatibility removal remains user-owned when repository evidence does not
settle it. Present concrete alternatives and consequences. Resolve routine
internal details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
compatibility removal. If none exists, report measurements or uncertainty. Do
not invent a timeout, reviewer count, confidence score, target, or error budget
and then treat it as a requirement.
