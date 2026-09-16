# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Generic nonzero oracle** | Build/setup failure is classified as bad. | Use distinct codes and inspect the cause. |
| **Boundary assumption** | Tags/dates are marked good/bad without running the oracle. | Verify both ends. |
| **Active-tree mutation** | Bisect checks out revisions over user work. | Use isolated worktree/clone. |
| **Current-dependency leakage** | Historical revisions use today’s generated or external state. | Reconstruct revision-appropriate dependencies. |
| **Skipped-range certainty** | A unique commit is claimed despite ambiguous skips. | Report the candidate range. |
| **Automatic revert** | The found commit is reverted without diagnosis/authority. | Inspect causal diff and await requested fix action. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
