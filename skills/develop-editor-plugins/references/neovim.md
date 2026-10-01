# Neovim Lua plugins

Gotchas for plugin layout, commands and mappings, buffer edits, async work,
configuration, and headless tests. Claims cite the Neovim v0.12.5 `runtime/doc`
help; check the plugin's declared minimum version before using a newer API
(`vim.system` needs 0.10, positional `vim.validate` 0.11, the `buf` key in
keymap and autocmd options 0.12; older releases use `buffer`).

## Contents

- [Layout and loading](#layout-and-loading)
- [Commands, mappings, and autocommands](#commands-mappings-and-autocommands)
- [Buffers and options](#buffers-and-options)
- [Async work](#async-work)
- [Configuration and errors](#configuration-and-errors)
- [Tests and docs](#tests-and-docs)
- [Sources](#sources)

## Layout and loading

- Mistake: `require("myplugin")` or a heavy `require` at the top of `plugin/myplugin.lua`. Fix:
  `plugin/` only defines commands and `<Plug>` maps; each callback calls `require` when it runs.
  Reason: `plugin/` files run at every startup, so top-level requires load the plugin for users who
  never call it. Check the count of `require('<name>` lines in `nvim --startuptime` output.
  [lua-plugin][lua-plugin]
- Mistake: no way to disable the plugin or guard against a second load. Fix: return early when
  `vim.g.loaded_<name>` is set, then set it. [lua-plugin][lua-plugin]
- Mistake: committing `doc/tags`. Fix: ignore it and generate it with `:helptags` on release copies;
  a committed file is overwritten by the next `:helptags`. [helptags][helphelp]
- Mistake: filetype options set from `plugin/` or `setup()`. Fix: put them in `ftplugin/<ft>.lua`
  with `vim.opt_local` and buffer-local maps, and set `b:undo_ftplugin` so they are undone when the
  filetype changes. [ftplugin][usr41]
- Mistake: `//`, `&`/`|` bitwise operators, `goto`, `utf8`, or `table.unpack` in plugin Lua. Fix:
  Neovim embeds Lua 5.1 or LuaJIT; use `math.floor(a / b)`, `require("bit")`, and `unpack`. Run pure
  helpers under both `lua` and `nvim -l` so a 5.4-only call fails in a test. [Lua
  compatibility][lua]
- Mistake: adding `vim.loader.enable()` to a plugin. Fix: leave it to the user's config; the help
  marks it experimental. [vim.loader][lua]
- Mistake: a rockspec that needs build steps or lists the wrong dependencies. Fix: keep a pure-Lua
  `*-scm-1.rockspec` and version releases with tags. [rockspec format][rockspec],
  [versioning][lua-plugin]

## Commands, mappings, and autocommands

- Mistake: binding default keys with `vim.keymap.set("n", "<leader>x")` from the plugin. Fix: expose
  `<Plug>(name-action)` mappings and let the user map them. Reason: a `<Plug>` map does nothing if
  unmapped, so defaults never collide with the user's. Buffer-local maps in plugin-owned buffers or
  `ftplugin/` files are the exception. [`<Plug>`][map], [keymaps][lua-plugin]
- Mistake: `vim.keymap.set(..., { buffer = 0 })` in deferred code. Fix: pass the captured handle;
  `0` resolves to whatever is current when the callback runs. On 0.12 the option is `buf`; `buffer`
  is deprecated. [deprecated][deprecated], [news][news]
- Mistake: `nvim_create_autocmd` without a group, or `nvim_clear_autocmds({ event = ... })` to
  de-duplicate. Fix: create the plugin's augroup with `clear = true`, pass `group`, and clear only
  that group. Reason: sourcing the file twice otherwise doubles handlers, and clearing by event
  removes other plugins' autocmds. [nvim_create_augroup][api]
- Mistake: per-buffer state or processes that outlive the buffer. Fix: a `BufWipeout` (or
  `BufDelete`) autocmd with `buffer = buf` that kills jobs and drops tables entries. [event
  args][api]
- Mistake: a command that takes `nargs = "*"` with no `complete` or range handling. Fix: set
  `nargs`, `range`, and `complete` in `nvim_create_user_command` and read `opts.fargs`,
  `opts.line1`, `opts.line2`. [nvim_create_user_command][api], [:command-nargs][map]

## Buffers and options

- Mistake: `vim.o.wrap = false` (or `vim.o.number`) for a window option. Fix: `vim.wo[win].wrap`
  with a handle, or `vim.opt_local` in `ftplugin/`. Reason: `vim.o` also sets the global value,
  which every window opened later inherits. [options in Lua][lua]
- Mistake: reading `vim.opt.x` as a value. Fix: it is an `Option` object; use `vim.o.x` or
  `vim.opt.x:get()`. Use `vim.opt.x:append()` for list options so commas are not duplicated.
  [options in Lua][lua]
- Mistake: `nvim_buf_set_lines` to change part of a line. Fix: `nvim_buf_set_text` with start and
  end positions; replacing whole lines discards extmarks on them. [nvim_buf_set_text][api]
- Mistake: one user action that needs several `u` presses. Fix: make the edits in one callback or
  join them with `:undojoin`; do not leave `'undolevels'` at `-1`. [undo blocks][undo],
  [options][options]
- Mistake: highlights and virtual text in namespace `0` or shared with other plugins. Fix:
  `nvim_create_namespace("name")` per plugin and clear with `nvim_buf_clear_namespace`; diagnostics
  get their own `vim.diagnostic` namespace. Positions are (0,0)-indexed.
  [nvim_buf_set_extmark][api], [diagnostic][diagnostic]
- Mistake: a results buffer that prompts on quit or is listed. Fix: `nvim_create_buf(false, true)`
  with `buftype=nofile`, `bufhidden=wipe`, `swapfile` off. [nvim_create_buf][api]

## Async work

- Mistake: calling `vim.api.*`, `vim.fn.*`, or `vim.cmd` inside a `vim.uv` callback or a
  `vim.system` callback. Fix: wrap with `vim.schedule` or `vim.schedule_wrap`. Reason: those run in
  a fast event context and fail with `E5560`. `vim.in_fast_event()` reports the context. [luv
  callbacks][lua], [api-fast][api]
- Mistake: building a shell string for `vim.system` with file names. Fix: pass an argument list
  (`{ "tool", "--flag", path }`), wrap the call in `pcall` because a missing executable throws, and
  check `code`. [vim.system][lua]
- Mistake: `:wait()` on the result of `vim.system` from a command or autocmd. Fix: pass an `on_exit`
  callback and schedule the result handler. Reason: `:wait()` blocks the UI until the process ends.
  [vim.system][lua]
- Mistake: applying an async result to buffer `0`, or to a buffer that changed. Fix: capture the
  handle and `nvim_buf_get_changedtick` at request time; in the callback recheck
  `nvim_buf_is_valid`, the changedtick, a request counter, and `vim.bo[buf].modifiable`. Reason: a
  stale result overwrites newer user edits, and a wiped buffer raises `Invalid buffer id`.
  [nvim_buf_get_changedtick][api]
- Mistake: superseded requests keep running. Fix: keep the `SystemObj` per buffer and call `:kill()`
  before starting the next one; the request counter above makes late results harmless.
  [SystemObj][lua]

## Configuration and errors

- Mistake: `setup()` that starts timers, registers autocmds, or requires heavy modules. Fix:
  `setup(opts)` validates and stores options; behavior starts when a command, `<Plug>` map, or
  filetype triggers it. [lua-plugin][lua-plugin]
- Mistake: requiring `setup()` for configuration. Fix: read `vim.g.<name>` as well and work with no
  configuration. Reason: `vim.g.x.y = 1` does not change the variable, so document assigning the
  whole table. [vim.g][lua]
- Mistake: `vim.validate` called with the old table form on 0.11+. Fix: use the positional form when
  the minimum version allows; report unknown keys instead of ignoring them. [news-0.11][news11],
  [deprecated][deprecated]
- Mistake: `error()` for a user-facing failure such as a missing executable. Fix:
  `vim.notify("name: message", vim.log.levels.ERROR)`; reserve `error()` for misuse of the Lua API.
  Reason: users see a stack trace instead of an actionable message. [vim.notify][lua]
- Mistake: no way to diagnose a broken setup. Fix: a `health.lua` under `lua/<name>/` using
  `vim.health.start/ok/warn/error`, run with `:checkhealth <name>`. [health][health]

## Tests and docs

- Mistake: testing editor behavior with a standalone `lua` run or a mocked `vim`. Fix: run headless
  (`nvim --clean --headless -u tests/minimal_init.lua -l tests/run.lua`) with `XDG_CONFIG_HOME`,
  `XDG_DATA_HOME`, `XDG_STATE_HOME`, and `XDG_CACHE_HOME` pointing to a temp directory. A mock
  proves only pure logic. [startup options][starting]
- Mistake: a test that waits with a fixed sleep. Fix: `vim.wait(timeout, condition)` on the state
  the callback sets. [vim.wait][lua]
- Mistake: a test that passes whether or not the fix is present. Fix: revert the fix and confirm the
  named test fails for the intended reason.
- Mistake: help file tags that do not resolve. Fix: run `:helptags` on a copy and open each new tag
  with `:help`. [help files][helphelp]
- Mistake: type annotations that LuaLS cannot see. Fix: LuaCATS `---@param`/`---@class` comments and
  a `.luarc.json` that lists the runtime. [annotations][luals-ann], [settings][luals-set]

## Sources

[api]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/api.txt
[deprecated]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/deprecated.txt
[diagnostic]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/diagnostic.txt
[health]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/health.txt
[helphelp]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/helphelp.txt
[lua]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt
[lua-plugin]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua-plugin.txt
[luals-ann]: https://luals.github.io/wiki/annotations/
[luals-set]: https://luals.github.io/wiki/settings/
[map]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/map.txt
[news]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/news.txt
[news11]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/news-0.11.txt
[options]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/options.txt
[rockspec]: https://github.com/luarocks/luarocks/blob/main/docs/rockspec_format.md
[starting]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/starting.txt
[undo]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/undo.txt
[usr41]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/usr_41.txt
