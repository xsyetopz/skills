# Buffers, options, and async work

Cards for editing text through the API, scoping options, and running
external work without blocking or corrupting the editor. Examples are in
[`assets/examples/lineup/`](../assets/examples/lineup/) and the standalone
scripts in [`assets/examples/demos/`](../assets/examples/demos/)
(`nvim --clean --headless -l <file>`).

Verification tier for this file: **Executed** with Neovim 0.12.5 (macOS
arm64 release build on an Apple M1 Max, macOS 27.0, LuaJIT 2.1.1774638290) via
`sh assets/examples/verify.sh suite|mutants|demos`. Output quoted below is
from those runs; absolute paths are shortened.

## Contents

- Option scopes
- Buffer handle instead of 0
- nvim_buf_set_lines
- nvim_buf_set_text
- Namespaces for extmarks and diagnostics
- Undo blocks
- Scratch buffer and split window
- vim.schedule and fast events
- vim.system process
- Freshness check before applying a result
- Cancel superseded work

## Option scopes

**Definition.** `vim.o.x` behaves like `:set` (for a window or buffer
option it sets the current window/buffer value and the global value);
`vim.go.x` is `:setglobal`; `vim.bo[buf].x` and `vim.wo[win].x` target a
given buffer or window (`vim.wo[win][0].x` is `:setlocal`);
`vim.opt`/`vim.opt_local`/`vim.opt_global` return `Option` objects with
`:append`, `:prepend`, `:remove`, and `:get()` for list and map options
([lua-vim-options][lua]). Unknown names raise an error.

**Use when.**

- `vim.bo[buf]`/`vim.wo[win]`: a plugin changes one buffer or window it
  holds a handle for (plugin-owned buffers, windows it opened).
- `vim.opt_local`: inside `ftplugin/`, for the current buffer and window.
- `vim.opt.x:append(...)`: list options such as `'wildignore'`, where
  string concatenation duplicates commas.

**Do not use when.**

- `vim.o` in plugin code for a window option: it also sets the global
  value, which every window opened later inherits (demo below).
- Reading `vim.opt.x` as a value: it is a table (`Option` object); use
  `vim.o.x` or `vim.opt.x:get()`.
- `vim.bo.x` (no index) in a callback: it targets whichever buffer is
  current when the callback runs.

**Example.**

```lua
local w1 = vim.api.nvim_get_current_win()
vim.opt_local.wrap = false   -- like :setlocal nowrap
vim.opt_local.wrap = true
vim.o.wrap = false           -- like :set nowrap
vim.cmd("new")               -- new window inherits the global value
assert(vim.wo.wrap == false)
local scratch = vim.api.nvim_create_buf(false, true)
vim.bo[scratch].filetype = "text" -- current buffer is untouched
```

Runnable: `assets/examples/demos/option_scopes.lua`. Recorded output:

```text
default                      w1=true  w2=true  global=true
vim.opt_local.wrap=false     w1=false w2=true  global=true
vim.o.wrap=false             w1=false w2=true  global=false
new window after vim.o: wrap=false
vim.bo[scratch].filetype=text current=""
type(vim.o.shortmess)=string type(vim.opt.shortmess)=table
vim.o.not_an_option -> ...option_scopes.lua:33: Unknown option
'not_an_option'
```

**Cost removed.** Option leaks into unrelated windows and buffers. Metric:
the global value (`vim.go.wrap`) is unchanged after plugin code runs.

**Verify.**

1. `sh verify.sh demos` prints the table above.
1. `mutants/global-option.patch` swaps `vim.opt_local.wrap` for
   `vim.o.wrap` in the ftplugin; suite test `ftplugin: local options and
   map, undone on filetype change` fails because `setlocal wrap<` then
   restores the changed global.
1. Interactive: `:verbose setlocal wrap?` shows who set the local value.

## Buffer handle instead of 0

**Definition.** API functions accept `0` for the current buffer (or
window), resolved when the call runs ([api-indexing][api]). A handle
captured with `nvim_get_current_buf()` at request time names the same
buffer until it is wiped; `nvim_buf_is_valid(handle)` reports whether it
still exists.

**Use when.**

