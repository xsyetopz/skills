---
name: neovim-plugin-development
description:
  Build, repair, or review Neovim Lua/runtimepath plugins with buffer, event,
  and resource lifecycle ownership.
---

# Neovim Plugin Development

Resolve the minimum Neovim version, runtimepath layout, public Lua modules, and
commands. Use supported host APIs and Lua syntax.

Read [runtime and events][ref-1] for loading, setup, positions, jobs,
diagnostics, LSP, help, testing, and distribution.

Keep `plugin/` startup lightweight and load `lua/` implementation on demand.
Make setup idempotent. Own augroups and namespaces; clear only owned resources.
Scope filetype settings and mappings to their intended buffers.

Schedule editor mutation from restricted callbacks. Re-check buffer validity,
loaded state, changedtick, and request generation before applying results. Stop
jobs and close owned timers, pipes, and watchers at teardown.

Verify affected behavior with an isolated configuration and runtimepath. Check
the minimum supported host for API changes. Use the
[starter](assets/plugin-template/TEMPLATE.md) for scaffolding.

[ref-1]: references/events-and-verification.md
