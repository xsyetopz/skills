# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Whole-tree reset** | User edits disappear to make the tree clean. | Restore only attributable hunks or use isolated worktree. |
| **Index/worktree conflation** | Staged and unstaged changes to one file are overwritten together. | Inspect both diffs and operate on the intended layer. |
| **Blind conflict choice** | Ours/theirs is accepted without preserving the semantic contract. | Resolve from base and requirements, then test. |
| **Force retry** | Unexpected remote changes are overwritten. | Fetch, inspect, and use authorized lease semantics if appropriate. |
| **Hook surprise** | Commit differs from reviewed staged content. | Reinspect commit and residual changes. |
| **Automatic commit** | Agent commits merely because implementation is done. | Commit only when requested or established workflow explicitly requires it. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
