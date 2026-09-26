package org.acme.todofinder

import com.intellij.openapi.actionSystem.AnAction
import com.intellij.openapi.actionSystem.AnActionEvent
import com.intellij.openapi.ui.Messages
import com.intellij.psi.PsiManager
import com.intellij.psi.search.FilenameIndex
import com.intellij.psi.search.GlobalSearchScope

class FindTodosAction : AnAction() {
    override fun update(e: AnActionEvent) {
        val project = e.project!!
        val files = FilenameIndex.getAllFilesByExt(project, "kt", GlobalSearchScope.projectScope(project))
        e.presentation.isEnabled = files.isNotEmpty()
    }

    override fun actionPerformed(e: AnActionEvent) {
        val project = e.project!!
        val psi = PsiManager.getInstance(project)
        var count = 0
        for (vf in FilenameIndex.getAllFilesByExt(project, "kt", GlobalSearchScope.projectScope(project))) {
            count += Regex("""//\s*TODO""").findAll(psi.findFile(vf)!!.text).count()
        }
        Messages.showInfoMessage(project, "$count TODO comments", "TODOs")
    }
}
