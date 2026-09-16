# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Edit token escape** | Stored token used in async callback. | Return data and invoke a new command. |
| **Stub-as-host proof** | Mocks pass while API/lifecycle fails in Sublime. | Run host suite and label stub evidence. |
| **System-runtime drift** | Code uses unsupported Python syntax/library. | Target embedded runtime. |
| **Reload leak** | Global listener/timer/process duplicates. | Idempotent registration and unload cleanup. |
| **Stale view** | Callback edits closed or changed view. | Capture/revalidate ID/change count/generation. |
| **Resource filesystem assumption** | Packaged resource treated as normal writable file. | Use host resource/storage APIs. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
