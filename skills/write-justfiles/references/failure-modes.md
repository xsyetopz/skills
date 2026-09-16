# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Second build system** | Recipes contain duplicated compilation/deployment logic. | Move logic to canonical script/tool and call it. |
| **Masked exit** | `\|\| true`, pipeline, or later command returns success. | Use strict script behavior and preserve status. |
| **Interpolation injection** | Free text becomes executable shell syntax. | Pass as quoted argument or structured input. |
| **Version guessing** | New syntax is used without checking installed just. | Inspect version/manual or gate upgrade decision. |
| **Dependency surprise** | A harmless command automatically triggers expensive/destructive recipes. | Keep dependencies minimal and explicit. |
| **Local-path leak** | Recipe embeds one developer’s absolute path or environment. | Use repository-relative/configured paths. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
