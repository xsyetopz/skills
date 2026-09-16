# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Age-based deletion** | Old code is removed because it looks legacy. | Find authority and consumers. |
| **Test-created contract** | An agent-added test is treated as proof support must remain. | Trace to user/public policy. |
| **Empty-search certainty** | No local call sites becomes “no users.” | Check public/export/data/deployment surfaces and mark unknown. |
| **Partial removal** | Implementation deleted but registration/export/docs/fallback keeps behavior. | Trace all entry points and artifacts. |
| **Behavior loss** | Shim removal drops unique validation/error/cleanup. | Preserve shared required behavior. |
| **Alias rebirth** | Old behavior is reintroduced under catch-all fallback. | Add explicit rejection/absence checks where contractual. |
| **Invented deprecation** | Never-required support is kept for an imaginary migration. | Remove it directly when authorized and verified. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
