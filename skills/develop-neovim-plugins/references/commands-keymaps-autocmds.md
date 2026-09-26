# Commands, keymaps, and autocmds

Cards for the entry points users invoke and the events a plugin reacts to.
Examples come from [`assets/examples/lineup/`](../assets/examples/lineup/);
the suite `tests/run.lua` and the mutants in `assets/examples/mutants/`
prove each claim.

Verification tier for this file: **Executed** with Neovim 0.12.5 (macOS
arm64 release build on an Apple M1 Max, macOS 27.0, LuaJIT 2.1.1774638290) via
`sh assets/examples/verify.sh suite` and `... mutants`. Behavior on
Neovim 0.10 and 0.11 is taken from `news*.txt`/`deprecated.txt` and was not
executed.

## Contents

- User command with nargs and range
- Command completion function
- Plug mappings
- Buffer-local keymap
- Augroup with clear
- Buffer lifetime autocmd

## User command with nargs and range

**Definition.** `vim.api.nvim_create_user_command(name, fn, opts)` (since
0.7.0) defines a global Ex command; `name` must start with an uppercase
letter, the Lua callback receives one table (`args`, `fargs`, `bang`,
`line1`, `line2`, `range`, `count`, `smods`, ...), and `opts` takes the
`:command` attributes plus `desc`, `force` (default `true`: redefinition
replaces), `complete`, and `preview` ([nvim_create_user_command][api]).
`nargs` is `0` (default), `1`, `*`, `?`, or `+` ([:command-nargs][map]).

**Use when.**

- The feature is an action the user names (`:LineupFilter sort`), needs
  arguments or a range, or should be discoverable with `:command Lineup`.
- A mapping should call it: `<Cmd>Name<CR>` or a `<Plug>` map.

**Do not use when.**

- The command applies to one buffer only: use
  `nvim_buf_create_user_command(buf, ...)`; a global command then errors
  or acts on the wrong buffer elsewhere.
- Parsing `args` yourself when `fargs` suffices: `fargs` already splits on
  unescaped whitespace; manual splitting breaks on escaped spaces.
- Omitting `nargs` for a command that needs arguments: the default `0`
  rejects any argument.

**Example.**

```lua
vim.api.nvim_create_user_command("LineupFilter", function(cmd)
  require("lineup").filter_command(cmd.fargs)
end, {
  nargs = "+",
  desc = "Pipe the buffer through a program; apply output if unchanged",
  complete = function(arg_lead, cmd_line)
    if cmd_line:match("^%s*%S+%s+%S*$") == nil then
      return {}
    end
    return require("lineup").complete_filter(arg_lead)
  end,
})

vim.api.nvim_create_user_command("LineupJson", function(cmd)
  require("lineup").json_lines(0, cmd.line1, cmd.line2)
end, { range = true, desc = "Replace the range with one JSON array" })
```

Runnable: `assets/examples/lineup/plugin/lineup.lua`.

**Cost removed.** Argument errors discovered inside the implementation.
Metric: with `nargs = "+"`, `:LineupFilter` without arguments fails
before the callback runs, with `E471: Argument required` (recorded in the
suite). `range = true` passes `line1`/`line2` (1-based, inclusive) to the
callback, so the plugin parses no cursor positions or marks.

**Verify.**

1. Suite test `user command nargs and completion` asserts `E471` on
   `:LineupFilter` and that `nvim_get_commands({}).LineupFilter.nargs` is
   `"+"`.
1. Suite test `json encodes the range and leaves other lines` runs
   `:2,5LineupJson` and asserts lines 1 and 6 are untouched.
1. `:verbose command LineupFilter` shows `nargs`, `<Lua function>`, the
   `desc`, and `Last set from .../plugin/lineup.lua`.

## Command completion function

**Definition.** `complete` may be a Lua function `(arg_lead, cmd_line,
cursor_pos) -> string[]`; Neovim shows the returned list as candidates
([lua-guide-commands-create][lua-guide]). The function must filter:
Neovim does not filter a Lua function's list by `arg_lead` (recorded: a
command whose function returns `{ "foo", "bar" }` gives
`getcompletion("X b", "cmdline") == { "foo", "bar" }`).

**Use when.**

- Arguments come from a known set (configured programs, subcommands, file
  types) that the plugin can list cheaply.

**Do not use when.**

- Completion needs I/O or a process: it runs on the main loop at each
  `<Tab>` and blocks typing. Cache the list or use a built-in completion
  string such as `"file"`.
