# Neovim runtime, events and resource ownership

Research: 2026-09-09. Latest stable examined: **Neovim 0.12.5**
([release][ref-1]); pinned [Lua help][ref-2] and [API help][ref-3]. Use APIs
available at the minimum supported version and LuaJIT-compatible syntax.

## Runtime layout and public API

A runtimepath plugin typically uses `plugin/example.lua` for lightweight
commands, `lua/example/init.lua` for `require("example")`, `ftplugin/` for
buffer-local filetype behavior, `doc/example.txt` for help and
`lua/example/health.lua` for health checks. It has no universal package
manifest; plugin managers consume repository/runtimepath layouts. Do not require
a specific manager to expose a Lua API.

Keep startup registration cheap and defer expensive work to a command or
`setup()`. `require` caches modules; clearing `package.loaded` during
development does not automatically remove old autocmds, jobs or callbacks. A
user command can defer implementation:

```lua
vim.api.nvim_create_user_command('ExampleInspect', function(opts)
  require('example').inspect(opts.args)
end, { nargs = '?', desc = 'Inspect the current buffer' })
```

Namespace commands and mappings. Expose `<Plug>` mappings or explicit opt-in
defaults without overriding existing user maps. Filetype options belong to the
buffer and need matching undo behavior in `b:undo_ftplugin` if changed by
ftplugins. [Runtime conventions][ref-4].

## Idempotent setup and scheduled callbacks

```lua
local M = {}
local defaults = { enabled = true }
function M.setup(opts)
  M.config = vim.tbl_deep_extend('force', {}, defaults, opts or {})
  local group = vim.api.nvim_create_augroup('ExampleInspect', { clear = true })
  vim.api.nvim_create_autocmd('BufWritePost', {
    group = group,
    callback = function(event)
      local buf = event.buf
      local tick = vim.api.nvim_buf_get_changedtick(buf)
      vim.schedule(function()
        if not vim.api.nvim_buf_is_valid(buf) or
            not vim.api.nvim_buf_is_loaded(buf) then return end
        if vim.api.nvim_buf_get_changedtick(buf) ~= tick then return end
        -- Read/apply current work for this buffer here.
      end)
    end,
  })
end
return M
```

The fragment copies defaults and replaces the owned augroup. Add analysis inside
the guarded callback. `vim.schedule` changes callback context; it does not make
the original buffer or result current. Many fast-event/libuv callbacks cannot
call ordinary editor APIs, and textlock can prohibit edits. Use
scheduling/`vim.schedule_wrap` where needed, then re-check identity at use. [Lua
event-loop constraints][ref-2].

## Positions, edits and async jobs

Most `nvim_buf_*` row/column APIs use zero-based indices and byte columns;
cursor APIs have their own indexing rules. LSP characters may count UTF-16
units. Do not reuse one integer domain without conversion, especially for
emoji/non-ASCII text. `nvim_buf_set_lines` uses an exclusive end row;
`nvim_buf_set_text` updates a byte range. Define undo and selection behavior for
multi-edit commands. Use extmarks with explicit gravity to track positions
across edits. Clear only the owned namespace. [API indexing][ref-3].

For external tools,
`vim.system({ 'tool', '--arg', value }, { text = true }, callback)` uses
argument arrays and returns a SystemObj. Callback results expose code, signal,
stdout and stderr; return to scheduled context before editor mutation. Avoid
`.wait()` on the interactive path. For older hosts use the supported
jobstart/jobstop interface, accounting for its chunked output semantics. Guard
APIs unavailable at the minimum supported version.

Use per-buffer generations for cancellation/coalescing. On close/setup teardown,
stop owned jobs and close libuv timers/pipes/watchers (`stop` then `close` as
appropriate); a scheduled callback can still fire, so also invalidate its
generation. Do not retain every visited buffer indefinitely in a module table.

## LSP, diagnostics and health

On supporting hosts, `vim.lsp.config` defines a client and `vim.lsp.enable`
enables activation; older plugins may use `vim.lsp.start` or established
lspconfig conventions. Choose the LSP setup API supported by the target version.
Specify command, root detection and filetypes; do not start one server for every
buffer if a workspace client can be reused. Diagnostics use a plugin-owned
namespace and `vim.diagnostic.set/reset`. Honor client position encoding when
applying protocol results. [LSP help](https://neovim.io/doc/user/lsp/).

Expose `check()` from `lua/example/health.lua`, using
`vim.health.start/ok/warn/error` to report missing prerequisites with a concrete
resolution. Keep health checks read-only. Help files need unique `*example-tag*`
tags and `:helptags` generation. [Health](https://neovim.io/doc/user/health/),
[help authoring](https://neovim.io/doc/user/helphelp/).

## Debug and distribute

For an isolated check, use temporary XDG config/data/state/cache directories and
explicit runtimepath; use the starter’s minimal-init smoke route.
`nvim --headless -u tests/minimal_init.lua -l tests/smoke.lua` runs that script
with the selected host. Use `:messages`, `:scriptnames`, `:checkhealth example`,
`:verbose command ExampleInspect` and `:verbose autocmd ExampleInspect` to
locate loading/registration issues. Run repeated setup, close/stale-result and
minimum-version cases only when affected.

Inspect the distributed repository/archive for runtime files, help and required
assets; generated local caches do not belong in the package. Check event
ordering in Neovim. Refresh a specific newer API or minimum-host behavior when
needed.

[ref-1]: https://github.com/neovim/neovim/releases/tag/v0.12.5
[ref-2]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt
[ref-3]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/api.txt
[ref-4]: https://neovim.io/doc/user/usr_05/
