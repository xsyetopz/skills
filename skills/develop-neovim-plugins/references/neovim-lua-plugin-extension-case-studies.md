# Extension case studies for Neovim Lua Plugin

## Neovim: stale buffer-safe async publication

```lua
local bufnr = vim.api.nvim_get_current_buf()
local tick = vim.api.nvim_buf_get_changedtick(bufnr)
local generation = state.next_generation
start_job(function(result)
  vim.schedule(function()
    if generation ~= state.next_generation then return end
    if not vim.api.nvim_buf_is_valid(bufnr) then return end
    if vim.api.nvim_buf_get_changedtick(bufnr) ~= tick then return end
    apply_result(bufnr, result)
  end)
end)
```

A headless test must change or delete the buffer before callback completion. Use
plugin-owned augroups/namespaces and close jobs/handles during teardown.

## Lifecycle evidence checklist

- activate/load once and twice;
- invoke normal and failing inputs;
- start async work, then edit/close/dispose before completion;
- cancel and verify no late publication;
- unload/reload or close/reopen project/workspace;
- inspect duplicate registrations, processes, timers, handles, and persisted
  state;
- build package, inspect contents, install in a clean declared host;
- distinguish stub/unit tests from real host execution.
