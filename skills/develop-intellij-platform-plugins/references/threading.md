# Threading: EDT, background threads, read and write actions

Cards for the IntelliJ Platform threading model. One application-wide
read-write lock guards model data (PSI, VFS, project model). Writes
happen only on the EDT, inside a write action; reads need a read action
unless they run on the EDT ([threading model][threading]). Excerpts come
from `assets/examples/plugin/src/main/`.

Tier: Executed for cards citing a test (light tests through
`verify.sh network`: IntelliJ IDEA OSS 2026.2.2, build 262.10315.125,
Gradle plugin 2.19.0, macOS arm64). Cards marked Compiled built with
kotlinc 2.4.20 against the 2026.2.2 jars in `verify.sh offline` and
passed Plugin Verifier 1.410, but no test calls them. API presence was
checked with `javap` on the 2026.2.2 jars.

## Contents

- EDT and background threads
- Forbidden slow operations on the EDT
- readAction (write-allowing, suspending)
- readActionBlocking (write-blocking, suspending)
- ReadAction.nonBlocking
- ReadAction.computeBlocking (replaces ReadAction.compute)
- Object validity across read actions
- writeCommandAction and writeAction in coroutines
- WriteCommandAction.runWriteCommandAction on the EDT
- Dispatchers.EDT, Default, and IO
- currentThreadCoroutineScope in actionPerformed
- Task.Backgroundable (Progress API)

## EDT and background threads

**Definition.** The single Event Dispatch Thread (EDT) handles UI events
and model writes; background threads (BGT) are many. On the EDT, code
run through `Application.invokeLater()` holds the write-intent lock
implicitly (2023.3+), so it may read without a read action and may start
write actions ([threading]).

**Use when.**

- Deciding where each step runs: UI updates and short writes on the EDT;
  file traversal, PSI parsing, reference resolution, index queries,
  network, and process I/O on a BGT.
- Checking the current thread with `Application.isDispatchThread()`.

**Do not use when.**

- Scheduling model writes through `SwingUtilities.invokeLater`. In
  2023.3+ only `Application.invokeLater()` or `Dispatchers.EDT` give the
  write-intent lock and modality state ([threading]).
- Acquiring or releasing locks directly: "must never be done by plugins"
  ([threading]).

**Example.** The split `WordStatsService` uses: the read runs on a BGT,
and the result reaches the UI later.

```kotlin
fun countInBackground(file: VirtualFile): Job = cs.launch {
    val count = countWords(file) ?: return@launch   // BGT, read action
    project.service<ProjectWordStats>().record(file.url, count)
    project.service<WordStatsReporter>().report(file.name, count)
}
```

Runnable: `WordStatsService.kt`.

**Cost removed.** UI freezes: every write waits for EDT work, and every
EDT read blocks typing. Investigate freezes with the platform's freeze
reports ([UI freezes blog][freezes]) and the Thread Access Info plugin
([threading]).

**Verify.**

1. `WordStatsTest.testServiceScopeCountsAndTestReporterRecords`.
1. Add `ThreadingAssertions.assertBackgroundThread()` or
   `assertEventDispatchThread()` at a boundary under test and run
   `gradle test`. Not added in this example.

## Forbidden slow operations on the EDT

**Definition.** VFS traversal, PSI parsing, reference resolution, and
index queries must not run on the EDT.
`SlowOperations.assertSlowOperationsAreAllowed()` reports some of these;
the assertion is active in EAP builds, internal mode, and development
instances ([threading]).

**Use when.**

- Reviewing `actionPerformed`, listeners, renderers, and `update()` for
  file, PSI, index, or network work.

**Do not use when.**

- "Fixing" the assertion by wrapping the call in a read action on the
  EDT. The work still blocks the UI; move it to a BGT (coroutine,
  `ReadAction.nonBlocking`, or `Task.Backgroundable`).
- Doing heavy work in listeners. They should only clear caches or
  schedule background processing ([threading]).

**Example.** The action does no PSI work; it hands the file to a service
scope:

```kotlin
override fun actionPerformed(e: AnActionEvent) {
    val project = e.project ?: return
    val file = e.getData(CommonDataKeys.VIRTUAL_FILE) ?: return
    project.service<WordStatsService>().countInBackground(file)
}
```

Runnable: `CountWordsAction.kt`.

