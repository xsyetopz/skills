# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Plan as noun ambiguity** | Title/name does not indicate writing action. | Use explicit “write implementation plans” and verb-driven tasks. |
| **Repository fiction** | Nonexistent files/APIs/commands are planned. | Inspect current source and cite locations. |
| **Task vagueness** | Steps say implement/refactor/test without concrete targets. | Specify change, prerequisite, and evidence. |
| **Architecture invention** | Plan creates services/abstractions for imagined future needs. | Follow accepted design and actual constraints. |
| **Verification blob** | “Run all tests” is the only acceptance. | Map checks to changed boundaries. |
| **Delivery creep** | Release/deploy/docs/cleanup stages appear without need. | Include only required downstream work. |
| **Estimation fiction** | Dates/story points/owners are invented. | Use user/process values or omit. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
