# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Pattern cargo cult** | A familiar architecture is added without scenario evidence. | Return to quality attributes and existing constraints. |
| **Source-of-truth ambiguity** | Several stores or configs can independently overwrite policy/state. | Choose authority and define synchronization or remove duplicate ownership. |
| **Responsibility collapse** | Validation or business rules move across layers merely to make tests pass. | Repair the invariant at the boundary with information and authority. |
| **Public-surface inflation** | Flags, config keys, endpoints, or extension points are added for imagined futures. | Keep behavior internal until a real consumer requires a surface. |
| **Retry reflex** | Retries mask deterministic errors or duplicate non-idempotent work. | Diagnose and add bounded retry only when protocol semantics support it. |
| **Abstraction leakage** | Provider-specific settings are ignored or approximated silently. | Expose explicit native controls or reject unsupported requests. |
| **Diagram authority** | A polished diagram is treated as current source truth. | Verify against code, config, deployment, and runtime evidence. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
