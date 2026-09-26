package org.acme.wordstats

import com.intellij.openapi.components.service
import com.intellij.openapi.extensions.ExtensionPointName
import com.intellij.psi.PsiFile

/** Extension point `org.acme.wordstats.wordFilter` (interface EP). */
interface WordFilter {
    /** Returns false to drop [word] found in [file]. Runs under read. */
    fun accepts(word: String, file: PsiFile): Boolean
}

private val EP_NAME =
    ExtensionPointName<WordFilter>("org.acme.wordstats.wordFilter")

/** Enumerated on every call: nothing caches extension instances. */
internal fun wordFilters(): List<WordFilter> = EP_NAME.extensionList

/** Stateless extension: reads settings through the service each call. */
class MinLengthFilter : WordFilter {
    override fun accepts(word: String, file: PsiFile): Boolean =
        word.length >= service<WordStatsSettings>().minLength
}
