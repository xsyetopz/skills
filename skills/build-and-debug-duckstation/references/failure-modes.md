# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **User-state overwrite** | Experiments use default user config/memory cards. | Use task-owned isolated paths and verify cleanup. |
| **Emulator conflation** | Commands/settings from another emulator or release are applied. | Use exact upstream version. |
| **Layer misdiagnosis** | Guest crash, renderer artifact, or process failure is assigned to wrong layer. | Compare controlled layers and first divergence. |
| **Save-state overreach** | A state from another revision is treated as authoritative. | Record provenance and reproduce by normal path where needed. |
| **Patch overbreadth** | Patch targets wrong serial/CRC/build or unconditional address. | Bind and validate exact target/condition. |
| **Command-as-execution** | Generated args are reported as tested emulator behavior. | Run and observe each claimed layer. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
