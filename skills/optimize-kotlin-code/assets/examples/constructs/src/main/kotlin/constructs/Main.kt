package constructs

import kotlin.system.exitProcess

fun main(args: Array<String>) {
    val groups = mapOf(
        "inline" to InlineChecks::run,
        "representation" to RepresentationChecks::run,
        "collections" to CollectionChecks::run,
        "control" to ControlFlowChecks::run,
        "coroutines" to CoroutineChecks::run,
    )
    val selected = args.toList().ifEmpty { groups.keys.toList() }
    for (name in selected) {
        val group = groups[name]
        if (group == null) {
            System.err.println("unknown group $name; groups: ${groups.keys}")
            exitProcess(2)
        }
        println("== $name")
        group()
    }
    if (Harness.failures > 0) {
        println("FAILED ${Harness.failures} check(s)")
        exitProcess(1)
    }
    println("ALL CHECKS PASSED")
}
