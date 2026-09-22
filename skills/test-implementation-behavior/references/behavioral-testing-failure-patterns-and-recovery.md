# Failure patterns and recovery for Behavioral Testing

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Implementation prose test** | Assertion checks comment, class name, or marker instead of behavior. | Observe the required result/effect unless structure is the requirement. |
| **Test-as-spec** | Visible test detail is treated as product intent. | Anchor expectation in approved contract. |
| **Tautological oracle** | Expected value uses the same code/algorithm. | Use independent model, known values, invariant, or differential source. |
| **Mock-away** | Relevant integration is replaced and claimed verified. | Retain boundary test. |
| **Visible-fixture overfit** | Production special-cases test input. | Test general behavior and varied/held-out cases. |
| **Snapshot reflex** | Unexpected output is blessed. | Review against contract and explain intended change. |
| **False TDD history** | Post-implementation test/mutant is reported as pre-implementation red. | Label actual chronology. |
| **Hardware evidence inflation** | Build/simulation is reported as device success. | Name exact execution layer. |
| **Flaky success** | One lucky pass is accepted. | Control source or gather sufficient repeated evidence. |
| **Test multiplication** | Many cases repeat same partition without new discrimination. | Keep minimal boundary partitions and meaningful properties. |

## Recovery discipline

Preserve the first observable behavioral test failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the behavioral test appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
