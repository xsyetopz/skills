# Failure patterns and recovery for Agent Hook

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Schema borrowing** | A Claude/Cursor/Codex field is assumed to exist in another host. | Use the exact host/version reference. |
| **Shell injection** | Payload fields are concatenated into a shell command. | Parse structured input and invoke fixed executables with argument arrays. |
| **Authority inflation** | A notification hook is described as an access control. | State actual host semantics and move enforcement to a supported boundary. |
| **Destructive rollback** | Rollback deletes a pre-existing config or all hooks. | Remove only the added entry and exclusively created files. |
| **Fail-policy ignorance** | Handler crash causes surprising fail-open or fail-closed behavior. | Test and document the host's actual failure path. |
| **Fixture-as-registration** | Unit tests pass but the host never invokes the hook. | Perform a host diagnostic or controlled live event. |

## Recovery discipline

Preserve the first observable agent hook failure and the state that produced it.
Stop dependent work after a false prerequisite. If another equivalent retry
cannot add evidence, change the source, instrument, or hypothesis. Undo only
task-owned experiments; preserve unrelated user work.

Do not make the agent hook appear successful by swallowing its error, weakening
its oracle, regenerating an unexplained snapshot, adding an unsupported
fallback, or reporting an intermediate checkpoint as completion.
