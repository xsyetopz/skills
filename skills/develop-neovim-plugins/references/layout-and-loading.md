# Layout and loading

Cards for where plugin files live, when Neovim runs them, and which Lua
dialect they must be written in. Every example is part of the runnable
plugin in [`assets/examples/lineup/`](../assets/examples/lineup/); run
`sh assets/examples/verify.sh` (set `NVIM` to the binary if it is not on
`PATH`).

Verification tier for this file: **Executed** with Neovim 0.12.5 (official
macOS arm64 release tarball, sha256 `65fb0000…1f9b` matching the GitHub
release digest), LuaJIT 2.1.1774638290, and PUC Lua 5.5.1, on an Apple M1
Max running macOS 27.0. The LuaRocks card is **structure-checked only**
(`luarocks` is not installed here). Help text is quoted from the v0.12.5
`runtime/doc` files.

## Contents

- Runtimepath plugin layout
- Lazy loading from plugin/
- Load guard variable
- Filetype plugin
- Lua 5.1 and LuaJIT compatibility
- vim.loader byte-code cache
- LuaRocks rockspec

## Runtimepath plugin layout

**Definition.** A plugin is a directory on `'runtimepath'`. Neovim has no
manifest or registration step ([lua-plugin-new][lua-plugin]): at startup it
sources `plugin/**/*.{vim,lua}` of every runtimepath entry (`.vim` first,
then `.lua`, alphabetically per directory; [load-plugins][starting]);
`require("x.y")` finds `lua/x/y.lua` or `lua/x/y/init.lua`; the `FileType`
event sources `ftplugin/<filetype>.lua`; `:help` finds tags generated from
`doc/*.txt` by `:helptags`.

**Use when.**

- Any code that must be available to users of an installed plugin.
- Choose each directory by trigger: startup (`plugin/`), first `require`
  (`lua/<name>/`), filetype (`ftplugin/`), documentation (`doc/`),
  `:checkhealth <name>` (`lua/<name>/health.lua`).

**Do not use when.**

- The request is a personal mapping or option in the user's own config:
  edit `init.lua`; a plugin directory adds loading and documentation
  obligations for no gain.
- Adding an empty `ftplugin/` or a `setup()` "just in case": skip what
  the feature has no content for (for example no filetype behavior).
- Committing `doc/tags`: it is generated per install by `:helptags`, and
  `:helptags` silently overwrites it ([helptags][helphelp]).

**Example.**

```text
lineup/
  plugin/lineup.lua        startup: commands and <Plug> maps only
  lua/lineup/init.lua      implementation, loaded on first use
  lua/lineup/config.lua    defaults, vim.g + setup() merge, validation
  lua/lineup/util.lua      pure Lua 5.1 helpers (no vim)
  lua/lineup/health.lua    :checkhealth lineup
  ftplugin/lineuplog.lua   buffer-local behavior for filetype lineuplog
  doc/lineup.txt           :help lineup (run :helptags on doc/)
  tests/minimal_init.lua   adds only this plugin to 'runtimepath'
  tests/run.lua            headless suite
  lineup-scm-1.rockspec    optional LuaRocks package description
```

Runnable: `assets/examples/lineup/`.

**Cost removed.** Wrong-directory bugs: code in `lua/` that never runs,
or code in `plugin/` that runs for every user at startup. Metric: the
suite's first test (`package.loaded.lineup == nil` after startup), and
`:scriptnames`, which lists every sourced `plugin/` file.

**Verify.**

1. `cd assets/examples/lineup && nvim --clean --headless -u
   tests/minimal_init.lua -l tests/run.lua` prints
   `ok   lazy startup: commands and maps exist, lineup not loaded` and
   `21 passed, 0 failed`.
1. Installed-layout check: `sh assets/examples/verify.sh package` copies
   only `plugin lua ftplugin doc` into a new directory, runs `nvim --clean
   --headless --cmd "set rtp^=<dir>" -l tests/installed_check.lua`, and
   prints `PASS installed layout: lineup` (command, ftplugin, health
   module, `:helptags` plus `:help :LineupFilter`). A source checkout can
   mask a file missing from the release archive.

## Lazy loading from plugin/