**Cost removed.** `SlowOperations` exceptions in EAP and internal mode,
and freezes for users. Target: 0 assertion reports in `idea.log`.

**Verify.**

1. Enable internal mode (`idea.is.internal=true` in the sandbox
   `idea.properties`, per [internal mode][internal]), run `runIde`,
   invoke the action, then `grep -c SlowOperations idea.log`: expect 0.
   Not executed.
1. Code review: `rg -n 'findFile|accept\(|FilenameIndex' <action files>`
   inside `update`/`actionPerformed` bodies: expect none.

## readAction (write-allowing, suspending)

**Definition.** `suspend fun <T> readAction(block: () -> T): T` (2024.1+)
runs `block` under the read lock on the calling dispatcher. A write
action request cancels and restarts the attempt; cancelling the calling
coroutine throws `CancellationException` ([coroutine read
actions][cra]). Note the naming: in coroutine code the unsuffixed name
gives writes priority, while in blocking code `runReadAction` blocks
writes ([cra]).

**Use when.**

- Reading PSI/VFS from a coroutine off the EDT, for work of any length
  that can safely restart.

**Do not use when.**

- The block has side effects outside the model and cannot restart. Move
  the side effects after the read.
- The block needs indexes. Use `smartReadAction(project) { }`, which
  waits for smart mode ([cra]).
- Suspending inside the block. It is impossible by design ([cra]).
- Throwing `ProcessCanceledException` by hand. Call
  `ProgressManager.checkCanceled()` instead ([cra]).

**Example.**

```kotlin
/** Write-allowing read: restarted when a write action arrives. */
suspend fun countWords(file: VirtualFile): Int? = readAction {
    if (!file.isValid) return@readAction null
    PsiManager.getInstance(project).findFile(file)?.let(::countPsiWords)
}
```

The walker calls `ProgressManager.checkCanceled()` on every element, so
restarts happen promptly (`PsiWords.kt`).

Runnable: `WordStatsService.kt`, `PsiWords.kt`.

**Cost removed.** Typing latency during long reads: a pending write
cancels the read instead of waiting for it ([threading]).

**Verify.**

1. `WordStatsTest.testServiceScopeCountsAndTestReporterRecords` (runs
   `countWords` through the service scope).
1. `rg -n 'runReadAction' src/main`: expect no hits in coroutine code.

## readActionBlocking (write-blocking, suspending)

**Definition.** `suspend fun <T> readActionBlocking(block: () -> T): T`
runs `block` under the read lock, is cancelled only with the calling
coroutine, and blocks pending writes until it finishes ([cra]).

**Use when.**

- The block is a few field reads that must not be restarted.

**Do not use when.**

- The block walks PSI, resolves, or loops over files. Pending writes
  (and typing) wait for all of it; use `readAction`.

**Example.**

```kotlin
/** Write-blocking read: never restarted; keep the block tiny. */
suspend fun fileLength(file: VirtualFile): Int? = readActionBlocking {
    if (file.isValid) file.length.toInt() else null
}
```

Runnable: `WordStatsService.kt`.

**Cost removed.** Repeated restarts of a tiny block under write-heavy
load. The block runs once per call, and the test gets 5.

**Verify.**

1. `NotificationAndActionTest.testWriteBlockingReadReturnsLength`:
   returns 5 for "12345".
1. Review: blocks passed to `readActionBlocking` contain no loops.

## ReadAction.nonBlocking

**Definition.** `ReadAction.nonBlocking(Callable)` returns a
`NonBlockingReadAction` that runs on a background executor, restarts on
writes, and expires via `expireWith(Disposable)` or
`expireWhen(BooleanSupplier)`. It can wait for smart mode
(`inSmartMode(project)`) and deliver on the EDT
(`finishOnUiThread(ModalityState, consumer)`) ([threading]).

**Use when.**

- Non-coroutine code (Java, or Kotlin targeting < 2024.1) needs a long
  read off the EDT.
- A background thread needs a cancellable read right away:
  `.executeSynchronously()` (see the `Task.Backgroundable` card).

**Do not use when.**

- Kotlin in a coroutine on 2024.1+. `readAction` replaces `submit`,
  `expireWith`, and `finishOnUiThread` ([cra]).
- `finishOnUiThread` would carry PSI to the EDT. Pass pure data
  (strings, counts, pointers) ([cra]).

**Example.**

