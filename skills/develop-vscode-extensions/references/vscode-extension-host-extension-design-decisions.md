# Extension design decisions for Vscode Extension Host

Use this guide after inspecting the request and target system for VS Code
extension. It selects an evidence path; it does not grant permission for an
external write or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Feature is declarative contribution only | Implement in `package.json` without unnecessary activation code. | A command/provider registration for static metadata. |
| Extension must run in web host | Use web-compatible APIs/bundling and reject Node-only dependencies. | Local filesystem/process assumptions. |
| Long analysis runs asynchronously | Use cancellation and document version/generation checks. | Publishing stale edits/results. |
| Language server is separate process | Define transport, lifecycle, restart, cancellation, and remote-host location. | Assuming local process path. |
| Feature executes workspace code | Require Workspace Trust and explicit action. | Hiding a command as security. |
| Packaging behavior is claimed | Build VSIX and inspect contents/install in host. | TypeScript compile only. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
VS Code extension remains user-owned when repository evidence does not settle
it. Present concrete alternatives and consequences. Resolve routine internal
details that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the VS
Code extension. If none exists, report measurements or uncertainty. Do not
invent a timeout, reviewer count, confidence score, target, or error budget and
then treat it as a requirement.
