# Configuration, errors, and health

Cards for how users configure a plugin, how it reports problems, and how
`:checkhealth` diagnoses it. Examples are in
[`assets/examples/lineup/`](../assets/examples/lineup/) and
[`error_vs_notify.lua`][demo] in `assets/examples/demos/`.

Verification tier for this file: **Executed** with Neovim 0.12.5 (macOS
arm64 release build on an Apple M1 Max, macOS 27.0, LuaJIT 2.1.1774638290) via
`sh assets/examples/verify.sh suite|mutants|demos`.

## Contents

- Configuration through vim.g
- setup that only stores options
- vim.validate
- Unknown option detection
- vim.notify versus error
- Health check module

## Configuration through vim.g

**Definition.** A plugin reads a table from a global variable
(`vim.g.<name>`) when a command runs, merges it over defaults, and
validates it ([lua-plugin-init][lua-plugin]). Users can set it before or
after startup, from Lua or Vimscript, and setting it never errors when the
plugin is absent. `vim.g.x` returns a copy: mutating a nested field in
place (`vim.g.x.y = 1`) does not change the variable ([lua-vim-variables][lua]).

**Use when.**

- The plugin works with defaults and configuration is optional.
- Values should be changeable at runtime without a restart.

**Do not use when.**

- The value must hold functions or userdata that Vimscript cannot
  represent; take them through a Lua `setup()` call instead.
- Reading `vim.g` once at `require` time: later changes are ignored. Read
  it where the value is used.

**Example.**

```lua
-- lua/lineup/config.lua
M.defaults = { filters = { "sort", "uniq" }, timeout_ms = 5000 }

function M.get()
  local merged, unknown_g = util.merge(M.defaults, vim.g.lineup)
  local final, unknown_s = util.merge(merged, overrides)
  for _, key in ipairs(unknown_s) do
    unknown_g[#unknown_g + 1] = key
  end
  return M.validate(final), unknown_g
end

-- user init.lua (whole table: vim.g returns copies)
vim.g.lineup = { filters = { "sort", "jq" } }
```

Runnable: `assets/examples/lineup/lua/lineup/config.lua`.

**Cost removed.** Required `setup()` calls and init-order errors. Metric:
with no configuration, every command works (the suite does not call
`setup()` before the config test).

**Verify.**

1. Suite test `config: vim.g read at use, setup wins, bad values notify`
   sets `vim.g.lineup` after startup and asserts the next `get()` sees it.
1. Every other suite test runs with no configuration.

## setup that only stores options

**Definition.** `setup(opts)` validates and stores overrides and does
nothing else; `plugin/`, not `setup()`, creates commands, maps, and
autocmds. The help describes this split and notes that a combined
setup-and-initialize function forces every user to call it and errors in
`init.lua` when the plugin is missing ([lua-plugin-init][lua-plugin]).

**Use when.**

- Users need Lua-only values (functions, callbacks) or prefer one Lua call.
- As a second source on top of `vim.g`; document the precedence.

**Do not use when.**

- `setup()` creates autocmds, commands, or processes: calling it twice
  duplicates them, and not calling it leaves the plugin dead.
- The plugin must not act until configured (opt-in initialization): a
  combined `setup()` is then the documented exception; say so in the
  help file.

**Example.**

```lua
---@param opts lineup.UserConfig?
function M.setup(opts)
  vim.validate("opts", opts, "table", true) -- nil allowed
  overrides = opts
end
```

Runnable: `assets/examples/lineup/lua/lineup/config.lua`.

**Cost removed.** Double initialization and "plugin does nothing until
setup" reports. Metric: autocmd count and command availability do not
depend on `setup()` being called (suite tests pass without it).

**Verify.**

1. Suite config test: `setup({ timeout_ms = 10 })` makes `get().timeout_ms`
   `10`; `setup("x")` raises `opts: expected table, got string`.

## vim.validate

**Definition.** `vim.validate(name, value, validator, optional, message)`
raises `"<name>: expected <type or message>, got <value>"` when `value`
fails; `validator` is a type name (`"string"`, `"table"`, `"callable"`,
...), a list of names, or a function returning `ok, msg`
([vim.validate()][lua]). **Version boundary:** this positional form
arrived in 0.11 ([news-0.11][news11]); the table form
`vim.validate({ name = { v, "string" } })` is deprecated
([deprecated][deprecated]).

**Use when.**

- Checking arguments of public Lua functions and merged configuration.

**Do not use when.**

- The plugin supports 0.10 or older: the positional form does not exist
  there (source-based; not executed on 0.10).
- Hot paths that run per keystroke or per line: validate once at the
  boundary.

**Example.**

```lua
function M.validate(config)
  vim.validate("lineup.filters", config.filters, is_string_list)
  vim.validate("lineup.timeout_ms", config.timeout_ms, function(v)
    return type(v) == "number" and v > 0 and v % 1 == 0
  end, "positive integer")
  return config
end
```

Runnable: `assets/examples/lineup/lua/lineup/config.lua`.

**Cost removed.** Late, unclear failures. Metric: without the check
(`mutants/no-validate.patch`) `timeout_ms = "soon"` surfaces as
`vim/_core/system:337: bad argument #1 to 'start' (number expected, got
string)`; with it the user sees `lineup.timeout_ms: expected positive
integer, got soon`.

**Verify.**

1. Suite config test asserts the message text above.
1. `sh verify.sh mutants` prints `killed no-validate`.

## Unknown option detection

**Definition.** Report user keys that the defaults lack; otherwise a typo
(`timout_ms`) is silently ignored. The help suggests reporting unknown
fields, for example from a health check to keep runtime overhead down
([lua-plugin-config][lua-plugin]).

**Use when.**

- Configuration is a table of known keys.

**Do not use when.**

