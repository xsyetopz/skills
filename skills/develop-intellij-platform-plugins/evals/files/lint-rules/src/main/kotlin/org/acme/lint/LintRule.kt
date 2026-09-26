package org.acme.lint

import com.intellij.psi.PsiFile

data class LintProblem(val offset: Int, val message: String)

interface LintRule {
    val id: String
    fun check(file: PsiFile): List<LintProblem>
}
