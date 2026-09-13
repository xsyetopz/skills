---
name: sublime-plugin-development
description: >-
  Build or diagnose Sublime Text packages across embedded Python, commands,
  events, edit ownership, reload lifecycle, resources, tests, and packaging.
---

# Sublime Plugin Development

Resolve the supported Sublime builds and embedded Python environments. Select
syntax and APIs supported by that range.

- Read [runtime and editing](references/runtime-and-editing.md) when changing
  commands, embedded Python compatibility, asynchronous work, or reload.
- Read [packaging and validation](references/packaging-and-validation.md) when
  changing resources, syntax definitions, tests, or distribution.

Choose TextCommand, WindowCommand, or ApplicationCommand by target. Keep each
`Edit` inside its text-command invocation. Apply asynchronous results through a
fresh command after checking view validity and change count.

Add lifecycle state only when the feature needs it. Invalidate pending
generations and remove callbacks/workers on unload. Use Sublime resource APIs
for packed assets. Keep user overrides separate from package defaults.

Check the changed command's result and undo in the real host; test reload or
asynchronous cleanup when affected. Inspect package-relative archive paths for
distribution changes. Use the [starter](assets/package-template/TEMPLATE.md) for
scaffolding.
