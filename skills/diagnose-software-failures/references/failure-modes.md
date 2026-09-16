# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Retry reflex** | Timeout/retry values are increased before identifying failure type. | Inspect wait state and protocol; add retry only for safe transient failure. |
| **Log avalanche** | Unbounded logs obscure the first error and expose sensitive data. | Add targeted correlation/observations at the disputed boundary. |
| **Patch accumulation** | Several speculative edits make causality and rollback unclear. | Return to known state and test one hypothesis. |
| **Harness conflation** | A wrapper/plugin failure is attributed to the target or vice versa. | Reproduce below the wrapper and compare layers. |
| **Assertion repair** | Expected output is changed to current broken output. | Recover expectation from the contract. |
| **Cache purge as fix** | Deleting all state hides an invalidation or provenance problem. | Name cold/warm state and establish why cache state matters. |
| **Dependency upgrade roulette** | Broad upgrades change the symptom without causal evidence. | Isolate the actual incompatible dependency or source defect. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
