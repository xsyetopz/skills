package org.acme.wordstats

import com.intellij.openapi.Disposable
import com.intellij.openapi.application.ModalityState
import com.intellij.openapi.application.ReadAction
import com.intellij.openapi.application.readAction
import com.intellij.openapi.application.readActionBlocking
import com.intellij.openapi.command.WriteCommandAction
import com.intellij.openapi.command.writeCommandAction
import com.intellij.openapi.components.Service
import com.intellij.openapi.components.service
import com.intellij.openapi.editor.Document
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile
import com.intellij.psi.PsiManager
import com.intellij.util.concurrency.AppExecutorUtil
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

/**
 * Light project service. The platform injects [cs]: it is cancelled when
 * the project closes or the plugin unloads. The constructor stores
 * references only; no work, no service lookups.
 */
@Service(Service.Level.PROJECT)
class WordStatsService(
    private val project: Project,
    private val cs: CoroutineScope,
) : Disposable {

    /** Counts off the EDT and reports; the caller returns at once. */
    fun countInBackground(file: VirtualFile): Job = cs.launch {
        val count = countWords(file) ?: return@launch
        project.service<ProjectWordStats>().record(file.url, count)
        project.service<WordStatsReporter>().report(file.name, count)
    }

    /** Write-allowing read: restarted when a write action arrives. */
    suspend fun countWords(file: VirtualFile): Int? = readAction {
        if (!file.isValid) return@readAction null
        PsiManager.getInstance(project).findFile(file)?.let(::countPsiWords)
    }

    /** Write-blocking read: never restarted; keep the block tiny. */
    suspend fun fileLength(file: VirtualFile): Int? = readActionBlocking {
        if (file.isValid) file.length.toInt() else null
    }

    /** Non-coroutine callers: cancellable read, result on the EDT. */
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

    /** One undoable command from a coroutine; runs on the EDT. */
    suspend fun appendSummary(document: Document, count: Int) {
        writeCommandAction(project, "Append Word Count") {
            document.insertString(document.textLength, "\nwords: $count")
        }
    }

    /** One undoable command from EDT code such as actionPerformed. */
    fun appendSummaryOnEdt(document: Document, count: Int) {
        WriteCommandAction.runWriteCommandAction(
            project,
            "Append Word Count",
            null,
            { document.insertString(document.textLength, "\nwords: $count") },
        )
    }

    // expireWith(this) cancels pending non-blocking reads on dispose.
    override fun dispose() = Unit
}
