# Failure patterns and recovery for Implementation Planning

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

Preserve the first observable implementation plan failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the implementation plan appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
