# Failure patterns and recovery for Failure Investigation

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

Preserve the first observable root-cause investigation failure and the state
that produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the root-cause investigation appear successful by swallowing its
error, weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