**Definition.** `plugin/<name>.lua` runs at every startup, so it only
defines commands, `<Plug>` mappings, and autocmds; each callback calls
`require()` itself, so the implementation module loads on first use
([lua-plugin-defer-require][lua-plugin]). The help states that plugin
managers' lazy-loading "do the same amount of work", so there is no
performance reason to ask users to configure lazy loading.

**Use when.**

- The plugin has any `plugin/` entry point.
- A top-level `local x = require("<name>")` appears in `plugin/`.

**Do not use when.**

- The work must run at startup (for example registering a filetype with
  `vim.filetype.add`): keep that code small and heavy modules out of it.
- Hiding the `require` in `vim.schedule` or a `VimEnter` autocmd to
  "defer" it: the module still loads at every startup, only later.

**Example.**

```lua
if vim.g.loaded_lineup then
  return
end
vim.g.loaded_lineup = true

vim.api.nvim_create_user_command("LineupJson", function(cmd)
  require("lineup").json_lines(0, cmd.line1, cmd.line2)
end, {
  range = true,
  desc = "Replace the range with one JSON array of its lines",
})

vim.keymap.set("n", "<Plug>(LineupJson)", "<Cmd>LineupJson<CR>", {
  desc = "lineup: JSON-encode the current line",
})
```

Runnable: `assets/examples/lineup/plugin/lineup.lua`.

**Cost removed.** Module loads during startup. `--startuptime` writes one
`require('<module>')` line per module loaded ([--startuptime][starting]).
Metric (`sh verify.sh startup`, Neovim 0.12.5, M1 Max, shared machine):
`require('lineup...')` lines lazy=0, eager=3 (the `eager-require` mutant
adds one top-level `require`, which pulls in `lineup`, `lineup.config`,
`lineup.util`). `plugin/lineup.lua` self+sourced time was 0.107 ms lazy
versus 0.827 ms eager in one run; treat milliseconds as machine-specific
noise and the line count as the metric.

**Verify.**

1. `sh assets/examples/verify.sh startup` prints
   `startup require('lineup...') lines: lazy=0 eager=3`.
1. In any plugin: `nvim --clean -u tests/minimal_init.lua --startuptime
   st.log +qa` then `grep -c "require('<name>" st.log` must print `0`.
1. `sh assets/examples/verify.sh mutants` prints
   `killed eager-require: ... 'lazy startup: commands and maps exist,
   lineup not loaded'`.

## Load guard variable

**Definition.** A `vim.g.loaded_<name>` check at the top of
`plugin/<name>.lua` returns early when the variable is set. It prevents a
second initialization when the file is sourced again (`:runtime!`, a
plugin manager reload) and lets users disable the plugin by setting the
variable before startup ([lua-plugin-filetype][lua-plugin] shows the same
pattern).

**Use when.**

- Every `plugin/` file that creates commands, maps, or autocmds.

**Do not use when.**

- As a substitute for idempotent registration: the guard does not stop
  jobs, timers, or closures created earlier, and `package.loaded[x] = nil`
  does not either. Registration must still be safe to repeat (`force` is
  the default for `nvim_create_user_command`; augroups use `clear = true`).
- In `ftplugin/`: use the buffer variable `b:did_ftplugin` there (see
  Filetype plugin); a global guard would run the ftplugin for the first
  buffer only.

**Example.**

```lua
if vim.g.loaded_lineup then
  return
end
vim.g.loaded_lineup = true
```

Runnable: top of `assets/examples/lineup/plugin/lineup.lua`.

**Cost removed.** Duplicate registrations after re-sourcing. Metric: the
count of `<Plug>(LineupJson)` entries in `nvim_get_keymap("n")` stays 1
even after the guard is cleared and the file is sourced again.

**Verify.**

1. The suite test `re-sourcing plugin/ is idempotent` runs
   `:runtime! plugin/lineup.lua` twice (once with the guard cleared) and
   asserts one normal-mode `<Plug>(LineupJson)` map and a working command.
1. User opt-out: `nvim --clean -u tests/minimal_init.lua --cmd
   "let g:loaded_lineup = 1" --headless -c "echo exists(':LineupJson')"
   -c qa` prints `0`.

## Filetype plugin

