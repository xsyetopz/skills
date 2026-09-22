# Failure patterns and recovery for System Boundaries

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

Preserve the first observable architecture decision failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the architecture decision appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