```kotlin
fun countNonBlocking(file: VirtualFile, onResult: (Int) -> Unit) {
    ReadAction.nonBlocking<Int?> {
        PsiManager.getInstance(project).findFile(file)
            ?.let(::countPsiWords)
    }
        .expireWith(this)
        .expireWhen { !file.isValid }
        .finishOnUiThread(ModalityState.defaultModalityState()) {
            if (it != null) onResult(it)
        }
        .submit(AppExecutorUtil.getAppExecutorService())
}
```

Runnable: `WordStatsService.kt`.

**Cost removed.** EDT freezes from long reads, and callbacks that run
after the service is disposed or the file is deleted. In the test the
callback arrives on the EDT; that no callback runs after `dispose` is
not tested.

**Verify.**

1. `WordStatsTest.testNonBlockingReadDeliversOnEdt` pumps the EDT queue
   until the callback delivers 2.
1. Check that `expireWith` names a `Disposable` with the right lifetime
   (here the project service).

## ReadAction.computeBlocking (replaces ReadAction.compute)

**Definition.** `ReadAction.computeBlocking(ThrowableComputable)` runs a
computation in a blocking read action from any thread, at most once, and
pending writes do not cancel it. `ReadAction.compute` and
`ReadAction.run` became `@Deprecated` in 2026.1 (branch 261); the
Javadoc points to `nonBlocking` or `computeBlocking`
([ReadAction.java at 261][ra-261]). The SDK threading page still shows
`ReadAction.compute`.

**Use when.**

- EDT code, modal-progress code, or tests need a short synchronous read.
- The target platform is 2026.1+. Older targets lack `computeBlocking`
  (absent from branch 253 sources); keep `compute` there.

**Do not use when.**

- Non-trivial work on a background thread. The Javadoc says to avoid it
  there because it "will likely cause UI freezes"
  ([ReadAction.java at 261][ra-261]); use `nonBlocking(...)`.

**Example.** From `WordStatsTest.kt`:

```kotlin
val file = myFixture.configureByText("notes.txt", "alpha beta\ngamma")
assertEquals(3, ReadAction.computeBlocking<Int, Throwable> {
    countPsiWords(file)
})
```

Runnable: `WordStatsTest.kt`.

**Cost removed.** Deprecation warnings that fail `-Werror` builds.
`javac -Xlint:deprecation` flagged `ReadAction.compute` in
`CountFileTask.java` against 2026.2.2 until it was replaced.

**Verify.**

1. `WordStatsTest.testCountsPlainTextWords`.
1. `sh assets/examples/verify.sh offline`: `javac -Xlint:all -Werror`
   passes.

## Object validity across read actions

**Definition.** An object read in one read action may be invalid in the
next: another thread can delete the file or reparse the PSI in between.
Check `isValid()` at the start of every read action ([threading]). To
keep a PSI reference across actions or plugin unloads, store a
`SmartPsiElementPointer` ([dynamic plugins][dynamic]).

**Use when.**

- A `VirtualFile`, `PsiElement`, `Project`, or `Module` crosses a
  suspension point, a thread switch, or a `finishOnUiThread`.

**Do not use when.**

- The value is pure data (string, offset, count); it needs no check.
- Storing raw PSI in a long-lived field. Store a pointer or an id.

**Example.**

```kotlin
suspend fun countWords(file: VirtualFile): Int? = readAction {
    if (!file.isValid) return@readAction null      // re-check each read
    PsiManager.getInstance(project).findFile(file)?.let(::countPsiWords)
}
```

```kotlin
.expireWhen { !file.isValid }                     // NBRA variant
```

Runnable: `WordStatsService.kt`.

**Cost removed.** `PsiInvalidElementAccessException` and
`InvalidVirtualFileAccessException` after concurrent edits or deletes.
Expect 0 of these names in `idea.log` or test output.

**Verify.**

1. Review: every `readAction`/`nonBlocking` block that receives a
   `VirtualFile` or PSI checks validity first.
1. A heavy test that deletes the file between calls. Not written.

## writeCommandAction and writeAction in coroutines

**Definition.** `writeCommandAction(project, name) { }` (package
`com.intellij.openapi.command`) runs the block from a suspending context
as an undoable command inside a write action on the EDT.
`writeAction { }` (package `com.intellij.openapi.application`) is the
suspending write action without a command ([threading]). Document
changes must be inside a command ([documents]).

**Use when.**

