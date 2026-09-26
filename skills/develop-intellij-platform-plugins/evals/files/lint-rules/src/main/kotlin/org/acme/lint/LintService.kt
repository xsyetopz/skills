package org.acme.lint

import com.intellij.openapi.components.Service
import com.intellij.psi.PsiFile

@Service(Service.Level.APP)
class LintService {
    private val rules: List<LintRule> = listOf(TrailingSpaceRule(), MarkdownHeadingRule())

    fun lint(file: PsiFile): List<LintProblem> = rules.flatMap { it.check(file) }
}
