# Actions, PSI, VFS, and documents

Cards for the action system and for reading the code model. Excerpts come
from `assets/examples/plugin/src/main/`.

Tier: Executed where a card cites a test (light tests through
`verify.sh network`: IntelliJ IDEA OSS 2026.2.2, build 262.10315.125,
Gradle plugin 2.19.0, macOS arm64). All example sources also compiled in
`verify.sh offline` against the 2026.2.2 jars.

## Contents

- AnAction with update on a background thread
- AnAction with update on the EDT
- Registering actions and groups
- DumbAwareAction
- EditorAction with EditorWriteActionHandler
- Walking PSI with PsiRecursiveElementWalkingVisitor
- From VirtualFile to PsiFile and Document
- Document modification rules

## AnAction with update on a background thread

**Definition.** `AnAction.update(e)` sets `e.presentation` (enabled,
visible) and runs often. Since 2022.3, `getActionUpdateThread()` picks
its thread. `ActionUpdateThread.BGT` runs it in the background with read
access to PSI, VFS, and the project model, and no access to Swing
components ([action system][actions]).

**Use when.**

- Availability depends on data-context values (`CommonDataKeys.PROJECT`,
  `VIRTUAL_FILE`, `PSI_FILE`), PSI, or project model reads. BGT is the
  preferred mode ([actions]).

**Do not use when.**

- `update` must touch Swing components. Use EDT, or
  `e.updateSession.compute(...)` to hop to the EDT ([actions]).
- The check is expensive (file system work, resolve, index queries).
  `update` must "execute very quickly"; decide in `actionPerformed` and
  tell the user if the context is wrong ([actions]).
- The class has fields. One action instance lives for the whole
  application, so fields leak projects ([actions]).

**Example.**

```kotlin
class CountWordsAction : DumbAwareAction() {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT

    // BGT update: data-context reads only; no PSI walk, no file I/O.
    override fun update(e: AnActionEvent) {
        val file = e.getData(CommonDataKeys.VIRTUAL_FILE)
        e.presentation.isEnabledAndVisible =
            e.project != null && file != null && !file.isDirectory
    }

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val file = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return
        project.service<WordStatsService>().countInBackground(file)
    }
}
```

Runnable: `CountWordsAction.kt`.

**Cost removed.** EDT time spent in `update` on every toolbar and menu
refresh. The DevKit inspection "ActionUpdateThread is missing" reports
an action that keeps the default ([actions]).

**Verify.**

1. `WordStatsTest.testCountWordsActionEnabledForFile`:
   `myFixture.testAction(CountWordsAction())` returns an enabled
   presentation.
1. `rg -n 'getActionUpdateThread' src/main`: every `AnAction` subclass
   overrides it.

## AnAction with update on the EDT

**Definition.** `ActionUpdateThread.EDT` runs `update` on the EDT, where
it may read Swing and editor UI state but "must not access PSI, VFS, or
project data" ([actions]).

**Use when.**

- Availability depends only on UI state, such as the editor selection
  model or a tree selection.

**Do not use when.**

- The check reads PSI or files. Use BGT.

**Example.**

```kotlin
class CountSelectionAction : AnAction() {
    override fun getActionUpdateThread() = ActionUpdateThread.EDT

    // EDT update: editor/Swing state is allowed; PSI and VFS are not.
    override fun update(e: AnActionEvent) {
        val editor = e.getData(CommonDataKeys.EDITOR)
        e.presentation.isEnabled =
            editor?.selectionModel?.hasSelection() == true
    }

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val editor = e.getData(CommonDataKeys.EDITOR) ?: return
        val text = editor.selectionModel.selectedText ?: return
        // 2024.2+: the action system owns and can cancel this coroutine.
        currentThreadCoroutineScope().launch {
            val count = withContext(Dispatchers.Default) {
                splitWords(text).size
            }
            project.service<WordStatsReporter>().report("selection", count)
        }
    }
}
```

Runnable: `CountSelectionAction.kt`.

**Cost removed.** Read-lock contention from UI-only checks, and a
"stuck" presentation from setting only one outcome: set both on every
call ([actions]). In the tests the presentation is disabled without a
selection and enabled with one.

**Verify.**

1. `NotificationAndActionTest.testEdtUpdateNeedsSelection`: disabled
   without a selection.
1. `NotificationAndActionTest.testSelectionCountRunsInActionCoroutine`:
   enabled with a `<selection>` marker.

## Registering actions and groups

**Definition.** `<actions>` holds `<action id class text description
icon>` and `<group id popup compact>` elements. `<add-to-group
group-id="..." anchor="first|last|before|after"
relative-to-action="...">` places them; `<keyboard-shortcut
keymap="..." first-keystroke="...">` binds keys. `id` must be unique
across all plugins, and `text` is required unless a resource bundle
supplies it ([plugin.xml reference][config]).

**Use when.**

