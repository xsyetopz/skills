# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Stale PSI** | Background result uses invalid element. | Store stable identifiers/data and re-resolve/revalidate. |
| **Write without command** | Mutation bypasses undo or write rules. | Use platform command/write APIs. |
| **DumbAware misuse** | Index-dependent code is marked safe. | Defer or remove index dependency. |
| **Disposable leak** | Project close leaves listeners/tasks alive. | Register under correct parent and cancel. |
| **Target drift** | API works only in development IDE. | Verify declared since/until targets. |
| **EDT blocking** | I/O or long computation runs on UI thread. | Move work and publish through platform-safe path. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
