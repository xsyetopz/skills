# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Schema borrowing** | A Claude/Cursor/Codex field is assumed to exist in another host. | Use the exact host/version reference. |
| **Shell injection** | Payload fields are concatenated into a shell command. | Parse structured input and invoke fixed executables with argument arrays. |
| **Authority inflation** | A notification hook is described as an access control. | State actual host semantics and move enforcement to a supported boundary. |
| **Destructive rollback** | Rollback deletes a pre-existing config or all hooks. | Remove only the added entry and exclusively created files. |
| **Fail-policy ignorance** | Handler crash causes surprising fail-open or fail-closed behavior. | Test and document the host’s actual failure path. |
| **Fixture-as-registration** | Unit tests pass but the host never invokes the hook. | Perform a host diagnostic or controlled live event. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
