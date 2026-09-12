# Runtime, editing, and resource ownership

## Version and layout

As of 2026-09-11, the latest stable examined is
[Neovim 0.12.5](https://github.com/neovim/neovim/releases/tag/v0.12.5). The
installed host's help is authoritative for its API surface. Online development
help can describe newer behavior. Declare and test the minimum host separately;
do not set it to the newest installed release without a feature requirement.

Use LuaJIT-compatible syntax, not syntax available only in a newer standalone
Lua. A normal runtimepath plugin needs no invented manifest or a particular
plugin manager. `plugin/` registers lightweight commands; `lua/` exposes modules
loaded by `require`; `ftplugin/` provides filetype-local behavior; `doc/`
contains help. Add each directory only when the feature uses it. A synchronous
command with no configuration needs neither a `setup()` API nor a configuration
module.

Check built-in commands and maintained plugins before adding another feature.
For JSON, paths, process execution, diagnostics, or LSP, prefer the host's
supported facilities over custom serializers or protocols. The
[starter](../assets/plugin-template/TEMPLATE.md) uses `vim.json.encode`; it does
not invent escaping rules or another serialization format.

Keep public names distinct. Register commands with `nvim_create_user_command`
and defer implementation with `require` when appropriate. Do not override user
keymaps by default; offer explicit mappings or `<Plug>` targets when useful.
Filetype options and mappings must remain buffer-local, with appropriate
`b:undo_ftplugin` cleanup. See the
[runtime conventions][source-4].

## Positions, edits, and undo

Most buffer API indices are zero-based; rows and byte columns have different
contracts. Cursor rows are one-based, while cursor columns are zero-based byte
offsets. Ex command ranges are one-based and inclusive. Convert at the API
boundary, not by scattering adjustments through the implementation.

`nvim_buf_set_lines` has an exclusive end row. `nvim_buf_set_text` uses
end-inclusive rows and end-exclusive byte columns; it is useful when only part
of a line changes. LSP character offsets can instead be UTF-8, UTF-16, or UTF-32
units. Use the client's negotiated encoding when applying protocol edits.
Exercise non-ASCII input and boundaries where multiple edits change later
offsets.

Keep a user's operation one undoable edit when the feature requires it. Do not
use `undojoin` indiscriminately: it can merge the operation into an unrelated
user edit. Test undo and redo against actual buffers. For fixtures, Neovim's
[undo-block guidance][source-1]
describes closing an undo block with `let &undolevels = &undolevels`.

`nomodifiable` forbids buffer edits. `readonly` concerns writing files and does
not by itself prohibit in-memory editing. Do not confuse these options or add
contradictory fallback behavior. Let synchronous host APIs enforce their
existing contracts; guard state explicitly when deferred work can invalidate an
earlier assumption. See the
[API contracts][source-3].

Extmarks can track positions through intervening edits. Set gravity according to
the feature; tracking a position is not proof that the text at that position
still matches the original request. Clear only the namespace you own.

## Setup and async lifecycle

If configuration/setup creates resources, make repeated calls replace or reuse
owned resources instead of duplicating them. `nvim_create_augroup` with
`clear = true` can replace an owned group's handlers. It is not permission to
clear unrelated autocmds. A loaded flag or `package.loaded` reset does not
cancel jobs, timers, old closures, or scheduled results.

Many libuv/fast-event callbacks cannot call ordinary editor APIs, and textlock
can prohibit edits. Use `vim.schedule` or `vim.schedule_wrap` when crossing to
an allowed context. Scheduling is not freshness validation. Capture the buffer
number at request time instead of later using buffer `0`, which means whichever
buffer is current when the callback runs.

For asynchronous edits, capture immutable input, buffer identity, changedtick,
and a request generation when requests can supersede each other. Before apply,
check that the buffer remains valid and loaded, the generation is current, and
the text has not changed. Respect current modifiability. A valid buffer number
alone does not prove a result is still applicable. Check again at the actual
edit boundary if another callback can intervene.

### RED — DO NOT: apply an asynchronous result to the current buffer

**Deciding condition:** A formatter can finish after the user switches or edits
buffers, so the request and target buffer can become stale.

```lua
vim.system({ "formatter", path }, {}, function(result)
  vim.schedule(function()
    vim.api.nvim_buf_set_lines(0, 0, -1, false, result.stdout)
  end)
end)
```

Why RED:

- buffer `0` is resolved when the callback runs, not when work starts;
- the user may have switched buffers or edited the original text;
- process failure can replace the buffer because the exit status is ignored.

### GREEN — DO: retain identity and reject stale work

```lua
local buffer = vim.api.nvim_get_current_buf()
local changedtick = vim.api.nvim_buf_get_changedtick(buffer)
local lines = vim.api.nvim_buf_get_lines(buffer, 0, -1, false)
local input = table.concat(lines, "\n")

vim.system({ "formatter", path }, { stdin = input }, function(result)
  vim.schedule(function()
    if result.code == 0
      and vim.api.nvim_buf_is_valid(buffer)
      and vim.api.nvim_buf_get_changedtick(buffer) == changedtick then
      local output = result.stdout:gsub("\n$", "")
      vim.api.nvim_buf_set_lines(
        buffer,
        0,
        -1,
        false,
        vim.split(output, "\n", { plain = true })
      )
    end
  end)
end)
```

Why GREEN:

- the callback targets the initiating buffer;
- changed text prevents stale replacement;
- immutable input corresponds to the result being applied;
- a failed formatter cannot replace the buffer.

Check:

- in a headless host test, delay completion, edit or switch the buffer, and
  verify the stale callback does not change either buffer.

`vim.system` on supporting hosts accepts an argument list and an optional
completion callback. Prefer it over a shell command assembled from filenames.
Failure to start throws synchronously, distinct from a started process exiting
nonzero. Inspect exit code, signal, stdout, and stderr; schedule editor mutation
from its completion callback. Do not call `.wait()` on an interactive async
path. For a minimum host without this API, evaluate the supported job APIs and
their chunked output semantics before adding a compatibility wrapper.

Own jobs and libuv handles. On buffer teardown or reconfiguration, stop/kill
owned work and stop/close applicable timers, pipes, or watchers. Invalidate
request identity too: a completion can already be scheduled when cancellation
runs. Do not retain every visited buffer in an unbounded global table. Avoid
inventing generations, workers, or teardown for a purely synchronous feature.
See the
[Lua/event-loop help][source-2].

[source-1]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/undo.txt
[source-2]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt
[source-3]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/api.txt
[source-4]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/usr_05.txt
