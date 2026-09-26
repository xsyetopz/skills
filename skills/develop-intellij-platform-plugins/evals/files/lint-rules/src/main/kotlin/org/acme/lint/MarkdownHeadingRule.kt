package org.acme.lint

import com.intellij.psi.PsiFile
import com.intellij.psi.util.PsiTreeUtil
import org.intellij.plugins.markdown.lang.psi.impl.MarkdownFile
import org.intellij.plugins.markdown.lang.psi.impl.MarkdownHeader

class MarkdownHeadingRule : LintRule {
    override val id = "markdown-heading-level"

    override fun check(file: PsiFile): List<LintProblem> {
        if (file !is MarkdownFile) return emptyList()
        var previous = 0
        return PsiTreeUtil.findChildrenOfType(file, MarkdownHeader::class.java).mapNotNull { h ->
            val skipped = previous != 0 && h.level > previous + 1
            previous = h.level
            if (skipped) LintProblem(h.textOffset, "Heading level skips from ${previous - 1}") else null
        }
    }
}
