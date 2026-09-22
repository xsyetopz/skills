# Failure patterns and recovery for Just Command Runner

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Second build system** | Recipes contain duplicated compilation/deployment logic. | Move logic to canonical script/tool and call it. |
| **Masked exit** | `\|\| true`, pipeline, or later command returns success. | Use strict script behavior and preserve status. |
| **Interpolation injection** | Free text becomes executable shell syntax. | Pass as quoted argument or structured input. |
| **Version guessing** | New syntax is used without checking installed just. | Inspect version/manual or gate upgrade decision. |
| **Dependency surprise** | A harmless command automatically triggers expensive/destructive recipes. | Keep dependencies minimal and explicit. |
| **Local-path leak** | Recipe embeds one developer's absolute path or environment. | Use repository-relative/configured paths. |

## Recovery discipline

Preserve the first observable justfile recipe failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the justfile recipe appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
