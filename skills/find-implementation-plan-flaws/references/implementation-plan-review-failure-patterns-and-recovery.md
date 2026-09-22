# Failure patterns and recovery for Implementation Plan Review

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Replacement-plan drift** | Review becomes a new plan in a preferred style. | Report flaws and corrections only. |
| **Finding quota** | Reviewer invents issues to look useful. | Allow clean review and require evidence. |
| **Path trust** | Plan paths/symbols are accepted without inspection. | Verify current source. |
| **Best-practice veto** | Plan is rejected for not using a fashionable pattern. | Evaluate actual constraints. |
| **Test-name confidence** | A test suite name is treated as covering the change. | Inspect what the tests exercise. |
| **Independent omissions** | Findings are listed without interaction or ordering impact. | Analyze combined consequences. |

## Recovery discipline

Preserve the first observable implementation-plan review failure and the state
that produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the implementation-plan review appear successful by swallowing its
error, weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
