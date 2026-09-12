---
name: jetbrains-plugin-development
description: >-
  Build, repair, or review IntelliJ Platform and JetBrains IDE plugins with
  compatibility, descriptor, PSI, threading, and lifecycle constraints. Use
  when implementing or diagnosing IntelliJ IDEA, Kotlin, or other JetBrains
  plugin behavior, packaging, or host integration.
---

# JetBrains Plugin Development

Select this workflow automatically when the task matches its description.
Selection supplies guidance only; it does not authorize operations beyond the
user's request.

Resolve supported IDE products/builds and compatible Java, Kotlin, and Gradle
versions. Align `plugin.xml` runtime dependencies with compilation dependencies.
`since-build` and `until-build` describe IDE compatibility.

Read [compatibility and lifecycle][ref-1] for descriptors, build tasks,
disposal, persistence, and distribution. Read
[PSI and threading](references/psi-and-threading.md) for read/write actions,
undo, indexing, and cancellation.

Re-resolve PSI pointers after asynchronous work. Check document stamps and
project disposal before applying results. Keep EDT callbacks and read actions
short. Bind listeners, coroutines, and UI resources to a plugin-owned lifetime.
Propagate cancellation.

Run focused platform checks. Run Plugin Verifier across affected supported
products/builds for compatibility changes. Inspect the ZIP and patched
descriptor for packaging changes. Use the
[starter](assets/plugin-template/TEMPLATE.md) for scaffolding.

[ref-1]: references/compatibility-and-lifecycle.md
