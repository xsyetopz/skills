---
name: eclipse-plugin-development
description: >-
  Build or diagnose Eclipse plug-ins and RCP/PDE integrations across OSGi
  lifecycle, target-platform, UI, resource, and packaging behavior.
---

# Eclipse Plugin Development

Resolve the target platform, execution environment, and affected OSGi bundles.
Compile against the declared target. Align `MANIFEST.MF`, `plugin.xml`, and
`build.properties`.

Read [runtime and distribution][ref-1] for identity, imports/exports, target
resolution, Tycho, and p2. Read
[jobs and resources](references/jobs-and-resources.md) for SWT, scheduling
rules, cancellation, services, and persistence.

Keep activation cheap. Bind listeners, jobs, services, and owned SWT resources
to their lifecycle. Update widgets on their Display thread. Re-check disposal
before queued UI work. Avoid model-lock/UI wait cycles.

Run checks for changed bundle behavior. Use API baselines for exported API
changes and clean-target resolution for p2 changes. Inspect packaged assets. Use
the [Tycho starter][ref-2] for scaffolding.

[ref-1]: references/runtime-and-distribution.md
[ref-2]: assets/tycho-plugin-template/TEMPLATE.md
