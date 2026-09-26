// Offline oracle for the platform-free logic in plugin/.../WordText.kt.
// verify.sh compiles it together with WordText.kt and runs it.
import org.acme.wordstats.encodeFormValue
import org.acme.wordstats.splitWords

private fun check(label: String, actual: Any?, expected: Any?) {
    check(actual == expected) { "$label: expected $expected, got $actual" }
    println("PASS $label")
}

fun main() {
    check("split words", splitWords("alpha, beta-2 γάμμα"),
        listOf("alpha", "beta", "2", "γάμμα"))
    check("no words", splitWords(" \t,.;"), emptyList<String>())
    check("encode space and plus", encodeFormValue("a b+c"), "a+b%2Bc")
    check("encode UTF-8", encodeFormValue("é"), "%C3%A9")
}
