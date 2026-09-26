# Testing, types, and help docs

Cards for proving plugin behavior in a real headless Neovim, checking
types, and shipping `:help`. The suite, runner, and mutants are in
[`assets/examples/`](../assets/examples/); `verify.sh` drives them.

Verification tier for this file: **Executed** for the runner, isolation,
async waits, mutants, pure tests, and help tags (Neovim 0.12.5 macOS
arm64 release build on an Apple M1 Max, macOS 27.0, LuaJIT
2.1.1774638290, PUC Lua 5.5.1). The LuaLS card is **not runnable here**:
`lua-language-server` is not installed; its commands are unexecuted.

## Contents

- Headless test runner
- Isolated editor state
- Waiting for async results
- Mutant runs
- Pure Lua tests under two runtimes
- LuaCATS annotations
- Help file and helptags

## Headless test runner

**Definition.** `nvim --clean --headless -u tests/minimal_init.lua -l
tests/run.lua` starts without UI (`--headless`), skips user config and
ShaDa (`--clean`), sources only the given init (`-u`), then runs the Lua
script and exits; `-l` "Exits 1 on Lua error" and makes `print()` write
to output ([-l][starting]). The runner is a plain Lua file: a list of
named test functions, each run in `pcall`, one `ok`/`FAIL` line each, and
`os.exit(1)` if any failed.

**Use when.**

- Any claim about editor behavior: commands, maps, autocmds, buffers,
  processes, help. A unit test with a mocked `vim` cannot show them.
- The repository has no test runner yet; this needs no dependency.

**Do not use when.**

- The repository already uses a runner (busted with nlua, plenary,
  mini.test): add tests there, not a second framework. Neovim's plugin
  help documents none of them; follow the repository.
- `-c 'lua ...' -c 'qa!'` as the runner: recorded here, `nvim --clean
  --headless -c 'lua assert(false, "boom")' -c 'qa!'` prints `E5108: Lua:
  ... boom` and exits 0. Use `-l`, or end with `cquit` on failure.

**Example.**

```lua
local tests, failed = {}, {}
local function test(name, fn)
  tests[#tests + 1] = { name = name, fn = fn }
end

test("json is one undo step", function()
  buffer({ "x", "y", "z" })
  local before = vim.fn.undotree().seq_last
  vim.cmd("%LineupJson")
  eq(vim.fn.undotree().seq_last - before, 1, "undo sequence delta")
end)

for _, t in ipairs(tests) do
  local ok, err = pcall(t.fn)
  print((ok and "ok   " or "FAIL ") .. t.name
    .. (ok and "" or ": " .. tostring(err)))
  if not ok then failed[#failed + 1] = t.name end
end
if #failed > 0 then os.exit(1) end
```

Runnable: `assets/examples/lineup/tests/run.lua` (21 tests) with
`tests/minimal_init.lua`.

**Cost removed.** Unverified integration claims. Metric:
`21 passed, 0 failed (0.12.5+v0.12.5)`; exit status 0, and 1 for every
mutant.

**Verify.**

1. `sh assets/examples/verify.sh suite`.
1. Break any assertion deliberately; the exit status must be 1
   (`verify.sh mutants` does this 13 times).
1. Plugin loading under `--clean`: [load-plugins][starting] lists
   `--clean` among the cases where plugin loading "won't be done", yet
   `nvim --clean --headless -u init.lua` **did** source `plugin/*.lua`
   from the runtimepath entry that `init.lua` prepended (0.12.5, recorded
   with a counter in a test `plugin/p.lua`); `-u NONE` and `--noplugin`
   did not. The suite's first test fails if the plugin is not loaded, so
   it detects a change in this behavior.

## Isolated editor state

**Definition.** Point `XDG_CONFIG_HOME`, `XDG_DATA_HOME`,
`XDG_STATE_HOME`, and `XDG_CACHE_HOME` at a temporary directory and run
from a disposable copy of the plugin, so neither the user's files nor the
repository change (`:helptags` writes `doc/tags`; logs and ShaDa go under
the XDG directories; see [base-directories][starting]).

**Use when.**

- Every automated run, locally and in CI.

**Do not use when.**

- Reproducing a user's bug that depends on their config: then run with
  their minimal config file as `-u`, still in a temporary XDG tree.

**Example.**

```sh
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' 0
export XDG_CONFIG_HOME="$WORK/xdg/config" XDG_DATA_HOME="$WORK/xdg/data"
export XDG_STATE_HOME="$WORK/xdg/state" XDG_CACHE_HOME="$WORK/xdg/cache"
cp -R lineup "$WORK/lineup"
cd "$WORK/lineup" && nvim --clean --headless -u tests/minimal_init.lua \
  -l tests/run.lua
```

Runnable: `assets/examples/verify.sh`.

**Cost removed.** Tests that pass only on the author's machine, and
generated files in the repository. Metric: no `doc/tags`, `*.orig`, or
`*.rej` appears under `assets/examples` after `verify.sh` runs.

