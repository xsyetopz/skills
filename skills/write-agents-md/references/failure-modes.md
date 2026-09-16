# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Global prompt dump** | Long general coding policy consumes every task context. | Keep repository-specific non-obvious rules only. |
| **Skill duplication** | Task workflows are copied into always-on instructions. | Use on-demand skills. |
| **Stale command** | Old README command is preserved despite current scripts/config. | Inspect and run current command. |
| **Scope collision** | Root and nested files contradict without precedence explanation. | Normalize shared rule and isolate local differences. |
| **Transient state** | Branch progress, current bug, or personal preference becomes durable policy. | Keep transient context outside instructions. |
| **Client folklore** | Discovery/size/precedence is assumed across tools. | Verify target client/version. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
