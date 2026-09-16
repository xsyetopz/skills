# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Replacement-plan drift** | Review becomes a new plan in a preferred style. | Report flaws and corrections only. |
| **Finding quota** | Reviewer invents issues to look useful. | Allow clean review and require evidence. |
| **Path trust** | Plan paths/symbols are accepted without inspection. | Verify current source. |
| **Best-practice veto** | Plan is rejected for not using a fashionable pattern. | Evaluate actual constraints. |
| **Test-name confidence** | A test suite name is treated as covering the change. | Inspect what the tests exercise. |
| **Independent omissions** | Findings are listed without interaction or ordering impact. | Analyze combined consequences. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
