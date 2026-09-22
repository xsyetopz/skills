# Extension design decisions for Neovim Lua Plugin

Use this guide after inspecting the request and target system for Neovim plugin.
It selects an evidence path; it does not grant permission for an external write
or another consequential operation.

| Condition | Action | Do not substitute |
| --- | --- | --- |
| Personal one-off mapping requested | Edit config, not create a plugin. | Plugin scaffold. |
| Async result targets buffer | Capture buffer + changedtick/generation; schedule and revalidate. | Using current buffer on completion. |
| Autocmds need reload safety | Use named augroup and clear only that group. | Global autocmd clear. |
| libuv/job used | Define stop/close/wait and error/exit handling. | Garbage-collection hope. |
| Feature requires newer API | Gate declared minimum version or provide evidenced compatibility. | pcall catch-all fallback. |
| UI state is ephemeral | Use namespaces/extmarks and deterministic cleanup. | Persistent global tables without lifecycle. |

## Unresolved decisions

A material scope, compatibility, interface, deployment, or policy choice for the
Neovim plugin remains user-owned when repository evidence does not settle it.
Present concrete alternatives and consequences. Resolve routine internal details
that do not change an external contract.

## Avoiding false precision

Use thresholds, limits, versions, and acceptance criteria that govern the Neovim
plugin. If none exists, report measurements or uncertainty. Do not invent a
timeout, reviewer count, confidence score, target, or error budget and then
treat it as a requirement.
