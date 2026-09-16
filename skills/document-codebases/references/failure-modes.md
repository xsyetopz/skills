# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Aspirational docs** | Planned behavior is described as available. | Tie claims to released/current source and label future work. |
| **Command invention** | A remembered command differs from project tooling. | Inspect scripts/config and execute the canonical command. |
| **Formatting scope creep** | Reflowing Markdown changes commands, tables, or meaning. | Preserve semantics and report factual defects separately. |
| **Snippet fragments** | Examples omit imports, files, working directory, or expected result. | Provide complete runnable context or label as partial. |
| **Diagram drift** | A diagram no longer matches dependencies or state transitions. | Verify against source and update both together. |
| **Secret exposure** | Real credentials or internal endpoints enter examples. | Use approved placeholders and review diffs/history. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
