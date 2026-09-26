package org.acme.header

import com.intellij.openapi.application.ApplicationManager
import com.intellij.openapi.fileEditor.FileDocumentManager
import com.intellij.openapi.project.Project
import com.intellij.openapi.vfs.VirtualFile

object HeaderInserter {
    fun addHeader(project: Project, file: VirtualFile) {
        ApplicationManager.getApplication().executeOnPooledThread {
            val doc = FileDocumentManager.getInstance().getDocument(file)!!
            if (!doc.text.startsWith("// Copyright")) {
                doc.insertString(0, "// Copyright Acme\r\n")
            }
        }
    }
}
