# Extension failures and recovery for Intellij Platform Plugin

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Stale PSI** | Background result uses invalid element. | Store stable identifiers/data and re-resolve/revalidate. |
| **Write without command** | Mutation bypasses undo or write rules. | Use platform command/write APIs. |
| **DumbAware misuse** | Index-dependent code is marked safe. | Defer or remove index dependency. |
| **Disposable leak** | Project close leaves listeners/tasks alive. | Register under correct parent and cancel. |
| **Target drift** | API works only in development IDE. | Verify declared since/until targets. |
| **EDT blocking** | I/O or long computation runs on UI thread. | Move work and publish through platform-safe path. |

## Recovery discipline

Preserve the first observable IntelliJ Platform plugin failure and the state
that produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the IntelliJ Platform plugin appear successful by swallowing its
error, weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
