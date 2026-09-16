# Decision guide

Use this guide after inspecting the target repository and current request. It
selects an evidence path; it does not grant permission for writes or external
operations.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Feature is language metadata/query only | Use language extension files; no Rust/Wasm code. | Unneeded extension binary. |
| Feature needs supported runtime API | Use exact selected-version extension API. | Assuming current main docs match target. |
| Language server already installed/configured | Respect native/user path and validate version before download. | Always downloading bundled binary. |
| Binary download required | Use platform mapping, integrity, approved source, cache/cleanup, and explicit errors. | Executing arbitrary latest asset. |
| Tree-sitter query fails | Match selected grammar nodes and test captures. | Copying query from another grammar revision. |
| Requested UI integration unsupported | Explain limitation or use documented alternative with user agreement. | Inventing manifest keys. |

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
