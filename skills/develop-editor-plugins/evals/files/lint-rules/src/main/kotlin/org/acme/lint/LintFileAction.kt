package org.acme.lint

import com.intellij.openapi.actionSystem.ActionUpdateThread
import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.actionSystem.CommonDataKeys
import com.intellij.openapi.application.ReadAction
import com.intellij.openapi.components.service
import com.intellij.openapi.progress.ProgressManager
import com.intellij.openapi.ui.Messages

class LintFileAction : AnAction() {
    override fun getActionUpdateThread() = ActionUpdateThread.BGT

    override fun update(e: AnActionEvent) {
        e.presentation.isEnabled = e.getData(CommonDataKeys.PSI_FILE) != null
    }

    override fun actionPerformed(e: AnActionEvent) {
        val file = e.getData(CommonDataKeys.PSI_FILE) ?: return
        val problems = ProgressManager.getInstance().runProcessWithProgressSynchronously<Int, Exception>(
            { ReadAction.nonBlocking<Int> { service<LintService>().lint(file).size }.executeSynchronously() },
            "Linting", true, e.project,
        )
        Messages.showInfoMessage(e.project, "$problems problem(s)", "Acme Lint")
    }
}
