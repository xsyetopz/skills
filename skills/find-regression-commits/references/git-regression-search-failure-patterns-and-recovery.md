# Failure patterns and recovery for Git Regression Search

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Generic nonzero oracle** | Build/setup failure is classified as bad. | Use distinct codes and inspect the cause. |
| **Boundary assumption** | Tags/dates are marked good/bad without running the oracle. | Verify both ends. |
| **Active-tree mutation** | Bisect checks out revisions over user work. | Use isolated worktree/clone. |
| **Current-dependency leakage** | Historical revisions use today's generated or external state. | Reconstruct revision-appropriate dependencies. |
| **Skipped-range certainty** | A unique commit is claimed despite ambiguous skips. | Report the candidate range. |
| **Automatic revert** | The found commit is reverted without diagnosis/authority. | Inspect causal diff and await requested fix action. |

## Recovery discipline

Preserve the first observable regression search failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the regression search appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
