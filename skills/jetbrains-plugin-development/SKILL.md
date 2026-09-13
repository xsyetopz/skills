---
name: jetbrains-plugin-development
description: >-
  Build or diagnose IntelliJ Platform and JetBrains IDE plugins across
  compatibility, descriptors, PSI, threading, lifecycle, and packaging.
---

# JetBrains Plugin Development

Resolve supported IDE products/builds and compatible Java, Kotlin, and Gradle
versions. Align `plugin.xml` runtime dependencies with compilation dependencies.
`since-build` and `until-build` describe IDE compatibility.

Read [compatibility and lifecycle][ref-1] when changing descriptors, builds,
resource ownership, persistence, or distribution. Read
[PSI and threading](references/psi-and-threading.md) when accessing the program
structure model (PSI), editing documents, or changing asynchronous work.

Re-resolve PSI pointers after asynchronous work. Check document stamps and
project disposal before applying results. Keep EDT callbacks and read actions
short. Bind listeners, coroutines, and UI resources to a plugin-owned lifetime.
Propagate cancellation.

Use platform tests to check the changed result, undo, and failure behavior where
applicable. Use a sandbox IDE for UI and unload behavior. Run Plugin Verifier
across affected supported
products/builds for compatibility changes. Inspect the ZIP and patched
descriptor for packaging changes. Use the
[starter](assets/plugin-template/TEMPLATE.md) for scaffolding.

[ref-1]: references/compatibility-and-lifecycle.md
