# Failure patterns and recovery for Repository Agent Instructions

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Global prompt dump** | Long general coding policy consumes every task context. | Keep repository-specific non-obvious rules only. |
| **Skill duplication** | Task workflows are copied into always-on instructions. | Use on-demand skills. |
| **Stale command** | Old README command is preserved despite current scripts/config. | Inspect and run current command. |
| **Scope collision** | Root and nested files contradict without precedence explanation. | Normalize shared rule and isolate local differences. |
| **Transient state** | Branch progress, current bug, or personal preference becomes durable policy. | Keep transient context outside instructions. |
| **Client folklore** | Discovery/size/precedence is assumed across tools. | Verify target client/version. |

## Recovery discipline

Preserve the first observable AGENTS.md instructions failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the AGENTS.md instructions appear successful by swallowing its
error, weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
