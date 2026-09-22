# Failure patterns and recovery for Local Git State

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Whole-tree reset** | User edits disappear to make the tree clean. | Restore only attributable hunks or use isolated worktree. |
| **Index/worktree conflation** | Staged and unstaged changes to one file are overwritten together. | Inspect both diffs and operate on the intended layer. |
| **Blind conflict choice** | Ours/theirs is accepted without preserving the semantic contract. | Resolve from base and requirements, then test. |
| **Force retry** | Unexpected remote changes are overwritten. | Fetch, inspect, and use authorized lease semantics if appropriate. |
| **Hook surprise** | Commit differs from reviewed staged content. | Reinspect commit and residual changes. |
| **Automatic commit** | Agent commits merely because implementation is done. | Commit only when requested or established workflow explicitly requires it. |

## Recovery discipline

Preserve the first observable local Git operation failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the local Git operation appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
