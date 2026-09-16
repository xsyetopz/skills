# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Implementation leakage** | Requirements mandate files/classes/algorithms without external necessity. | State the behavior and move design choices to architecture/planning. |
| **State-goal conflation** | Current behavior is copied as intent despite the requested change. | Trace desired behavior to current authority. |
| **Invented thresholds** | Numeric limits appear without source. | Use measured baselines or request a user-owned threshold. |
| **Happy-path only** | Failures, cancellation, concurrency, or partial effects are unspecified despite exposure. | Add observable outcomes where material. |
| **Example expansion** | One sample value becomes a general policy. | Separate example from rule and resolve the actual domain. |
| **Test-as-spec** | A visible test implementation detail becomes the requirement. | Anchor behavior in the approved contract. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
