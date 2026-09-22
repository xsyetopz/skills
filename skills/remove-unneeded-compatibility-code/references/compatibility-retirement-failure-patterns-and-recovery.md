# Failure patterns and recovery for Compatibility Retirement

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

Preserve the first observable compatibility removal failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the compatibility removal appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
