# Failure patterns and recovery for Behavioral Requirements

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Implementation leakage** | Requirements mandate files/classes/algorithms without external necessity. | State the behavior and move design choices to architecture/planning. |
| **State-goal conflation** | Current behavior is copied as intent despite the requested change. | Trace desired behavior to current authority. |
| **Invented thresholds** | Numeric limits appear without source. | Use measured baselines or request a user-owned threshold. |
| **Happy-path only** | Failures, cancellation, concurrency, or partial effects are unspecified despite exposure. | Add observable outcomes where material. |
| **Example expansion** | One sample value becomes a general policy. | Separate example from rule and resolve the actual domain. |
| **Test-as-spec** | A visible test implementation detail becomes the requirement. | Anchor behavior in the approved contract. |

## Recovery discipline

Preserve the first observable behavioral requirement set failure and the state
that produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the behavioral requirement set appear successful by swallowing its
error, weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