- Code runs after the user action: `vim.schedule`, `vim.system`
  callbacks, timers, autocmds for other buffers.
- Library functions: take `buf` as a parameter and let the command
  resolve `0` once.

**Do not use when.**

- Using `0` in deferred code: if the user switched buffers, the edit
  lands in the wrong file.
- Assuming a captured handle is still valid: check `nvim_buf_is_valid`
  first; API calls on a wiped buffer raise `Invalid buffer id: <n>`
  (recorded).

**Example.**

```lua
function M.filter_command(fargs)
  -- resolve the current buffer once, at request time
  local ok, err = pcall(M.filter, vim.api.nvim_get_current_buf(), fargs)
  if not ok then
    notify(tostring(err), vim.log.levels.ERROR)
  end
end
```

Runnable: `assets/examples/lineup/lua/lineup/init.lua`.

**Cost removed.** Edits applied to the wrong buffer. Metric: after a
filter completes while another buffer is current, the other buffer's
lines are unchanged.

**Verify.**

1. Suite test `filter edits the initiating buffer, not the current one`.
1. `mutants/current-buffer.patch` writes to buffer `0` in the callback;
   that test fails.

## nvim_buf_set_lines

**Definition.** `nvim_buf_set_lines(buf, start, end, strict, lines)`
replaces whole lines `[start, end)`: zero-based, end-exclusive, negative
indices count from the end (`-1` is past the last line); `start == end`
inserts; `{}` deletes; out-of-range indices are clamped unless `strict`
([nvim_buf_set_lines][api]). Ex ranges and `line1`/`line2` are one-based
inclusive, so a range `a,b` is `set_lines(buf, a - 1, b, ...)`. It fails
under `textlock` and on a `'nomodifiable'` buffer.

**Use when.**

- Replacing, inserting, or deleting whole lines; the help prefers it over
  `nvim_buf_set_text` there "for performance".

**Do not use when.**

- Only part of a line changes and extmarks, diagnostics, or signs sit on
  that line: they move to column 0 (see `nvim_buf_set_text`).
- `strict = false` would hide an off-by-one: pass `true` for a
  user-supplied range so a bad range errors instead of clamping.
- Checking `'readonly'` to decide whether to edit: `'readonly'` guards
  only writing the file; `'modifiable'` guards edits.

**Example.**

```lua
function M.json_lines(buf, first, last)
  local lines = vim.api.nvim_buf_get_lines(buf, first - 1, last, true)
  local encoded = vim.json.encode(lines)
  vim.api.nvim_buf_set_lines(buf, first - 1, last, true, { encoded })
end
```

Runnable: `assets/examples/lineup/lua/lineup/init.lua`.

**Cost removed.** Off-by-one range errors and writes to protected buffers.
Metric: on a `'nomodifiable'` buffer the command fails with
`Buffer is not 'modifiable'` and the text is unchanged; with only
`'readonly'` set the edit succeeds.

**Verify.**

1. Suite tests `json encodes the range and leaves other lines` and
   `json respects nomodifiable, not readonly`.
1. Unicode and escaping: the first test encodes `café 雪`, a quote, and a
   backslash.

## nvim_buf_set_text

**Definition.** `nvim_buf_set_text(buf, start_row, start_col, end_row,
end_col, lines)` replaces a character range: zero-based rows
(end-inclusive) and byte columns (end-exclusive). The help recommends it
over `nvim_buf_set_lines` for partial-line edits because "extmarks will be
preserved on non-modified parts of the touched lines"
([nvim_buf_set_text][api]).

**Use when.**

- Renaming a word, applying an LSP text edit, or any edit inside a line
  that carries extmarks (highlights, virtual text, diagnostics).

**Do not use when.**

- Columns are characters or UTF-16 units: they are bytes. Convert first
  (`vim.str_byteindex`); LSP positions use the negotiated encoding.
- Replacing whole lines: use `nvim_buf_set_lines`.

**Example.**