- The table is open by design (for example per-filetype maps keyed by
  arbitrary names): validate its values instead.
- Raising an error for unknown keys on every command: one typo would
  disable the plugin; warn in `:checkhealth` instead.

**Example.**

```lua
function M.merge(defaults, user)
  local merged, unknown = {}, {}
  for key, value in pairs(defaults) do
    merged[key] = value
  end
  for key, value in pairs(user or {}) do
    if defaults[key] == nil then
      unknown[#unknown + 1] = tostring(key)
    else
      merged[key] = value
    end
  end
  table.sort(unknown)
  return merged, unknown
end
```

Runnable: `assets/examples/lineup/lua/lineup/util.lua` (pure Lua 5.1).

**Cost removed.** Silently ignored settings. Metric: `:checkhealth lineup`
shows `WARNING unknown option: typo` for `vim.g.lineup = { typo = 1 }`.

**Verify.**

1. `lua tests/util_spec.lua` and `nvim --clean -l tests/util_spec.lua`
   (unknown keys `{ "c", "zz" }`).
1. Suite test `checkhealth reports config and filters`.

## vim.notify versus error

**Definition.** `error(msg)` raises a Lua error; inside a command
callback Neovim reports it as `Lua :command callback: <file>:<line>:
<msg>` followed by a stack traceback. `vim.notify(msg, level)` shows a
message (default provider: `nvim_echo` into `:messages`, `err = true`
for `ERROR`) and returns, so the callback keeps running
([vim.notify()][lua]).

**Use when.**

- `vim.notify` with `vim.log.levels.ERROR`/`WARN`: expected failures a
  user can fix (program exited nonzero, not found, bad config). Prefix the
  plugin name.
- `error()`: programmer errors in a Lua API (wrong argument types), where
  the traceback helps the caller; `vim.validate` raises this way.

**Do not use when.**

- `error()` for user-facing failures: the user sees a traceback into
  plugin internals.
- `vim.notify` from a fast callback without scheduling: the default
  provider raises E5560 there.
- Assuming `vim.notify(..., ERROR)` is invisible to callers: when the
  command runs through `vim.cmd` inside `pcall` (tests, other plugins),
  the error message makes `vim.cmd` raise `Vim:<msg>` after the callback
  finishes (recorded below). Tests should capture `vim.notify`.

**Example.**

```lua
vim.api.nvim_create_user_command("DemoError", function()
  error("config file missing")
end, {})
vim.api.nvim_create_user_command("DemoNotify", function()
  vim.notify("demo: config file missing", vim.log.levels.ERROR)
  after = true -- notify does not unwind the callback
end, {})
```

Runnable: `assets/examples/demos/error_vs_notify.lua`. Recorded:

```text
error():  ok=false traceback=true
  Vim:Lua :command callback: .../error_vs_notify.lua:6: config file missing
notify(): ok=false traceback=false callback finished=true
  Vim:demo: config file missing
```

**Cost removed.** Tracebacks shown for ordinary failures. Metric: the
failure message contains no `stack traceback`. The mutant
`error-not-notify.patch` raises from the scheduled callback instead; the
log then shows
`vim.schedule callback: .../init.lua:111: sh exited 3: bad` with a stack
traceback and the notify test fails.

**Verify.**

1. `sh verify.sh demos` prints the recorded lines.
1. Suite test `nonzero exit notifies and keeps the buffer` asserts one
   notification, level `ERROR`, text `lineup: sh exited 3: bad\n`.

## Health check module

**Definition.** `:checkhealth <name>` finds `lua/<name>/health.lua` (or
`lua/<name>/health/init.lua`) on `'runtimepath'` and calls its `check()`;
the module reports with `vim.health.start(name)`, `.ok(msg)`,
`.info(msg)`, `.warn(msg, advice...)`, and `.error(msg, advice...)`
([health-dev][health]).

**Use when.**

- The plugin has prerequisites a user can fix: Neovim version, external
  executables, configuration validity, other plugins.

**Do not use when.**

- The check would change state (write files, start servers, fix config):
  health checks report only.
- Warning about optional tools the plugin never calls: users chase
  irrelevant warnings.

**Example.**

```lua
local M = {}
function M.check()
  vim.health.start("lineup")
  local ok, cfg, unknown = pcall(require("lineup.config").get)
  if not ok then
    vim.health.error("invalid configuration: " .. tostring(cfg),
      "Fix vim.g.lineup or the table passed to setup().")
    return
  end
  vim.health.ok("configuration is valid")
  for _, key in ipairs(unknown) do
    vim.health.warn("unknown option: " .. key, "Remove it or fix the typo.")
  end
  for _, program in ipairs(cfg.filters) do
    if vim.fn.executable(program) == 1 then
      vim.health.ok(("filter `%s` found"):format(program))
    else
      vim.health.warn(("filter `%s` is not executable"):format(program),
        "Install it or remove it from `filters`.")
    end
  end
end
return M
```

Runnable: `assets/examples/lineup/lua/lineup/health.lua` (also checks
`vim.fn.has("nvim-0.12")`).

**Cost removed.** Support round trips: the report names the bad value and
the fix. Metric: for the suite's configuration the health buffer
contains these four lines (asserted):

```text
OK configuration is valid
WARNING unknown option: typo
OK filter `sort` found
WARNING filter `lineup-missing` is not executable
```

**Verify.**

1. Suite test `checkhealth reports config and filters` runs
   `:checkhealth lineup` headless and searches the buffer text.
1. Interactive: `:checkhealth lineup`.

[deprecated]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/deprecated.txt
[health]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/health.txt
[lua]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt
[lua-plugin]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua-plugin.txt
[news11]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/news-0.11.txt
[demo]: ../assets/examples/demos/error_vs_notify.lua
