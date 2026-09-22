# Operational decisions for Just Command Runner

Use this guide after inspecting the request and target system for justfile
recipe. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| A project script already implements operation | Call it with explicit parameters. | Copying script logic into justfile. |
| Multiline shell logic needs strict behavior | Use a script recipe or existing script file. | Backslash-heavy one-liner with masked errors. |
| Recipe is platform-specific | Use supported OS selector or explicit dependency and fail clearly elsewhere. | Silent fallback to different behavior. |
| Parameter contains paths/free text | Use documented parameters and safe shell quoting/script args. | `eval` or string-built command. |
| Multiple recipes form a workflow | Use dependencies only when every invocation requires them; otherwise separate explicit recipes. | Surprising automatic deployment/build steps. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
justfile recipe remains user-owned when repository evidence does not settle it.
Present concrete alternatives and consequences. Resolve routine internal details
that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the
justfile recipe. If none exists, report measurements or uncertainty. Do not
invent a timeout, reviewer count, confidence score, target, or error budget and
then treat it as a requirement.