- A coroutine computed a result off the EDT and now applies it as a
  document or PSI change users undo in one step (`writeCommandAction`).
- Non-undoable model writes, such as VFS or project model changes
  (`writeAction`).

**Do not use when.**

- Computing inside the write block. Writes run on the EDT, so keep only
  the mutation inside ([threading]).
- Compute and write must see the same model state. Use
  `readAndWriteAction { ... writeAction { } }`, which guarantees no
  write in between ([cra]).
- Your Plugin Verifier policy treats experimental API as a problem. This
  run reported `CoroutinesKt.writeCommandAction` as "Experimental API
  method" (1 usage); use `WriteCommandAction` from the EDT instead.

**Example.**

```kotlin
/** One undoable command from a coroutine; runs on the EDT. */
suspend fun appendSummary(document: Document, count: Int) {
    writeCommandAction(project, "Append Word Count") {
        document.insertString(document.textLength, "\nwords: $count")
    }
}
```

Runnable: `WordStatsService.kt` (`appendSummary`).

Tier: Compiled. No test calls `appendSummary`: a light test blocks the
EDT, and this call needs the EDT, so it would deadlock.

**Cost removed.** An undo history with one entry per edit, and
`Write access is allowed inside write-action only` errors. Expected: one
Edit | Undo entry per call, named "Append Word Count".

**Verify.**

1. `gradle verifyPlugin`: reports the experimental usage and says
   "Compatible" (this run).
1. For behavior, use the EDT variant's test (next card).

## WriteCommandAction.runWriteCommandAction on the EDT

**Definition.** `WriteCommandAction.runWriteCommandAction(project, name,
groupId, runnable)` executes `runnable` as one command in a write
action; nested commands merge into the outermost one ([documents]).

**Use when.**

- EDT code (Java, or blocking Kotlin) modifies documents or PSI.
- The file may be read-only: call
  `ReadonlyStatusHandler.ensureFilesWritable()` before writing
  ([documents]).

**Do not use when.**

- The caller is a background thread. Writes are EDT-only ([threading]).
- The action is an editor action. `EditorWriteActionHandler` already
  provides the write action and command (see
  [actions and PSI](actions-psi.md)).

**Example.**

```kotlin
fun appendSummaryOnEdt(document: Document, count: Int) {
    WriteCommandAction.runWriteCommandAction(
        project,
        "Append Word Count",
        null,
        { document.insertString(document.textLength, "\nwords: $count") },
    )
}
```

Runnable: `WordStatsService.kt` (`appendSummaryOnEdt`).

**Cost removed.** Edits that cannot be undone, or that undo in several
steps. In the test, one `ACTION_UNDO` restores the text.

**Verify.**

1. `WordStatsTest.testWriteCommandIsOneUndoStep`: one `Undo` restores
   the original text.
1. Strings passed to `insertString` use only `\n` line breaks
   ([documents]).

## Dispatchers.EDT, Default, and IO

**Definition.** `Dispatchers.Default` runs CPU work, with parallelism
capped at the core count. `Dispatchers.IO` runs blocking I/O.
`Dispatchers.EDT` runs on the Swing EDT with the context's modality
state. In 2025.1+, `Dispatchers.Main` forbids read and write actions
([dispatchers]).

**Use when.**

- Switching inside one coroutine with `withContext(...)` instead of
  nested `launch` or `invokeLater` chains ([tips]).
- Wrapping only the blocking call itself in
  `withContext(Dispatchers.IO)` ([dispatchers]).

**Do not use when.**

- Platform-aware code would use `Dispatchers.Main`. Prefer
  `Dispatchers.EDT` ([dispatchers]).
- Non-I/O parsing runs inside `Dispatchers.IO`. Leave IO as soon as the
  I/O finishes ([dispatchers]).

**Example.**

```kotlin
currentThreadCoroutineScope().launch {
    val count = withContext(Dispatchers.Default) {
        splitWords(text).size
    }
    project.service<WordStatsReporter>().report("selection", count)
}
```

Runnable: `CountSelectionAction.kt`.

**Cost removed.** Thread oversubscription and nested callback chains.
`rg` for `Dispatchers.Main` and `SwingUtilities.invokeLater` returns 0
hits.

**Verify.**

1. `NotificationAndActionTest.testSelectionCountRunsInActionCoroutine`.
1. `rg -n 'Dispatchers.Main|SwingUtilities.invokeLater' src/main`:
   expect no hits.

