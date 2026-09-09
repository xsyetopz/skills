# PSI, documents, threading and actions

Research: 2026-09-09; current IntelliJ Platform SDK. Select read/coroutine APIs
supported by the minimum target platform.

## Separate read, write and command semantics

Background execution does not grant model access. Read PSI/index/model state
under the platform's read-access contract. Use target-supported cancellable read
APIs for long work. Release read access promptly so writes can proceed. A write
action grants mutation access; a command supplies undo grouping. For an editor
document change, use a write command on the supported UI context. [Threading
model][ref-1].

```kotlin
class InspectAction : AnAction() {
    override fun actionPerformed(event: AnActionEvent) {
        val project = event.project ?: return
        val editor = event.getData(CommonDataKeys.EDITOR) ?: return
        val document = editor.document
        WriteCommandAction.runWriteCommandAction(project) {
            document.insertString(editor.caretModel.offset, "example")
        }
    }
}
```

The command inserts literal text as one undo operation. Check selection and
writability when adapting it. Do not perform network I/O or a full-project scan
inside that write command. Imports are from the corresponding
`com.intellij.openapi.actionSystem`, `command` APIs. [Actions][ref-2],
[documents][ref-3].

## Asynchronous PSI pipeline

Snapshot the relevant document modification stamp and stable identity, perform
cancellable analysis under valid read access, then return to the permitted
write/UI context. Re-check project disposal, document stamp, pointer validity
and writability immediately before applying. Use `SmartPsiElementPointer` when
an element must survive reparsing; a smart pointer may resolve to null and is
not a guarantee that semantic context stayed unchanged. Avoid passing raw PSI
into long-lived caches or non-read callbacks. [PSI][ref-4].

Uncommitted document text and PSI can differ. Use `PsiDocumentManager`'s
supported commit/read coordination when the feature needs PSI corresponding to
current document text; do not assume a filesystem refresh commits editor text.
Use language-aware PSI factories and references for structural edits.

## Indexing and cancellation

Index-dependent actions must wait for smart mode or explicitly handle dumb mode.
Implement `DumbAware` only when the action's actual work does not require
unavailable indexes. `update()` runs frequently: keep it cheap, avoid expensive
resolves and declare the supported action update thread when required. A
background `update` must not touch Swing state. [Indexing and dumb mode][ref-5].

Propagate `ProcessCanceledException` and coroutine cancellation. Catching all
exceptions and retrying can make canceled read work starve writes indefinitely.
Use bounded coalescing for repeated document events, with one newest generation
per target. Do not hold a model lock while synchronously waiting for UI work
that might need it.

## Validation boundaries

Use platform fixtures for PSI/document edits and check resulting structure,
references, undo and error paths relevant to the change. Add indexing-state
cases only when behavior depends on indexes. Verify against the minimum
supported product/build for API changes and use a sandbox host for UI/lifecycle
claims. Check editor behavior with platform fixtures or the sandbox host.
Refresh the particular new read/coroutine API rather than mandating a platform
upgrade.

[ref-1]: https://plugins.jetbrains.com/docs/intellij/threading-model.html
[ref-2]: https://plugins.jetbrains.com/docs/intellij/action-system.html
[ref-3]: https://plugins.jetbrains.com/docs/intellij/documents.html
[ref-4]: https://plugins.jetbrains.com/docs/intellij/psi.html
[ref-5]: https://plugins.jetbrains.com/docs/intellij/indexing-and-psi-stubs.html
