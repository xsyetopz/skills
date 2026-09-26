package org.acme.wordstats

import com.intellij.openapi.progress.ProgressManager
import com.intellij.psi.PsiComment
import com.intellij.psi.PsiElement
import com.intellij.psi.PsiFile
import com.intellij.psi.PsiPlainText
import com.intellij.psi.PsiRecursiveElementWalkingVisitor

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
