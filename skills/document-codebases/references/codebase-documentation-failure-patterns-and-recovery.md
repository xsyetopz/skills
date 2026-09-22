# Failure patterns and recovery for Codebase Documentation

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Aspirational docs** | Planned behavior is described as available. | Tie claims to released/current source and label future work. |
| **Command invention** | A remembered command differs from project tooling. | Inspect scripts/config and execute the canonical command. |
| **Formatting scope creep** | Reflowing Markdown changes commands, tables, or meaning. | Preserve semantics and report factual defects separately. |
| **Snippet fragments** | Examples omit imports, files, working directory, or expected result. | Provide complete runnable context or label as partial. |
| **Diagram drift** | A diagram no longer matches dependencies or state transitions. | Verify against source and update both together. |
| **Secret exposure** | Real credentials or internal endpoints enter examples. | Use approved placeholders and review diffs/history. |

## Recovery discipline

Preserve the first observable codebase documentation failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the codebase documentation appear successful by swallowing its
error, weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
