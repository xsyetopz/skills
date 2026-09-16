# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Pythonization** | Non-Python code is rewritten to mimic Python constructs. | Use the target language’s explicit ownership, error, concurrency, and resource mechanisms. |
| **Line-count minimalism** | Required validation or lifecycle behavior is removed to make code shorter. | Simplify concepts, not contracts. |
| **Aphorism as verdict** | A review quotes “simple is better” without identifying a concrete defect. | Tie the principle to behavior, ownership, names, or change cost. |
| **Alias accumulation** | A rename leaves permanent old/new paths without a support decision. | Decide migration and compatibility deliberately. |
| **Abstraction purge** | Interfaces or layers are removed because they look indirect. | Inspect actual deployment, ownership, testing, and extension constraints. |
| **Comment-only clarity** | Comments explain behavior that remains needlessly implicit or wrong. | Repair executable interfaces when executable behavior is the problem. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