**Definition.** `ftplugin/<filetype>.lua` runs each time a buffer's
`'filetype'` is set to `<filetype>`. It must only affect the current
buffer and its window ([ftplugin][usr41]): guard with `b:did_ftplugin`,
set local options and buffer-local maps, and store the commands that undo
them in `b:undo_ftplugin`, which `$VIMRUNTIME/ftplugin.vim` executes before
the next filetype's plugin runs ([undo_ftplugin][usr41]).

**Use when.**

- Behavior is specific to one filetype, or to a buffer the plugin owns and
  labels with its own filetype ([lua-plugin-filetype][lua-plugin]).
- For a plugin-owned buffer, set `'filetype'` last, after creating the
  buffer and window, so user `FileType` autocmds can override your options.

**Do not use when.**

- The filetype belongs to someone else (for example `ftplugin/lua.lua`)
  and you set `b:did_ftplugin`: when your directory precedes `$VIMRUNTIME`
  on `'runtimepath'`, `$VIMRUNTIME/ftplugin/lua.vim` (which checks
  `b:did_ftplugin`) and user ftplugins that check it are skipped. For
  other plugins' filetypes, use a differently named file such as
  `ftplugin/lua_<name>.lua` (sourced by the `ftplugin/{name}_*.lua`
  pattern in `$VIMRUNTIME/ftplugin.vim`) without the guard, or a
  `FileType` autocmd.
- Global options or global maps: they leak to every later buffer.

**Example.**

```lua
if vim.b.did_ftplugin then
  return
end
vim.b.did_ftplugin = 1

vim.opt_local.wrap = false
vim.opt_local.number = false
vim.keymap.set("n", "q", "<Cmd>close<CR>", {
  buf = 0,
  desc = "lineup: close the log window",
})

vim.b.undo_ftplugin = "setlocal wrap< number<"
  .. " | silent! nunmap <buffer> q"
```

Runnable: `assets/examples/lineup/ftplugin/lineuplog.lua`, opened by
`:LineupLog`.

**Cost removed.** Settings leaking across buffers. Metric: after
`:set filetype=text` in the same buffer, the map is gone
(`maparg("q", "n")`) and `wrap` is back to the global value
(`vim.wo[win].wrap`).

**Verify.**

1. Suite test `ftplugin: local options and map, undone on filetype
   change` asserts `wrap=false` in the log window, `wrap=true` in the other
   window, a buffer-local `q`, and both undone after a filetype change.
1. `sh verify.sh mutants` shows `no-undo-ftplugin` (no `b:undo_ftplugin`)
   and `global-option` (`vim.o.wrap` instead of `vim.opt_local.wrap`) both
   killed by that test.

## Lua 5.1 and LuaJIT compatibility

**Definition.** "Lua 5.1 is the permanent interface for Nvim Lua"; later
dialects and extensions such as `goto` are unsupported, and LuaJIT
extensions (`ffi`, `jit.*`) must be guarded with `if jit then`
([lua-compat][lua]). A standalone `lua` on the machine is often 5.4 or
5.5, which accepts code that Neovim rejects.

**Use when.**

- Writing any plugin Lua, including pure helper modules unit-tested
  outside Neovim.
- Avoid: `//` integer division, `&`, `|`, `~`, `<<`, `>>` (use
  `require("bit")`, always available per [lua-bit][lua]), the `utf8`
  library, `table.unpack` (use `unpack`), `goto`, integer/float subtypes
  (`math.type`), and `<const>`/`<close>` attributes.

**Do not use when.**

- Testing only under PUC Lua 5.4+: the suite passes and Neovim fails.
  The dialect is the target language, not an option.

**Example.**

```lua
-- Pure helper that runs under LuaJIT and PUC Lua alike.
function M.prefix_matches(candidates, prefix)
  local out = {}
  for _, name in ipairs(candidates) do
    if name:sub(1, #prefix) == prefix then
      out[#out + 1] = name
    end
  end
  return out
end
```

Runnable: `assets/examples/lineup/lua/lineup/util.lua` and
`tests/util_spec.lua`.

**Cost removed.** Runtime errors that a non-Neovim test run cannot see.
Recorded under `nvim -l` (LuaJIT 2.1.1774638290): `table.unpack` and
`utf8` are nil; `return 7 // 2` fails to parse ("unexpected symbol near
'/'"); `goto` parses (LuaJIT extension, still unsupported by the
contract).

**Verify.**

1. Run pure tests under both runtimes: `lua tests/util_spec.lua` and
   `nvim --clean -l tests/util_spec.lua`; both print `PASS util_spec`.
