package org.acme.wordstats

import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.components.service
import com.intellij.openapi.project.DumbAwareAction

/**
 * DumbAware: counting walks PSI of one file and uses no indexes, so the
 * action stays available while indexing. No fields: one instance lives for
 * the whole application.
 */
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
