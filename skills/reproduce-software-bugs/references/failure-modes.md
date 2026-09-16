# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Generic-error substitution** | Target parser bug becomes missing-file/import error. | Use sanity and signature checks. |
| **Mock-away** | Mock returns the desired failure without exercising the real boundary. | Retain the failing protocol/component. |
| **Hidden environment** | Local caches, services, credentials, or global packages are required but undocumented. | Run in a fresh isolated environment. |
| **Over-reduction** | Important configuration/timing/ownership is removed. | Restore the last element and explain its role. |
| **Tutorial drift** | Reproducer becomes an explanatory sample that no longer fails. | Keep expected versus actual and runnable failure. |
| **Sensitive bundle** | Customer data, tokens, or proprietary modules are included. | Synthesize/minimize under policy and verify signature. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