```lua
local ns = vim.api.nvim_create_namespace("demo.set_text")
local buf = vim.api.nvim_create_buf(false, true)
vim.api.nvim_buf_set_lines(buf, 0, -1, true, { "local foo = 1" })
local id = vim.api.nvim_buf_set_extmark(buf, ns, 0, 12, {}) -- on "1"
vim.api.nvim_buf_set_text(buf, 0, 6, 0, 9, { "bar" }) -- bytes 6..8
local pos = vim.api.nvim_buf_get_extmark_by_id(buf, ns, id, {})
assert(pos[2] == 12)
```

Runnable: `assets/examples/demos/set_text_vs_set_lines.lua`. Recorded:

```text
set_lines: "local bar = 1" extmark col 0
set_text:  "local bar = 1" extmark col 12
```

**Cost removed.** Extmarks displaced by an edit. Metric: the extmark
column after the same textual change: 0 with `set_lines`, 12 with
`set_text`.

**Verify.**

1. `sh verify.sh demos` prints both lines; the script asserts column 12.

## Namespaces for extmarks and diagnostics

**Definition.** `nvim_create_namespace(name)` returns an id that owns
extmarks, highlights, and virtual text; `nvim_buf_clear_namespace(buf, ns,
0, -1)` removes only that id's objects (`-1` as `ns` clears all
namespaces) ([nvim_buf_clear_namespace][api]). Extmark positions are
0-based rows and byte columns; `right_gravity` (default `true`) decides
whether a mark moves right when text is inserted at its position
([nvim_buf_set_extmark][api]). `vim.diagnostic.set(ns, buf, items)` stores
diagnostics per namespace and `vim.diagnostic.reset(ns, buf)` removes only
that namespace's items ([diagnostic][diagnostic]). Exception to 0-based
indexing: `nvim_win_get_cursor`/`nvim_win_set_cursor` and marks are
(1,0)-indexed ([api-indexing][api]).

**Use when.**

- The plugin draws highlights or virtual text, or reports problems in
  buffers: create one namespace per purpose at module load and reuse it.
- Reporting problems: use `vim.diagnostic.set` instead of drawing signs
  and virtual text, so the user's `vim.diagnostic` configuration, signs,
  float, and jump maps apply.

**Do not use when.**

- Clearing with `ns = -1` or `vim.diagnostic.reset()` without a namespace:
  it removes LSP diagnostics and other plugins' marks.
- Treating a tracked extmark position as proof the text is unchanged: the
  mark moves with edits; compare text or `changedtick` too.
- Passing a cursor row straight to a buffer API: subtract 1 (cursor rows
  are 1-based; `nvim_buf_get_lines` rows are 0-based).

**Example.**

```lua
local ns = vim.api.nvim_create_namespace("demo.mine")
local buf = vim.api.nvim_get_current_buf()
vim.api.nvim_buf_set_extmark(buf, ns, 0, 6,
  { end_col = 10, hl_group = "Todo" })
vim.diagnostic.set(ns, buf, { { lnum = 0, col = 0, message = "mine" } })
-- cleanup: only what this namespace owns
vim.api.nvim_buf_clear_namespace(buf, ns, 0, -1)
vim.diagnostic.reset(ns, buf)
local row = vim.api.nvim_win_get_cursor(0)[1]       -- 1-based
local line = vim.api.nvim_buf_get_lines(buf, row - 1, row, true)[1]
```

Runnable: `assets/examples/demos/namespaces.lua`. Recorded:

```text
insert at col 6: left-gravity col 6, right-gravity col 10
after clearing mine: extmarks mine=0 other=1
after reset(mine): diagnostics mine=0 other=1
cursor row 2 -> buffer line "gamma"
```

**Cost removed.** Deleting other owners' marks and diagnostics, and
off-by-one rows. Metric: after cleanup, the other namespace still has 1
extmark and 1 diagnostic.

**Verify.**

1. `sh verify.sh demos` runs the script; it asserts the counts above.
1. Interactive: `:lua =vim.api.nvim_get_namespaces()` lists namespace
   names and ids.

## Undo blocks

**Definition.** Changes made by one command or one script run join a
single undo block until something closes it; setting `'undolevels'` (even
to its current value) closes the block ([undo-close-block][undo]).
`:undojoin` merges the next change into the previous block and the help
warns it "may prevent the user from properly undoing changes". A buffer
with `'undolevels'` `-1` keeps no undo ([options][options]).