**Verify.**

1. Run `sh assets/examples/verify.sh`, then `find assets/examples -name
   tags -o -name '*.orig' -o -name '*.rej'` prints nothing (checked
   here).

## Waiting for async results

**Definition.** `vim.wait(ms, cond, interval)` processes events (timers,
process exits, scheduled callbacks) until `cond()` returns true or `ms`
elapse; it returns `true` on success and `false, -1` on timeout
([vim.wait()][lua]). A test forces the interleaving it needs: start the
work, perform the conflicting action, then wait for the completion flag.

**Use when.**

- Testing anything that completes through `vim.system`, `vim.uv`, or
  `vim.schedule`.
- Ordering matters: slow the external process deliberately
  (`{ "sh", "-c", "sleep 0.2; sort" }`) so the edit or buffer switch
  always happens before completion.

**Do not use when.**

- `vim.wait(200)` without a condition as synchronization: the result
  depends on machine load. Wait on a condition with a deadline.
- Inside a fast callback: `vim.wait` cannot be called there.

**Example.**

```lua
local function filter_and_wait(buf, argv, before_wait)
  local outcome
  require("lineup").filter(buf, argv, function(o)
    outcome = o
  end)
  if before_wait then
    before_wait() -- the conflicting action, before completion
  end
  assert(vim.wait(5000, function()
    return outcome ~= nil
  end, 10), "filter did not finish within 5000 ms")
  return outcome
end
```

Runnable: `assets/examples/lineup/tests/run.lua`.

**Cost removed.** Flaky async tests. Metric: the stale-result,
current-buffer, cancel, and wipeout tests pass on every run and fail on
their mutants (no timing assertion except the 2000 ms kill bound).

**Verify.**

1. Run `sh verify.sh suite` several times; results do not change.
1. `sh verify.sh mutants` kills `no-changedtick`, `current-buffer`,
   `no-generation`, and `no-kill`.

## Mutant runs

**Definition.** A mutant is a small patch that reintroduces one known
failure (eager `require`, missing `clear = true`, buffer `0` in a
callback, no `vim.schedule`, ...). Running the unchanged suite on each
patched copy must fail with the specific test named in the patch's
`Expect:` line; a mutant that survives means the suite does not test that
construct.

**Use when.**

- Adding a test for a failure that is easy to write and easy to miss
  (stale results, duplicate autocmds, leaked processes).

**Do not use when.**

- Accepting "the suite fails" without checking which test: a mutant that
  breaks loading fails every test and proves nothing specific.

**Example.**

```diff
Why: Each run adds another BufWipeout handler.
Expect: FAIL autocmd group holds one handler after repeated runs

--- a/lua/lineup/init.lua
+++ b/lua/lineup/init.lua
@@ -46,7 +46,7 @@

 -- Recreated on every filter run; clear = true keeps exactly one handler.
 local function ensure_autocmds()
-  local group = vim.api.nvim_create_augroup("lineup", { clear = true })
+  local group = vim.api.nvim_create_augroup("lineup", { clear = false })
```

Runnable: `assets/examples/mutants/*.patch` (13 patches), applied with
`patch -p1` by `verify.sh mutants`.

**Cost removed.** Tests that pass whatever the code does. Metric:
13 of 13 mutants killed, each by its named test (`no-schedule` fails 5
tests; each other mutant fails exactly 1).

**Verify.**

1. `sh assets/examples/verify.sh mutants` prints one `killed <name>` line
   per patch and exits 0.

## Pure Lua tests under two runtimes

**Definition.** Modules that do not touch `vim` can be tested with a
standalone interpreter, but Neovim runs LuaJIT with Lua 5.1 semantics
([lua-compat][lua]), so the same test must also run under `nvim -l`. The
test adjusts `package.path` from `arg[0]` so both runtimes find
`lua/<name>/*.lua`.

**Use when.**

