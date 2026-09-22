# Extension failures and recovery for Eclipse OSGi Plugin

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **UI thread violation** | Widget accessed from background job. | Use Display async/sync execution with disposed checks. |
| **Disposed resource use** | Delayed callback uses widget/color/image after owner closes. | Check owner/display/resource and cancel callback. |
| **Scheduling-rule omission** | Concurrent workspace jobs corrupt/conflict. | Use workspace APIs/rules for affected resources. |
| **OSGi classpath leak** | Code relies on transitive/unexported package. | Declare correct imports/exports and target dependencies. |
| **Plain-JVM proof** | Mocks pass while bundle/extension wiring fails. | Add PDE/Tycho host test. |
| **p2 incompleteness** | Feature/repository misses bundle/dependency. | Install clean artifact and resolve. |

## Recovery discipline

Preserve the first observable Eclipse plugin failure and the state that produced
it. Stop dependent work after a false prerequisite. If another equivalent retry
cannot add evidence, change the source, instrument, or hypothesis. Undo only
task-owned experiments; preserve unrelated user work.

Do not make the Eclipse plugin appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
