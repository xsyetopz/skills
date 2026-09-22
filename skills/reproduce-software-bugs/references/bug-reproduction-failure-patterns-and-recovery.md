# Failure patterns and recovery for Bug Reproduction

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Generic-error substitution** | Target parser bug becomes missing-file/import error. | Use sanity and signature checks. |
| **Mock-away** | Mock returns the desired failure without exercising the real boundary. | Retain the failing protocol/component. |
| **Hidden environment** | Local caches, services, credentials, or global packages are required but undocumented. | Run in a fresh isolated environment. |
| **Over-reduction** | Important configuration/timing/ownership is removed. | Restore the last element and explain its role. |
| **Tutorial drift** | Reproducer becomes an explanatory sample that no longer fails. | Keep expected versus actual and runnable failure. |
| **Sensitive bundle** | Customer data, tokens, or proprietary modules are included. | Synthesize/minimize under policy and verify signature. |

## Recovery discipline

Preserve the first observable bug reproducer failure and the state that produced
it. Stop dependent work after a false prerequisite. If another equivalent retry
cannot add evidence, change the source, instrument, or hypothesis. Undo only
task-owned experiments; preserve unrelated user work.

Do not make the bug reproducer appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
