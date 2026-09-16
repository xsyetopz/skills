# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Goal is logging/telemetry | Use a notification event and nonblocking, sanitized output. | Pretending the hook enforces policy. |
| Goal is to reject dangerous tool arguments | Use a documented pre-action blocking event with strict parsing. | A post-action notification or prompt text. |
| Host offers no suitable blocking event | Report that limitation or use an approved external control. | Exit-code folklore from another host. |
| Existing config contains hooks | Merge the one new entry with preserved ordering/scope. | Replacing the file from a template. |
| Payload includes a command string | Treat it as data and validate structured fields; avoid `shell=True`/`eval`. | Executing the string to inspect it. |

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
