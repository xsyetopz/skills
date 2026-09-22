# Extension failures and recovery for Sublime Python Plugin

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Edit token escape** | Stored token used in async callback. | Return data and invoke a new command. |
| **Stub-as-host proof** | Mocks pass while API/lifecycle fails in Sublime. | Run host suite and label stub evidence. |
| **System-runtime drift** | Code uses unsupported Python syntax/library. | Target embedded runtime. |
| **Reload leak** | Global listener/timer/process duplicates. | Idempotent registration and unload cleanup. |
| **Stale view** | Callback edits closed or changed view. | Capture/revalidate ID/change count/generation. |
| **Resource filesystem assumption** | Packaged resource treated as normal writable file. | Use host resource/storage APIs. |

## Recovery discipline

Preserve the first observable Sublime Text plugin failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the Sublime Text plugin appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
