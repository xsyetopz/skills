# Operational decisions for Release History

Use this guide after inspecting the request and target system for changelog
entry. It selects an evidence path; it does not grant permission for an external
write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Change affects only internal refactor with no audience impact | Omit or place only if the repository explicitly tracks internals. | Marketing it as improvement. |
| Commit label says breaking but public contract is unchanged | Describe actual effect; do not force a major bump. | Trusting the label alone. |
| Security fix has disclosure constraints | Follow approved advisory wording/timing. | Exposing exploit details prematurely. |
| Release version not specified | Update Unreleased/draft and surface version decision. | Choosing next version. |
| Already published note is wrong | Correct according to project policy and preserve historical transparency. | Silently rewriting history where immutable notes are expected. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
changelog entry remains user-owned when repository evidence does not settle it.
Present concrete alternatives and consequences. Resolve routine internal details
that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
changelog entry. If none exists, report measurements or uncertainty. Do not
invent a timeout, reviewer count, confidence score, target, or error budget and
then treat it as a requirement.
