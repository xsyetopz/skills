# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Feature is declarative contribution only | Implement in `package.json` without unnecessary activation code. | A command/provider registration for static metadata. |
| Extension must run in web host | Use web-compatible APIs/bundling and reject Node-only dependencies. | Local filesystem/process assumptions. |
| Long analysis runs asynchronously | Use cancellation and document version/generation checks. | Publishing stale edits/results. |
| Language server is separate process | Define transport, lifecycle, restart, cancellation, and remote-host location. | Assuming local process path. |
| Feature executes workspace code | Require Workspace Trust and explicit action. | Hiding a command as security. |
| Packaging behavior is claimed | Build VSIX and inspect contents/install in host. | TypeScript compile only. |

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
