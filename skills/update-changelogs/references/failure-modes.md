# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Commit-log dump** | Entries repeat commit messages without user impact. | Inspect diffs/issues/behavior and synthesize. |
| **Invented release** | Date/version/state is fabricated. | Keep Unreleased/draft or obtain decision. |
| **Internal inflation** | Refactor becomes feature/performance/security claim. | Limit to observed effect. |
| **Breaking-by-label** | Conventional commit or file name decides SemVer. | Check actual public contract. |
| **Publication conflation** | Text update is reported as released/deployed. | Verify provider/registry/deployment separately. |
| **Range leakage** | Entries include work outside start/end revisions. | Record and audit exact range. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