- Adding menu, toolbar, or popup entries. Prefix ids with the plugin id.
  Platform group ids are in `PlatformActions.xml`, standard action ids
  in `IdeActions` ([actions]).

**Do not use when.**

- A group has no `id`. Dynamic plugins require one ([dynamic]).
- The action should show grayed out in a `compact` menu such as Tools.
  Disabled actions are hidden there ([actions]).
- Setting the presentation text in the action constructor. DevKit flags
  "Eager creation of action presentation" ([actions]).

**Example.**

```xml
<actions>
  <group id="org.acme.wordstats.Menu" text="Word Stats"
         popup="true">
    <add-to-group group-id="ToolsMenu" anchor="last"/>
    <action id="org.acme.wordstats.CountWords"
            class="org.acme.wordstats.CountWordsAction"
            text="Count Words in File"
            description="Count words in comments and plain text"/>
  </group>
</actions>
```

Runnable: `src/main/resources/META-INF/plugin.xml`.

**Cost removed.** Duplicate-id load errors and unplaced actions.
`check_plugin_xml.py` counts duplicate and missing ids.

**Verify.**

1. `check_plugin_xml.py`: no `duplicate action/group id` or
   `<group> without id` error.
1. `EncodeFormValueActionTest` invokes the action by its registered id,
   so the registration loaded.

## DumbAwareAction

**Definition.** During indexing ("dumb mode") only actions that
implement `DumbAware` stay available. Extend `DumbAwareAction`; do not
override `isDumbAware()` ([actions]).

**Use when.**

- The action does not query indexes: single-file PSI walks, document
  edits, settings.

**Do not use when.**

- The action resolves references, searches across files, or uses
  `FilenameIndex`; it would fail during indexing. Keep plain `AnAction`
  (hidden while indexing), or schedule the work with
  `DumbService.smartInvokeLater` or `smartReadAction` ([threading]).

**Example.** The class header and the only work it starts. The walk
touches one file's PSI tree and no index:

```kotlin
class CountWordsAction : DumbAwareAction() {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project ?: return
        val file = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return
        project.service<WordStatsService>().countInBackground(file)
    }
    // update(): see "AnAction with update on a background thread"
}
```

Runnable: `CountWordsAction.kt`, `PsiWords.kt`.

**Cost removed.** An action disabled for the whole indexing period after
project open. Expected: the action stays enabled while "Indexing..."
shows in the status bar (not executed).

**Verify.**

1. Review `actionPerformed` and its callees for index APIs
   (`rg -n 'Index|ReferencesSearch' src/main`); expect none in a
   DumbAware action.
1. A test in dumb mode (`DumbModeTestUtils`). Not written.

## EditorAction with EditorWriteActionHandler

**Definition.** `EditorAction(handler)` with
`EditorWriteActionHandler.ForEachCaret` runs `executeWriteAction` once
per caret; `isEnabledForCaret` gates each caret. The platform supplies
the write action, the undoable command, read-only file handling, and
per-caret dispatch.

**Use when.**

- A text transformation of the selection or caret positions, including
  multiple carets.

**Do not use when.**

- The change is structural (rename, move, PSI-aware refactor). Use PSI
  factories inside a write command.
- The transformation needs network or project-wide work, which must not
  run inside the write action.
- Wrapping the handler in another `WriteCommandAction`. The handler
  already runs in one.

**Example.**

```kotlin
class EncodeFormValueAction : EditorAction(Handler()) {
    private class Handler : EditorWriteActionHandler.ForEachCaret() {
        override fun isEnabledForCaret(
            editor: Editor,
            caret: Caret,
            dataContext: DataContext,
        ): Boolean = caret.hasSelection()

        override fun executeWriteAction(
            editor: Editor,
            caret: Caret,
            dataContext: DataContext,
        ) {
            val selected = caret.selectedText ?: return
            val start = caret.selectionStart
            val encoded = encodeFormValue(selected)
            editor.document.replaceString(start, caret.selectionEnd, encoded)
            caret.setSelection(start, start + encoded.length)
        }
    }
}
```

`encodeFormValue` is `URLEncoder.encode(text, UTF_8)`: a form-value
encoder, not a URL or path encoder.

Runnable: `EncodeFormValueAction.kt`, `WordText.kt`.

**Cost removed.** Hand-written write, command, and undo code and
per-caret loops. One `Undo` reverts every caret's change.

**Verify.**

1. `EncodeFormValueActionTest.testMultipleSelectionsAndSingleUndo`: two
   selections encoded, the caret without a selection untouched, one undo
   restores all.
1. `EncodeFormValueActionTest.testNoSelectionDoesNotChangeDocument`: the
   modification stamp is unchanged.

## Walking PSI with PsiRecursiveElementWalkingVisitor

**Definition.** `psiFile.accept(object :
PsiRecursiveElementWalkingVisitor() { ... })` visits every element
depth-first; `super.visitElement(element)` descends into the children
([PSI files][psi-files]). Callers need read access.

**Use when.**

