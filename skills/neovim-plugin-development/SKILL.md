---
name: neovim-plugin-development
description: >-
  Build or diagnose Neovim plugins across Lua, runtimepath, buffers, events,
  commands, mappings, LSP integration, packaging, and resource lifecycle.
---

# Neovim Plugin Development

Resolve the minimum Neovim version, runtimepath layout, public Lua modules, and
commands. Use supported host APIs and Lua syntax.

- For loading, edits, callbacks, or resource ownership, read
  [runtime and ownership](references/runtime-and-ownership.md).
- Read [integration and validation](references/integration-and-validation.md)
  when changing LSP, diagnostics, health, help, or distribution, or setting up
  real-host tests.

Keep `plugin/` startup lightweight and load `lua/` implementation on demand. Add
setup only when needed, and make repeated calls idempotent. Own any augroups and
namespaces you create; clear only owned resources. Scope filetype settings and
mappings to their intended buffers.

Schedule editor mutation from restricted callbacks. Re-check buffer validity,
loaded state, changedtick, and request generation before applying results. Stop
jobs and close owned timers, pipes, and watchers at teardown.

Verify affected behavior with an isolated configuration and runtimepath. Check
the minimum supported host for API changes. Use the
[starter](assets/plugin-template/TEMPLATE.md) for scaffolding.
