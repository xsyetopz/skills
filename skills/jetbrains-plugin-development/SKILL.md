---
name: jetbrains-plugin-development
description: >-
  Use only when explicitly invoked by name. Build, repair, or review IntelliJ
  Platform plugins with IDE compatibility, descriptors, PSI/threading, and
  lifecycle constraints.
---

# JetBrains Plugin Development

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

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
