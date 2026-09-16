# Failure modes and recovery

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

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
