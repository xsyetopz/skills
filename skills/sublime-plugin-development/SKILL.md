---
name: sublime-plugin-development
description:
  Build, repair, or review Sublime Text packages using embedded Python,
  command/edit ownership, reload lifecycle, and packed resources.
---

# Sublime Plugin Development

Resolve the supported Sublime builds and embedded Python environments. Select
syntax and APIs supported by that range.

Read [runtime and packaging][ref-1] for loading, commands, asynchronous work,
resources, syntax definitions, debugging, and Package Control.

Choose TextCommand, WindowCommand, or ApplicationCommand by target. Keep each
`Edit` inside its text-command invocation. Apply asynchronous results through a
fresh command after checking view validity and change count.

Initialize API-dependent state through the plugin lifecycle. Invalidate pending
generations and remove callbacks/workers on unload. Use Sublime resource APIs
for packed assets. Keep user overrides separate from package defaults.

Run relevant logic and host checks. Inspect package-relative archive paths for
distribution changes. Use the [starter](assets/package-template/TEMPLATE.md) for
scaffolding.

[ref-1]: references/runtime-and-packaging.md
