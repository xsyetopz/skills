# Failure modes and recovery

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **UI thread violation** | Widget accessed from background job. | Use Display async/sync execution with disposed checks. |
| **Disposed resource use** | Delayed callback uses widget/color/image after owner closes. | Check owner/display/resource and cancel callback. |
| **Scheduling-rule omission** | Concurrent workspace jobs corrupt/conflict. | Use workspace APIs/rules for affected resources. |
| **OSGi classpath leak** | Code relies on transitive/unexported package. | Declare correct imports/exports and target dependencies. |
| **Plain-JVM proof** | Mocks pass while bundle/extension wiring fails. | Add PDE/Tycho host test. |
| **p2 incompleteness** | Feature/repository misses bundle/dependency. | Install clean artifact and resolve. |

## Recovery discipline

Preserve the first useful error and the state that produced it. Stop dependent
work when a prerequisite is false. Change strategy when another equivalent edit
or retry cannot produce new evidence. Undo only attributable experimental
changes; never reset or overwrite unrelated user work to obtain a clean result.

Do not convert a failure into success by swallowing the error, weakening the
assertion, regenerating an unexplained snapshot, adding speculative fallback
behavior, or reporting an intermediate checkpoint as the completed task.
