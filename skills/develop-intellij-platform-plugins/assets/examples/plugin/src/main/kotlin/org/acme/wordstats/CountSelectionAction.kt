package org.acme.wordstats

import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.components.service
import com.intellij.openapi.progress.currentThreadCoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

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