- Collecting facts from one file's tree without indexes: comments, plain
  text, element counts.

**Do not use when.**

- Searching many files. Use indexes or `PsiSearchHelper` in smart mode.
- Walking without read access, or on the EDT for large files.
- Language-specific structure is needed. Use that language's PSI classes
  or visitor (`JavaRecursiveElementVisitor` and similar).

**Example.**

```kotlin
/** Counts filtered words in comments and plain text. Needs read access. */
fun countPsiWords(file: PsiFile): Int {
    val filters = wordFilters()
    var count = 0
    file.accept(object : PsiRecursiveElementWalkingVisitor() {
        override fun visitElement(element: PsiElement) {
            // Lets a write action cancel (and restart) this read.
            ProgressManager.checkCanceled()
            if (element is PsiComment || element is PsiPlainText) {
                count += splitWords(element.text).count { word ->
                    filters.all { it.accepts(word, file) }
                }
            } else {
                super.visitElement(element)
            }
        }
    })
    return count
}
```

Runnable: `PsiWords.kt`.

**Cost removed.** Custom text parsing that disagrees with the IDE's
parser; the PSI tree is the IDE's own parse. The two tests' counts (3
and 2) match it.

**Verify.**

1. `WordStatsTest.testCountsPlainTextWords`: "alpha beta\ngamma" gives 3.
1. `WordStatsTest.testExtensionFilterReadsSettings`: minimum length 5
   gives 2.

## From VirtualFile to PsiFile and Document

**Definition.** `VirtualFile` is the application-wide file handle; PSI
is project-scoped. `PsiManager.getInstance(project).findFile(vf)`
returns the `PsiFile` or null.
`FileDocumentManager.getInstance().getDocument(vf)` returns the editable
`Document`, loading it from disk if needed. `PsiDocumentManager` maps
between the two ([PSI files][psi-files], [documents]). Both lookups need
read access.

**Use when.**

- An action or service gets a `VirtualFile` from
  `CommonDataKeys.VIRTUAL_FILE` and needs its PSI or text.

**Do not use when.**

- Storing `Document` or `PsiFile` in long-lived fields. The file holds
  both weakly, so a field that holds them leaks ([documents]).
- The PSI must match uncommitted editor text. Commit first with
  `PsiDocumentManager.commitDocument` (in a write-safe context).

**Example.**

```kotlin
suspend fun countWords(file: VirtualFile): Int? = readAction {
    if (!file.isValid) return@readAction null
    PsiManager.getInstance(project).findFile(file)?.let(::countPsiWords)
}
```

Runnable: `WordStatsService.kt`.

**Cost removed.** Leaks from cached documents and PSI, and unhandled
`null` PSI: `findFile` returns null for directories and binary files.
`rg` finds no `Document`/`PsiFile` fields in services.

**Verify.**

1. `WordStatsTest.testServiceScopeCountsAndTestReporterRecords`.
1. `rg -n 'val .*: (Document|PsiFile)' src/main` in service fields:
   expect none.

## Document modification rules

**Definition.** Document changes need a write action and a command
(`CommandProcessor.executeCommand`, or `WriteCommandAction`, which wraps
both); the outermost command is one undo step. Text passed to
`insertString`/`replaceString`/`setText` must use `\n` only. A read-only
file fails unless `ReadonlyStatusHandler.ensureFilesWritable()` succeeds
first ([documents]).

**Use when.**

- Any code path that changes editor text outside an editor action
  handler.

**Do not use when.**

- The change is inside `EditorWriteActionHandler`, which already has
  the command.
- The text comes from disk with `\r\n`. Normalize with
  `StringUtil.convertLineSeparators` first.

**Example.** See `WriteCommandAction.runWriteCommandAction` in
[threading](threading.md#writecommandactionrunwritecommandaction-on-the-edt):

```kotlin
WriteCommandAction.runWriteCommandAction(
    project,
    "Append Word Count",
    null,
    { document.insertString(document.textLength, "\nwords: $count") },
)
```

Runnable: `WordStatsService.kt` (`appendSummaryOnEdt`).

**Cost removed.** Changes that bypass undo or split into several undo
steps, and write-access errors from writes outside a write action. In
the test, one `ACTION_UNDO` restores the text.

**Verify.**

1. `WordStatsTest.testWriteCommandIsOneUndoStep`.
1. `rg -n '\\r\\n' src/main`: no CRLF literals passed to documents.

[actions]: https://plugins.jetbrains.com/docs/intellij/action-system.html
[config]: https://plugins.jetbrains.com/docs/intellij/plugin-configuration-file.html
[dynamic]: https://plugins.jetbrains.com/docs/intellij/dynamic-plugins.html
[threading]: https://plugins.jetbrains.com/docs/intellij/threading-model.html
[psi-files]: https://plugins.jetbrains.com/docs/intellij/psi-files.html
[documents]: https://plugins.jetbrains.com/docs/intellij/documents.html
