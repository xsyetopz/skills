# Failure patterns and recovery for Release History

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Commit-log dump** | Entries repeat commit messages without user impact. | Inspect diffs/issues/behavior and synthesize. |
| **Invented release** | Date/version/state is fabricated. | Keep Unreleased/draft or obtain decision. |
| **Internal inflation** | Refactor becomes feature/performance/security claim. | Limit to observed effect. |
| **Breaking-by-label** | Conventional commit or file name decides SemVer. | Check actual public contract. |
| **Publication conflation** | Text update is reported as released/deployed. | Verify provider/registry/deployment separately. |
| **Range leakage** | Entries include work outside start/end revisions. | Record and audit exact range. |

## Recovery discipline

Preserve the first observable changelog entry failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the changelog entry appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
