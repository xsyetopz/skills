# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| A project script already implements operation | Call it with explicit parameters. | Copying script logic into justfile. |
| Multiline shell logic needs strict behavior | Use a script recipe or existing script file. | Backslash-heavy one-liner with masked errors. |
| Recipe is platform-specific | Use supported OS selector or explicit dependency and fail clearly elsewhere. | Silent fallback to different behavior. |
| Parameter contains paths/free text | Use documented parameters and safe shell quoting/script args. | `eval` or string-built command. |
| Multiple recipes form a workflow | Use dependencies only when every invocation requires them; otherwise separate explicit recipes. | Surprising automatic deployment/build steps. |

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