**Use when.**

- One user action should undo with one `u`: make all API edits inside
  one command callback; nothing else is needed.
- Test fixtures: close the fixture's block (`vim.o.undolevels =
  vim.o.undolevels`) before the action under test so undo counts only
  that action.
- Plugin-owned display buffers (logs, pickers): `vim.bo[buf].undolevels =
  -1`.

**Do not use when.**

- `:undojoin` after an async result: it merges your edit into whatever
  the user did last, and `u` then removes both.
- `vim.o.undolevels = vim.o.undolevels` in plugin code where the buffer
  has a local value: the help shows that `let &undolevels = &undolevels`
  copies the local value into the global one, and `vim.o` behaves like
  `:set`/`let &`. To close a block from a plugin, use
  `vim.go.undolevels = vim.go.undolevels`.

**Example.**

```lua
local function seq() return vim.fn.undotree().seq_last end
local base = seq()
vim.api.nvim_buf_set_lines(0, 0, -1, true, { "a" })
vim.api.nvim_buf_set_lines(0, 1, 1, true, { "b" })
print(seq() - base)               --> 1
base = seq()
vim.o.undolevels = vim.o.undolevels
vim.api.nvim_buf_set_lines(0, 0, 0, true, { "c" })
vim.o.undolevels = vim.o.undolevels
vim.api.nvim_buf_set_lines(0, 0, 0, true, { "d" })
print(seq() - base)               --> 2
```

Runnable: `assets/examples/demos/undo_blocks.lua`. Recorded:

```text
two edits, no close:  1 undo step(s)
two edits, closed:    2 undo step(s)
undolevels=-1 buffer: 0 undo step(s)
```

**Cost removed.** Extra `u` presses (or one `u` that undoes too much).
Metric: `undotree().seq_last` delta per user action; `:LineupJson` adds
exactly 1, and one `u` restores the original lines.

**Verify.**

1. Suite test `json is one undo step`.
1. `sh verify.sh demos` prints the three counts above (asserted).

## Scratch buffer and split window

**Definition.** `nvim_create_buf(listed, scratch)` returns a new unnamed
buffer; `scratch = true` makes it a throwaway buffer (always
`'nomodified'`, `'nomodeline'`) ([nvim_create_buf][api]).
`nvim_open_win(buf, enter, config)` opens it in a split when `config` has
`split = "left"|"right"|"above"|"below"` and no `relative`, or a float
when `relative` is set (floats need `width` and `height`)
([nvim_open_win][api]).

**Use when.**

- The plugin shows generated content (logs, results, previews) that is
  not a file.
- Reuse: keep the handle and reopen the same buffer while
  `nvim_buf_is_valid` is true instead of creating one per call.

**Do not use when.**

- The user should save the content: use a normal named buffer.
- Setting `'filetype'` before options and lines: `FileType` handlers
  (your ftplugin, user autocmds) run first, and your later settings
  override theirs. Set it last ([lua-plugin-filetype][lua-plugin]).

**Example.**

```lua
function M.open_log()
  if not (log_buf and vim.api.nvim_buf_is_valid(log_buf)) then
    log_buf = vim.api.nvim_create_buf(false, true)
    vim.bo[log_buf].undolevels = -1
  end
  vim.bo[log_buf].modifiable = true
  vim.api.nvim_buf_set_lines(log_buf, 0, -1, true, log)
  vim.bo[log_buf].modifiable = false
  vim.api.nvim_open_win(log_buf, true, { split = "below", height = 8 })
  vim.bo[log_buf].filetype = "lineuplog" -- last: users can override