- Returning the same list at every argument position when candidates
  depend on it: `:LineupFilter sort -<Tab>` would offer program names as
  program arguments. Check `cmd_line` as in the example.

**Example.**

```lua
function M.complete_filter(arg_lead)
  local ok, cfg = pcall(config.get)
  if not ok then
    return {} -- invalid config: no candidates, no error while typing
  end
  return util.prefix_matches(cfg.filters, arg_lead)
end
```

Runnable: `assets/examples/lineup/lua/lineup/init.lua`.

**Cost removed.** Typos in arguments and doc lookups. Metric:
`vim.fn.getcompletion("LineupFilter s", "cmdline")` returns `{ "sort" }`
with the default config, and `{}` after the program argument.

**Verify.**

1. Suite test `user command nargs and completion` asserts both
   `getcompletion` results.
1. `mutants/lua54-only.patch` breaks the matcher under LuaJIT; the same
   test fails with `E5108: Lua function: ... attempt to call field
   'unpack' (a nil value)`.

## Plug mappings

**Definition.** `<Plug>` is a key name no keyboard produces, so a mapping
whose lhs starts with `<Plug>` can only be reached from another mapping
([<Plug>][map]). A plugin defines `<Plug>(Name)` in each mode it supports;
the user binds real keys with one `vim.keymap.set` line, which works (does
nothing) even if the plugin is missing ([lua-plugin-keymaps][lua-plugin]).

**Use when.**

- The plugin offers an action users will want on a key.
- Different modes need different behavior behind one name (normal: current
  line; visual: selection).

**Do not use when.**

- Mapping real keys by default (`<Leader>j`): it overrides the user's
  mappings. The help allows automatic maps only for buffer-local
  cases such as plugin-owned buffers ([lua-plugin-keymaps][lua-plugin]).
- The action needs many option combinations: expose a Lua function that
  takes an options table instead of dozens of `<Plug>` names.

**Example.**

```lua
-- Plugin (plugin/lineup.lua)
vim.keymap.set("n", "<Plug>(LineupJson)", "<Cmd>LineupJson<CR>", {
  desc = "lineup: JSON-encode the current line",
})
vim.keymap.set("x", "<Plug>(LineupJson)", ":LineupJson<CR>", {
  silent = true,
  desc = "lineup: JSON-encode the selected lines",
})

-- User config
vim.keymap.set({ "n", "x" }, "<Leader>j", "<Plug>(LineupJson)")
```

The visual map uses `:` (not `<Cmd>`) so Neovim inserts the `'<,'>` range.

Runnable: `assets/examples/lineup/plugin/lineup.lua`.

**Cost removed.** Key conflicts with user mappings. Metric: plugin maps
whose lhs is not `<Plug>...`: 0. The suite counts maps whose `desc`
starts with `lineup:` in modes n, x, i, o.

**Verify.**

1. Suite tests `no default mappings outside <Plug>` and `<Plug> mapping
   works in visual mode through a user map` (maps `<Leader>j`, runs
   `Vj<Leader>j`, asserts `["a","b"]`).
1. `mutants/global-keymap.patch` adds a default `<Leader>j`; the first test
   fails.
1. Interactive: `:verbose nmap <Plug>(LineupJson)` shows where it was set.

## Buffer-local keymap

**Definition.** `vim.keymap.set(mode, lhs, rhs, { buf = n })` creates a
mapping active only in buffer `n` (`0` = current) ([vim.keymap.set][lua]).
Other options: `desc` (shown by `:map` and pickers), `remap` (default
`false`), `expr`, `silent`. **Version boundary:** 0.12 renamed the key
`buffer` to `buf` in `vim.keymap.set`/`vim.keymap.del` and in
`nvim_create_autocmd`, `nvim_get_autocmds`, `nvim_exec_autocmds`,
`nvim_clear_autocmds`; the old name is still accepted
([deprecated-0.12][deprecated], [news][news]). Code that must run on 0.11
or older uses `buffer`.

**Use when.**

- The mapping belongs to a plugin-owned buffer (log, picker, preview) or
  is set from an `ftplugin/` file.

**Do not use when.**

- Global actions: users expect them in every buffer, and a buffer-local
  map is silently absent elsewhere.
- In an ftplugin without a matching `nunmap <buffer>` in
  `b:undo_ftplugin`: the map survives a filetype change.