1. `sh verify.sh pure` applies `mutants/lua54-only.patch` and prints
   `lua54-only: passes under Lua 5.5.1, fails under nvim: attempt to call
   field 'unpack' (a nil value)`.

## vim.loader byte-code cache

**Definition.** `vim.loader.enable()` (added in 0.9, [news-0.9][news09])
replaces the default module loader with one that byte-compiles and caches
Lua modules; the help marks it "experimental/unstable" ([vim.loader][lua]).
It is a process-wide switch.

**Use when.**

- In a user's own `init.lua`, when `--startuptime` shows `require()` lines
  dominating startup.

**Do not use when.**

- Inside a plugin: it changes module loading for the whole editor and
  every other plugin.
- As a fix for eager `require` in `plugin/`: caching makes an unneeded
  load cheaper; deferring removes it (see Lazy loading from plugin/).

**Example.**

```lua
-- User init.lua, first line.
vim.loader.enable()
```

**Cost removed.** Parse/compile time of cached modules on later
startups. Metric: `nvim --startuptime a.log +qa` with and without the
line (run each twice; the first enabled run fills the cache), comparing
the `require(...)` self times. Not measured here; no numbers are
claimed.

**Verify.**

1. `nvim --clean --headless -c 'lua vim.loader.enable();
   print(vim.loader.enabled)' -c qa` printed `true` here. `enabled` is a
   field in [`runtime/lua/vim/loader.lua`][loader-src], not in the help.
1. Compare `--startuptime` logs as above on the user's machine.

## LuaRocks rockspec

**Definition.** A rockspec is a Lua file named
`<package>-<version>.rockspec`. Its mandatory fields are `package`,
`version` (for example `scm-1`: version plus rockspec revision), `source`,
and `source.url`; `build.type = "builtin"` installs the Lua files mapped in
`build.modules` (module name to path) and copies `build.copy_directories`
as they are (default `{"doc"}`; never name `lua`, `lib`, or
`rock_manifest` there) ([rockspec format][rockspec]).
`:h lua-plugin-versioning` suggests LuaRocks when a plugin has
dependencies or build steps ([lua-plugin-versioning][lua-plugin]).

**Use when.**

- The plugin depends on other rocks, has a build step, or is meant to be
  a dependency of other plugins.

**Do not use when.**

- The repository already publishes another way and the task did not ask
  for LuaRocks: a second release channel expands the scope.
- Publishing (`luarocks upload`) without explicit authorization.

**Example.**

```lua
rockspec_format = "3.0"
package = "lineup"
version = "scm-1"
source = { url = "git+https://github.com/OWNER/lineup" }
description = { summary = "Encode or filter Neovim buffer lines" }
dependencies = { "lua >= 5.1" }
build = {
  type = "builtin",
  modules = {
    ["lineup"] = "lua/lineup/init.lua",
    ["lineup.config"] = "lua/lineup/config.lua",
    ["lineup.health"] = "lua/lineup/health.lua",
    ["lineup.util"] = "lua/lineup/util.lua",
  },
  copy_directories = { "doc", "ftplugin", "plugin" },
}
```

Runnable: `assets/examples/lineup/lineup-scm-1.rockspec`.

**Cost removed.** Packages missing `plugin/`, `ftplugin/`, or `doc/`, or
mapping a module to a file that does not exist. Metric:
`tests/rockspec_check.lua` checks both and prints
`PASS rockspec: 4 modules, 3 directories`.

**Verify.**

1. `lua tests/rockspec_check.lua` (run by `sh verify.sh pure`): mandatory
   fields, file name, every mapped path, and no reserved directory name.
   **Executed.**
1. `luarocks lint lineup-scm-1.rockspec` and `luarocks make` in a temporary
   tree, then load the installed plugin in a clean runtimepath. **Not
   runnable here:** `luarocks` is not installed; unexecuted.

[helphelp]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/helphelp.txt
[loader-src]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/lua/vim/loader.lua
[lua]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt
[lua-plugin]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua-plugin.txt
[news09]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/news-0.9.txt
[rockspec]: https://github.com/luarocks/luarocks/blob/main/docs/rockspec_format.md
[starting]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/starting.txt
[usr41]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/usr_41.txt
