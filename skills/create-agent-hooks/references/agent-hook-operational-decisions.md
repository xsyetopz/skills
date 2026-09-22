# Operational decisions for Agent Hook

Use this guide after inspecting the request and target system for agent hook. It
selects an evidence path; it does not grant permission for an external write or
another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Goal is logging/telemetry | Use a notification event and nonblocking, sanitized output. | Pretending the hook enforces policy. |
| Goal is to reject dangerous tool arguments | Use a documented pre-action blocking event with strict parsing. | A post-action notification or prompt text. |
| Host offers no suitable blocking event | Report that limitation or use an approved external control. | Exit-code folklore from another host. |
| Existing config contains hooks | Merge the one new entry with preserved ordering/scope. | Replacing the file from a template. |
| Payload includes a command string | Treat it as data and validate structured fields; avoid `shell=True`/`eval`. | Executing the string to inspect it. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
agent hook remains user-owned when repository evidence does not settle it.
Present concrete alternatives and consequences. Resolve routine internal details
that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the agent
hook. If none exists, report measurements or uncertainty. Do not invent a
timeout, reviewer count, confidence score, target, or error budget and then
treat it as a requirement.
