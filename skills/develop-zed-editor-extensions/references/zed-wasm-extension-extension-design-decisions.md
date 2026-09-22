# Extension design decisions for Zed WASM Extension

Use this guide after inspecting the request and target system for Zed extension.
It selects an evidence path; it does not grant permission for an external write
or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Feature is language metadata/query only | Use language extension files; no Rust/Wasm code. | Unneeded extension binary. |
| Feature needs supported runtime API | Use exact selected-version extension API. | Assuming current main docs match target. |
| Language server already installed/configured | Respect native/user path and validate version before download. | Always downloading bundled binary. |
| Binary download required | Use platform mapping, integrity, approved source, cache/cleanup, and explicit errors. | Executing arbitrary latest asset. |
| Tree-sitter query fails | Match selected grammar nodes and test captures. | Copying query from another grammar revision. |
| Requested UI integration unsupported | Explain limitation or use documented alternative with user agreement. | Inventing manifest keys. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
Zed extension remains user-owned when repository evidence does not settle it.
Present concrete alternatives and consequences. Resolve routine internal details
that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the Zed
extension. If none exists, report measurements or uncertainty. Do not invent a
timeout, reviewer count, confidence score, target, or error budget and then
treat it as a requirement.
