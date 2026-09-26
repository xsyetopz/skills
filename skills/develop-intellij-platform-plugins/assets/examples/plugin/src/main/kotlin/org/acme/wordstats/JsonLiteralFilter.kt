package org.acme.wordstats

import com.intellij.json.psi.JsonFile
import com.intellij.psi.PsiFile

/**
 * Uses a class from the JSON plugin, so it is registered only in
 * org.acme.wordstats-withJson.xml, the optional dependency's file.
 */
class JsonLiteralFilter : WordFilter {
    override fun accepts(word: String, file: PsiFile): Boolean =
        file !is JsonFile || word !in JSON_LITERALS
}

private val JSON_LITERALS = setOf("true", "false", "null")