end
```

Runnable: `assets/examples/lineup/lua/lineup/init.lua`.

**Cost removed.** "Save changes?" prompts and stray listed buffers from
plugin UI. Metric: `vim.bo[log_buf].buflisted == false` and
`vim.bo[log_buf].modified == false` after writing lines.

**Verify.**

1. Suite test `ftplugin: local options and map, undone on filetype
   change` opens the log and asserts filetype `lineuplog` plus
   window-local options.
1. Interactive: `:ls!` lists the log buffer as unlisted (`u` flag).

## vim.schedule and fast events

**Definition.** `vim.uv` callbacks (timers, process exit, fs watchers)
run in a "fast" context where calling `vim.api` functions other than
`api-fast` ones is error E5560 ([lua-loop-callbacks][lua]).
`vim.schedule(fn)` queues `fn` on the main loop; `vim.schedule_wrap(fn)`
returns a function that does that with its arguments;
`vim.in_fast_event()` reports the context ([api-fast][api]). Scheduling
also escapes `textlock`.

**Use when.**

- Any editor API call from a `vim.system` on_exit, a `vim.uv` timer, or
  another luv callback. Recorded in a timer callback: `vim.cmd` fails
  (`E5560: nvim_exec2 ...`) and the default `vim.notify` fails
  (`E5560: nvim_echo ...`), while `vim.fn.getpid()` succeeds. Do not
  guess per function; schedule the whole editor-facing part.

**Do not use when.**

- The callback only updates Lua tables or calls fast functions: scheduling
  adds a main-loop hop for nothing.
- As a freshness guarantee: by the time scheduled code runs, the user
  may have changed or closed the buffer (see Freshness check).
- For one-shot delays: `vim.defer_fn(fn, ms)` already schedules.

**Example.**

```lua
local timer = assert(vim.uv.new_timer())
timer:start(0, 0, function()
  local ok, err = pcall(vim.api.nvim_get_current_line)
  print(ok, err) -- false, E5560: ... fast event context
  vim.schedule(function()
    print(vim.api.nvim_get_current_line()) -- allowed
  end)
  timer:close() -- always close uv handles
end)
```

Runnable: suite test `uv callbacks need vim.schedule for editor API
(E5560)` in `tests/run.lua`. Recorded message: `E5560:
nvim_get_current_line must not be called in a fast event context`.

**Cost removed.** Callback crashes. Metric: with `mutants/no-schedule.patch`
(on_exit not wrapped) the log shows `E5560: nvim_buf_is_valid must not be
called in a fast event context`, the result is never applied, and 5 suite
tests fail.

**Verify.**

1. Suite test above passes (asserts `E5560` and that the scheduled call
   ran).
1. `sh verify.sh mutants` prints `killed no-schedule: 5 failing test(s)`.

## vim.system process

**Definition.** `vim.system(cmd, opts, on_exit)` (since 0.10,
[news-0.10][news10]) starts `cmd` (a list, no shell) and returns a
`vim.SystemObj` (`pid`, `wait`, `kill`, `write`, `is_closing`). With
`on_exit` it runs asynchronously and calls `on_exit({ code, signal,
stdout, stderr })` in a fast context. Options include `stdin` (string or
list written then closed), `text` (normalize `\r\n`), `cwd`, `env`, and
`timeout` (ms; on expiry SIGTERM and `code = 124`). It **throws** if the
command cannot start ([vim.system][lua]).

**Use when.**

- Running an external program without freezing the UI.
- Arguments contain user data (file names, patterns): the list form needs
  no shell quoting.

**Do not use when.**

- Calling `:wait()` on an interactive path: it blocks the editor until
  the process exits.
- Building a shell string from file names (`{"sh", "-c", "fmt " ..
  path}`): it invites quoting bugs and injection. Invoke a shell only for
  shell syntax you control.
- Treating a start failure like a nonzero exit: it is a synchronous error;
  wrap the call in `pcall`.

**Example.**

```lua
local ok, proc = pcall(vim.system, argv, {
  stdin = input,          -- string[]: written, then stdin is closed
  text = true,
  timeout = cfg.timeout_ms,
}, vim.schedule_wrap(function(out)
  if out.code ~= 0 then
    notify(("%s exited %d: %s"):format(argv[1], out.code, out.stderr),
      vim.log.levels.ERROR)
    return finish("failed")
  end
  -- freshness checks, then apply out.stdout (see next card)
end))
if not ok then
  notify(tostring(proc), vim.log.levels.ERROR) -- could not start
  return finish("not started")