## currentThreadCoroutineScope in actionPerformed

**Definition.** `currentThreadCoroutineScope()` (package
`com.intellij.openapi.progress`, 2024.2+ for actions) returns a scope
the action system controls and can cancel. Coroutines launched from
`actionPerformed` belong to that action invocation ([launching]).

**Use when.**

- Work started by one action invocation that should stop when the
  action system cancels it.

**Do not use when.**

- The work must outlive the action, such as a long job with its own
  lifetime. Use the service scope ([scopes]).
- Calling `runBlockingCancellable` on the EDT. It blocks the UI; the
  docs say not to use it where a service scope works ([launching]).

**Example.**

```kotlin
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
```

Read the selection on the EDT before launching, so the coroutine gets a
`String`, not the editor.

Runnable: `CountSelectionAction.kt`.

**Cost removed.** Orphaned work after an action is cancelled. The report
arrives in the test without a service scope.

**Verify.**

1. `NotificationAndActionTest.testSelectionCountRunsInActionCoroutine`:
   the recording reporter receives `"selection" to 2`.
1. The Plugin Verifier did not flag `currentThreadCoroutineScope` as
   experimental in this run.

## Task.Backgroundable (Progress API)

**Definition.** `Task.Backgroundable(project, title, canBeCancelled)`
runs `run(ProgressIndicator)` on a BGT with status-bar progress, then
calls `onSuccess()` on the EDT; `queue()` starts it. The docs mark the
Progress API obsolete for 2024.1+ in favor of coroutines
([background processes][bgp]).

**Use when.**

- Java code or pre-2024.1 targets need visible, cancellable background
  progress.

**Do not use when.**

- Kotlin on 2024.1+. Use `withBackgroundProgress(project, title) { }`
  (package `com.intellij.platform.ide.progress`, present in 2026.2.2) in
  a service scope.
- `run()` holds one long blocking read. Use
  `ReadAction.nonBlocking(...).wrapProgress(indicator)
  .executeSynchronously()` so writes can interrupt it.

**Example.**

```java
@Override
public void run(@NotNull ProgressIndicator indicator) {
  Project project = getProject();
  // Background thread: cancellable read, restarted after each write.
  // ReadAction.compute is deprecated since 2026.1 (build 261).
  count = ReadAction.nonBlocking(() -> {
    if (!file.isValid()) {
      return 0;
    }
    PsiFile psi = PsiManager.getInstance(project).findFile(file);
    return psi == null ? 0 : PsiWordsKt.countPsiWords(psi);
  }).wrapProgress(indicator).executeSynchronously();
}
```

Runnable: `CountFileTask.java`; start with
`new CountFileTask(project, file, n -> { ... }).queue()`.
Tier: Compiled (`javac -Xlint:all -Werror`); no test queues the task.

**Cost removed.** Modal waits for long jobs; the user can cancel.
Expected in `runIde`: a status-bar progress with a cancel button (not
executed).

**Verify.**

1. `sh assets/examples/verify.sh offline`: `javac` passes with
   `-Werror`.
1. In `runIde`, the status bar shows "Counting words" with a cancel
   button. Not executed.

[threading]: https://plugins.jetbrains.com/docs/intellij/threading-model.html
[cra]: https://plugins.jetbrains.com/docs/intellij/coroutine-read-actions.html
[scopes]: https://plugins.jetbrains.com/docs/intellij/coroutine-scopes.html
[launching]: https://plugins.jetbrains.com/docs/intellij/launching-coroutines.html
[dispatchers]: https://plugins.jetbrains.com/docs/intellij/coroutine-dispatchers.html
[tips]: https://plugins.jetbrains.com/docs/intellij/coroutine-tips-and-tricks.html
[bgp]: https://plugins.jetbrains.com/docs/intellij/background-processes.html
[documents]: https://plugins.jetbrains.com/docs/intellij/documents.html
[dynamic]: https://plugins.jetbrains.com/docs/intellij/dynamic-plugins.html
[freezes]: https://blog.jetbrains.com/platform/2025/09/investigating-intellij-platform-ui-freezes/
[internal]: https://plugins.jetbrains.com/docs/intellij/enabling-internal.html
[ra-261]: https://github.com/JetBrains/intellij-community/blob/261/platform/core-api/src/com/intellij/openapi/application/ReadAction.java
