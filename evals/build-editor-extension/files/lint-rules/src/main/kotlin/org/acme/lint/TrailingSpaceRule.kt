package org.acme.lint

import com.intellij.psi.PsiFile

class TrailingSpaceRule : LintRule {
    override val id = "trailing-space"

    override fun check(file: PsiFile): List<LintProblem> =
        Regex("""[ \t]+$""", RegexOption.MULTILINE).findAll(file.text)
            .map { LintProblem(it.range.first, "Trailing whitespace") }
            .toList()
}