end
```

Runnable: `assets/examples/lineup/lua/lineup/init.lua`. Recorded start
failure: `vim/_core/system:324: ENOENT: no such file or directory (cmd):
'lineup-no-such-program'`.

**Cost removed.** UI freezes and unreported failures. Metric: the suite
edits the buffer while `sh -c "sleep 0.2; sort"` runs (possible only
because the call is asynchronous); a nonzero exit produces exactly one
notification `lineup: sh exited 3: bad` and no buffer change.

**Verify.**

1. Suite tests `filter applies output to an unchanged buffer`, `nonzero
   exit notifies and keeps the buffer`, and `a program that cannot start
   notifies instead of raising`.

## Freshness check before applying a result

**Definition.** Before applying an async result, re-check everything the
result depends on: the buffer still exists (`nvim_buf_is_valid`), its text
is unchanged (`nvim_buf_get_changedtick` equals the value captured with
the input), the request is still the latest for that buffer (identity of
the request record), and the buffer is `'modifiable'`. `b:changedtick`
increases on every change ([nvim_buf_get_changedtick][api]).

**Use when.**

- A result computed from buffer text is written back later (formatters,
  filters, code actions, completions).

**Do not use when.**

- The operation is synchronous (inside one command callback): nothing
  changes in between, so the checks and request records are dead code.
- As a merge strategy: a stale result is discarded, not rebased; if the
  feature must survive concurrent edits, re-run the request.

**Example.**

```lua
local tick = vim.api.nvim_buf_get_changedtick(buf)   -- at request time
local input = vim.api.nvim_buf_get_lines(buf, 0, -1, true)
-- ... in the scheduled on_exit:
if pending[buf] ~= req then
  return finish("cancelled")                         -- superseded
end
pending[buf] = nil
if not vim.api.nvim_buf_is_valid(buf)
  or vim.api.nvim_buf_get_changedtick(buf) ~= tick then
  return finish("stale")                             -- text changed
end
if not vim.bo[buf].modifiable then
  return finish("nomodifiable")
end
vim.api.nvim_buf_set_lines(buf, 0, -1, true, util.split_lines(out.stdout))
```

Runnable: `assets/examples/lineup/lua/lineup/init.lua`.

**Cost removed.** Lost user edits. Metric: after typing during a filter
run, the buffer still contains the typed line (`{ "typed", "b", "a" }`)
and the outcome is `stale`.

**Verify.**

1. Suite tests `filter discards a stale result` and `a newer request
   cancels the older one`.
1. `mutants/no-changedtick.patch` and `mutants/no-generation.patch` each
   fail their test.

## Cancel superseded work

**Definition.** Keep the `vim.SystemObj` of each pending request; when a
newer request replaces it or its buffer is wiped, call
`proc:kill("sigterm")` (signal names or numbers per `luv-constants`,
[SystemObj:kill()][lua]) and drop the record, so the old completion is
recognized as cancelled.

**Use when.**

- Requests can overlap for the same target, or outlive their buffer.
- The external program is slow or expensive.

**Do not use when.**

- The work is cheap and idempotent and the freshness check already
  discards stale results: killing adds bookkeeping with no visible
  effect.
- Killing without invalidating the record: an exit already queued on
  the main loop would still apply.

**Example.**

```lua
function M.forget(buf)
  local req = pending[buf]
  pending[buf] = nil                 -- invalidate first
  if req and req.proc and not req.proc:is_closing() then
    req.proc:kill("sigterm")         -- then stop the process
  end
end
```

Runnable: `assets/examples/lineup/lua/lineup/init.lua` (called at the
start of `filter()` and from the `BufWipeout` autocmd).

**Cost removed.** Orphan processes and CPU after the user moved on.
Metric: wiping the buffer during `sleep 5` yields outcome `cancelled` in
under 2000 ms.

**Verify.**

1. Suite tests `wiping the buffer kills the process` and `a newer request
   cancels the older one`.
1. `mutants/no-kill.patch` fails the first.

[api]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/api.txt
[diagnostic]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/diagnostic.txt
[lua]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt
[lua-plugin]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua-plugin.txt
[news10]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/news-0.10.txt
[options]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/options.txt
[undo]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/undo.txt
