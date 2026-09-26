package org.acme.wordstats

import java.net.URLEncoder
import java.nio.charset.StandardCharsets

// Pure logic: no platform imports, so it compiles and runs without an IDE.

/** Maximal runs of letters or digits in [text], in order. */
fun splitWords(text: CharSequence): List<String> =
    WORD.findAll(text).map { it.value }.toList()

/** UTF-8 `application/x-www-form-urlencoded` form of [text]. */
fun encodeFormValue(text: String): String =
    URLEncoder.encode(text, StandardCharsets.UTF_8)

private val WORD = Regex("""[\p{L}\p{N}]+""")
