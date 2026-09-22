# Failure patterns and recovery for Cross Language PEP 20

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Pythonization** | Non-Python code is rewritten to mimic Python constructs. | Use the target language's explicit ownership, error, concurrency, and resource mechanisms. |
| **Line-count minimalism** | Required validation or lifecycle behavior is removed to make code shorter. | Simplify concepts, not contracts. |
| **Aphorism as verdict** | A review quotes “simple is better” without identifying a concrete defect. | Tie the principle to behavior, ownership, names, or change cost. |
| **Alias accumulation** | A rename leaves permanent old/new paths without a support decision. | Decide migration and compatibility deliberately. |
| **Abstraction purge** | Interfaces or layers are removed because they look indirect. | Inspect actual deployment, ownership, testing, and extension constraints. |
| **Comment-only clarity** | Comments explain behavior that remains needlessly implicit or wrong. | Repair executable interfaces when executable behavior is the problem. |

## Recovery discipline

Preserve the first observable cross-language design review failure and the state
that produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the cross-language design review appear successful by swallowing its
error, weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