- Parsing, merging, formatting, and other logic kept free of editor
  state (the plugin's `util.lua`).

**Do not use when.**

- The code calls `vim.*`: test it headless instead of stubbing `vim`.
- Running only the standalone `lua`: here it is PUC Lua 5.5.1, which
  accepts `table.unpack`, `//`, and `utf8`; Neovim does not.

**Example.**

```lua
local here = arg and arg[0] and arg[0]:match("^(.*)/[^/]*$") or "."
package.path = here .. "/../lua/?.lua;" .. package.path
local util = require("lineup.util")
local merged, unknown = util.merge({ a = 1 }, { a = 2, zz = 1 })
assert(merged.a == 2 and unknown[1] == "zz")
print(("PASS under %s"):format(jit and jit.version or _VERSION))
```

Runnable: `assets/examples/lineup/tests/util_spec.lua`.

**Cost removed.** Dialect bugs found only by users. Recorded:
`PASS util_spec under Lua 5.5` and `PASS util_spec under LuaJIT
2.1.1774638290`; the `lua54-only` mutant passes PUC Lua and fails under
nvim with `attempt to call field 'unpack' (a nil value)`.

**Verify.**

1. `sh assets/examples/verify.sh pure`.

## LuaCATS annotations

**Definition.** `---@class`, `---@field`, `---@param`, `---@return`,
`---@type`, and `---@alias` comments describe types for
lua-language-server (LuaLS); `(exact)` on a class rejects undeclared
fields ([annotations][luals-ann]). The help recommends them for catching
bugs in CI ([lua-plugin-type-safety][lua-plugin]). Neovim ships its own
annotations under `$VIMRUNTIME/lua`, so adding that to
`workspace.library` types every `vim.*` call.

**Use when.**

- Public functions, configuration tables, and callback signatures.
- CI can run LuaLS: `lua-language-server --check=<dir>
  --checklevel=Warning` writes a diagnosis report to `--logpath`
  (default `./log`) ([usage][luals-usage]).

**Do not use when.**

- As a substitute for tests: annotations are not enforced at runtime.
- Writing Lua 5.4 in `.luarc.json` `runtime.version`: set `"LuaJIT"` so
  5.4-only functions are flagged.

**Example.**

```lua
---@class (exact) lineup.UserConfig
---@field filters? string[]
---@field timeout_ms? integer

---@param opts lineup.UserConfig?
function M.setup(opts)
  vim.validate("opts", opts, "table", true)
  overrides = opts
end
```

```json
{
  "runtime.version": "LuaJIT",
  "workspace.library": ["${env:VIMRUNTIME}/lua"],
  "workspace.checkThirdParty": "Disable"
}
```

Runnable files: `assets/examples/lineup/lua/lineup/config.lua` and
`assets/examples/lineup/.luarc.json` (keys from [settings][luals-set]).

**Cost removed.** Type errors found at runtime (wrong option keys, wrong
argument types). Metric: diagnostics count in the LuaLS report. Not
measured here.

**Verify.** **Not runnable here** (no `lua-language-server`); unexecuted:

1. `export VIMRUNTIME=$(nvim --clean --headless -c 'lua
   io.write(vim.env.VIMRUNTIME)' -c qa)` (this command was executed and
   prints the runtime directory).
1. `lua-language-server --check=assets/examples/lineup
   --checklevel=Warning --logpath=/tmp/luals` and read the report in the
   log path. The exit status is not documented on the usage page; read
   the report instead of trusting the status.

## Help file and helptags

**Definition.** `doc/<name>.txt` is a vimdoc file: first line
`*<name>.txt*<Tab>short description`, tags defined as `*tag*` (usually
right-aligned, prefixed with the plugin name), links as `|tag|`, options
as `'option'`, and a modeline such as `vim:tw=78:ts=8:noet:ft=help:norl:`
([help-writing][helphelp]). `:helptags {dir}` scans the `*.txt` files and
writes `{dir}/tags`, reporting duplicate tags as errors ([helptags][helphelp]).

**Use when.**

- Every published plugin; `:h lua-plugin-doc` expects `:h {plugin}` to
  work ([lua-plugin-doc][lua-plugin]).
- Tag every command (`*:Name*`), `<Plug>` map, option variable
  (`*g:name*`), and Lua function users call.

**Do not use when.**

- Committing `doc/tags`: plugin managers generate it; a committed copy
  goes stale.
- Treating a README as the help: `:help` cannot find it.

**Example.**

```text
*lineup.txt*    Encode or filter buffer lines

==============================================================================
COMMANDS                                                   *lineup-commands*

                                                             *:LineupFilter*
:LineupFilter {program} [args]
        Send the buffer to {program} on stdin without a shell. ...

 vim:tw=78:ts=8:noet:ft=help:norl:
```

Runnable: `assets/examples/lineup/doc/lineup.txt` (the real file uses a
Tab after the first tag and Tab-indented bodies; shown here as spaces).

**Cost removed.** Undocumented or unreachable commands. Metric: every
advertised topic resolves: the suite runs `:helptags` on a copy and opens
`lineup`, `:LineupFilter`, `<Plug>(LineupJson)`, and `g:lineup`, asserting
`'filetype'` is `help` each time.

**Verify.**

1. Suite test `help tags resolve`, and `verify.sh package` resolves
   `:help :LineupFilter` from the installed layout.
1. Duplicate check: `:helptags` raises `Vim:E154: Duplicate tag "dup" in
   file .../a.txt` (recorded with a two-tag fixture), so the suite fails
   if two tags collide.

[helphelp]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/helphelp.txt
[lua]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt
[lua-plugin]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua-plugin.txt
[luals-ann]: https://luals.github.io/wiki/annotations/
[luals-set]: https://luals.github.io/wiki/settings/
[luals-usage]: https://luals.github.io/wiki/usage/
[starting]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/starting.txt
