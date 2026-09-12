---
name: neovim-plugin-development
description: >-
  Build, repair, or review Neovim plugins using Lua, runtimepath, buffer,
  event, and resource lifecycle ownership. Use when implementing or
  diagnosing Neovim plugin commands, autocmds, mappings, LSP integration,
  packaging, or headless host behavior.
---

# Neovim Plugin Development

Select this workflow automatically when the task matches its description.
Selection supplies guidance only; it does not authorize operations beyond the
user's request.

Resolve the minimum Neovim version, runtimepath layout, public Lua modules, and
commands. Use supported host APIs and Lua syntax.

- Read [runtime and ownership](references/runtime-and-ownership.md) for loading,
  positions, undo, callbacks, and resource lifecycle.
- Read [integration and validation](references/integration-and-validation.md)
  for LSP, diagnostics, health, real-host tests, help, and distribution.

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