- Writing `buf` in a plugin whose declared minimum is below 0.12: the key
  was introduced by the rename (per the 0.12 news); not executed on 0.11
  here.

**Example.**

```lua
vim.keymap.set("n", "q", "<Cmd>close<CR>", {
  buf = 0,
  desc = "lineup: close the log window",
})
```

Runnable: `assets/examples/lineup/ftplugin/lineuplog.lua`.

**Cost removed.** Mappings leaking to unrelated buffers. Metric:
`vim.fn.maparg("q", "n", false, true).buffer` is `1` in the log buffer,
and `maparg("q", "n")` is `""` after its filetype changes.

**Verify.**

1. Suite test `ftplugin: local options and map, undone on filetype
   change`.
1. `mutants/no-undo-ftplugin.patch` removes the undo string; the test
   fails.

## Augroup with clear

**Definition.** `nvim_create_augroup(name, { clear = true })` creates the
group or, if it exists, deletes its autocmds; `clear` defaults to `true`
([nvim_create_augroup][api]). Creating autocmds with `group = id` makes
the group the owner, so re-running the setup code replaces instead of
duplicating, and cleanup deletes only this plugin's handlers.

**Use when.**

- Every autocmd a plugin creates.
- Code that registers autocmds may run more than once (a function called
  per request, a re-sourced file, `setup()` called twice).

**Do not use when.**

- Passing `clear = false` where the code then adds handlers again: use
  it only to get the id of a group that another part of the same plugin
  populates.
- Clearing someone else's group or all autocmds for an event
  (`nvim_clear_autocmds({ event = ... })` without `group`): it deletes
  user and other-plugin handlers.

**Example.**

```lua
local function ensure_autocmds()
  local group = vim.api.nvim_create_augroup("lineup", { clear = true })
  vim.api.nvim_create_autocmd("BufWipeout", {
    group = group,
    desc = "lineup: drop per-buffer filter state",
    callback = function(args)
      M.forget(args.buf)
    end,
  })
end
```

Runnable: `assets/examples/lineup/lua/lineup/init.lua` (called on every
`filter()`).

**Cost removed.** Duplicate handlers: each duplicate runs the callback
again per event. Metric: `#vim.api.nvim_get_autocmds({ group = "lineup"
})` stays `1` after three filter runs; with `clear = false` it grows by
one per run.

**Verify.**

1. Suite test `autocmd group holds one handler after repeated runs`.
1. `mutants/augroup-no-clear.patch` (`clear = false`) fails that test.
1. Interactive, after one `:LineupFilter` run: `:autocmd lineup` lists
   the group's handlers with `desc` (before any run it reports `E216: No
   such group or event: lineup`, because the group is created lazily).

## Buffer lifetime autocmd

**Definition.** An autocmd callback receives `args.buf` (`<abuf>`),
`args.match`, `args.file`, `args.event`, `args.group`, `args.id`, and
`args.data` ([event-args][api]). A `BufWipeout` handler that removes
per-buffer state keyed by `args.buf` bounds plugin state to live buffers;
a callback returning a truthy value deletes its autocmd.

**Use when.**

- The plugin keeps a table keyed by buffer handle (pending requests,
  caches, attached state) or owns processes per buffer.

**Do not use when.**

- The per-buffer state can live in `vim.b[buf]` and needs no cleanup
  action: buffer variables are removed with the buffer.
- Using `nvim_get_current_buf()` inside the callback: the event's buffer
  can differ from the current one (for example `:bwipeout 5`).

**Example.**

```lua
function M.forget(buf)
  local req = pending[buf]
  pending[buf] = nil
  if req and req.proc and not req.proc:is_closing() then
    req.proc:kill("sigterm")
  end
end
-- registered as: callback = function(args) M.forget(args.buf) end
```

Runnable: `assets/examples/lineup/lua/lineup/init.lua`.

**Cost removed.** Leaked processes and unbounded tables. Metric: time from
`nvim_buf_delete` to the filter outcome; the suite starts `sleep 5`, wipes
the buffer, and requires outcome `cancelled` in under 2000 ms.

**Verify.**

1. Suite test `wiping the buffer kills the process`.
1. `mutants/no-kill.patch` leaves the process running; the test fails.

[api]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/api.txt
[deprecated]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/deprecated.txt
[lua]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt
[lua-guide]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua-guide.txt
[lua-plugin]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua-plugin.txt
[map]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/map.txt
[news]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/news.txt
