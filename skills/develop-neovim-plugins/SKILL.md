---
name: develop-neovim-plugins
description: >-
  Builds and tests Neovim Lua plugins: layout, lazy loading, user commands,
  Plug mappings, autocommands, buffer edits, async jobs, health checks,
  headless tests. Use when writing or fixing a Neovim plugin. Not for init.lua
  tweaks or Vim plugins.
---

# Develop Neovim Plugins

Build or change a Neovim Lua plugin so that it loads lazily, registers
each entry point once, edits the right buffer with correct undo, runs
external work asynchronously without corrupting later edits, reports
problems as notifications and health results, and is proven by a headless
suite that fails on each known defect. Each card in the references gives
the definition, **Use when** and **Do not use when** conditions, the cost
it removes, verification, and a runnable example. Cards cite the Neovim
v0.12.5 `runtime/doc` help; follow them instead of recalling API usage.

## Workflow

1. Record the host: `nvim --version` (first line and LuaJIT line) and the
   plugin's declared minimum version (README, help file, CI matrix,
   health check). Keep that minimum. Check the version boundaries in the
   cards: `vim.system` needs 0.10, positional `vim.validate` 0.11, the
   `buf` key in keymap/autocmd options 0.12 (older: `buffer`).
1. Map the existing layout before adding files: `plugin/`, `lua/<name>/`,
   `ftplugin/`, `doc/`, tests, rockspec. Extend what exists; do not add a
   second scaffold, runner, or config mechanism.
1. Pick the card from the routing table and read all of it, including
   **Do not use when**.
1. Write or extend the headless test first. Use the repository runner, or
   copy `assets/examples/lineup/tests/` (runner + minimal init) when none
   exists. For async behavior, force the ordering and wait on a condition.
1. Implement the smallest change that satisfies the card.
1. Run the suite in isolation from the user's config:
   `nvim --clean --headless -u tests/minimal_init.lua -l tests/run.lua`
   with `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, and
   `XDG_CACHE_HOME` pointing to a temp directory, from a copy of the
   plugin ([isolation](references/testing-types-docs.md#isolated-editor-state)).
1. Prove the test discriminates: revert the fix (or apply the matching
   mutant idea from `assets/examples/mutants/`) and confirm the named test
   fails for the intended reason.
1. Measure the claimed benefit with the card's metric: for example the
   count of `require('<name>` lines in `--startuptime` output, the number
   of autocmds in the group, the `undotree().seq_last` delta.
1. Update `doc/<name>.txt`, run `:helptags` on a copy, and resolve every
   new tag with `:help`.

## Route the task to a card

| Task or symptom | Card |
| --- | --- |
| New plugin, where does this file go | [Runtimepath plugin layout](references/layout-and-loading.md#runtimepath-plugin-layout) |
| `require` at top of `plugin/`, slow startup | [Lazy loading](references/layout-and-loading.md#lazy-loading-from-plugin) |
| Plugin initializes twice, user cannot disable it | [Load guard](references/layout-and-loading.md#load-guard-variable) |
| Filetype-specific options or maps | [Filetype plugin](references/layout-and-loading.md#filetype-plugin) |
| Works in `lua`, fails in Neovim (`unpack`, `//`, `utf8`) | [Lua 5.1 and LuaJIT](references/layout-and-loading.md#lua-51-and-luajit-compatibility) |
| User asks about `vim.loader` | [vim.loader](references/layout-and-loading.md#vimloader-byte-code-cache) |
| Publish to LuaRocks | [Rockspec](references/layout-and-loading.md#luarocks-rockspec) |
| Add an Ex command with arguments or range | [User command](references/commands-keymaps-autocmds.md#user-command-with-nargs-and-range) |
| Tab completion for command arguments | [Completion](references/commands-keymaps-autocmds.md#command-completion-function) |
| Offer an action on a key | [Plug mappings](references/commands-keymaps-autocmds.md#plug-mappings) |
| Map only in one buffer | [Buffer-local keymap](references/commands-keymaps-autocmds.md#buffer-local-keymap) |
| Autocmd fires twice after reload | [Augroup with clear](references/commands-keymaps-autocmds.md#augroup-with-clear) |
| Per-buffer state or processes outlive buffers | [Buffer lifetime autocmd](references/commands-keymaps-autocmds.md#buffer-lifetime-autocmd) |
| Option leaks into other windows | [Option scopes](references/buffers-options-async.md#option-scopes) |
| Edit lands in the wrong buffer | [Buffer handle](references/buffers-options-async.md#buffer-handle-instead-of-0) |
| Replace or insert whole lines | [nvim_buf_set_lines](references/buffers-options-async.md#nvim_buf_set_lines) |
| Change part of a line, keep extmarks | [nvim_buf_set_text](references/buffers-options-async.md#nvim_buf_set_text) |
| Highlights, virtual text, or diagnostics | [Namespaces](references/buffers-options-async.md#namespaces-for-extmarks-and-diagnostics) |
| One action needs several `u` presses | [Undo blocks](references/buffers-options-async.md#undo-blocks) |
| Show results in a split or float | [Scratch buffer](references/buffers-options-async.md#scratch-buffer-and-split-window) |
| `E5560 ... must not be called in a fast event context` | [vim.schedule](references/buffers-options-async.md#vimschedule-and-fast-events) |
| Run an external program | [vim.system](references/buffers-options-async.md#vimsystem-process) |
| Async result overwrites newer user edits | [Freshness check](references/buffers-options-async.md#freshness-check-before-applying-a-result) |
| Old requests finish after newer ones | [Cancel superseded work](references/buffers-options-async.md#cancel-superseded-work) |
| Configuration design | [vim.g](references/config-errors-health.md#configuration-through-vimg), [setup](references/config-errors-health.md#setup-that-only-stores-options) |
| Bad option values fail deep inside | [vim.validate](references/config-errors-health.md#vimvalidate), [Unknown options](references/config-errors-health.md#unknown-option-detection) |
| Users see stack tracebacks | [vim.notify versus error](references/config-errors-health.md#vimnotify-versus-error) |
| Diagnose user setups | [Health check](references/config-errors-health.md#health-check-module) |
| Write or run tests | [Runner](references/testing-types-docs.md#headless-test-runner), [async waits](references/testing-types-docs.md#waiting-for-async-results), [mutants](references/testing-types-docs.md#mutant-runs) |
| Test pure helpers | [Two runtimes](references/testing-types-docs.md#pure-lua-tests-under-two-runtimes) |
| Type annotations | [LuaCATS](references/testing-types-docs.md#luacats-annotations) |
| Help file | [Help and helptags](references/testing-types-docs.md#help-file-and-helptags) |

## Rules

- `plugin/<name>.lua` defines commands, `<Plug>` maps, and nothing
  heavy; every callback calls `require` itself. No top-level `require` of
  the plugin's own modules there.
- No default key mappings outside `<Plug>`, except buffer-local maps in
  plugin-owned buffers or `ftplugin/` files with `b:undo_ftplugin`.
- Every autocmd has a `group` created with `clear = true`, owned by the
  plugin. Never clear autocmds by event alone.
- Deferred code (scheduled, process exit, timer, autocmd for another
  buffer) uses a captured buffer handle, never `0`, and re-checks
  `nvim_buf_is_valid`, `changedtick`, request identity, and
  `'modifiable'` before editing.
- Editor API calls from `vim.uv`/`vim.system` callbacks go through
  `vim.schedule` or `vim.schedule_wrap`.
- `vim.system` takes an argument list, not a shell string with file
  names; wrap it in `pcall` (start failure throws) and check `code`.
  No `:wait()` on interactive paths.
- User-facing failures use `vim.notify` with a `vim.log.levels` level and
  the plugin name; `error()` is for misuse of a Lua API.
- `setup()` only stores and validates options. Configuration also works
  through `vim.g.<name>` and with no configuration at all.
- Plugin Lua is Lua 5.1: no `//`, bitwise operators, `utf8`,
  `table.unpack`, `goto`. Run pure tests under `nvim -l` as well.
- Window options from plugins go through `vim.wo[win]` or
  `vim.opt_local`, never `vim.o`.
- Do not commit `doc/tags`. Do not publish (LuaRocks upload, registry
  edits) without explicit authorization.
- Claims about editor behavior need a headless run; a standalone `lua`
  run or a mocked `vim` proves only pure logic.

## Bundled tools

- `assets/examples/lineup/`: a complete plugin (commands, `<Plug>` maps,
  augroup, async filter with freshness and cancellation, config, health,
  ftplugin, help, rockspec, test suite). Copy files into the user's
  repository and rename `lineup` consistently; do not edit the installed
  skill instead.
- `assets/examples/mutants/`: patches that each reintroduce one defect.
- `assets/examples/demos/`: standalone scripts for option scopes, undo
  blocks, `set_text` extmarks, namespaces, and `error` versus `notify`.
- `sh assets/examples/verify.sh [all|pure|suite|mutants|startup|demos|
  package]` runs them. Set `NVIM` to the binary if it is not on `PATH`
  (and `LUA` for the standalone interpreter). Missing executables print
  `SKIP`.

## References

- [Layout and loading](references/layout-and-loading.md): layout, lazy
  loading, load guard, ftplugin, Lua 5.1, vim.loader, rockspec.
- [Commands, keymaps, and autocmds](references/commands-keymaps-autocmds.md):
  user commands, completion, `<Plug>`, buffer-local maps, augroups,
  lifetime autocmds.
- [Buffers, options, and async work](references/buffers-options-async.md):
  option scopes, handles, `set_lines`, `set_text`, namespaces and
  diagnostics, undo, scratch windows,
  `vim.schedule`, `vim.system`, freshness, cancellation.
- [Configuration, errors, and health](references/config-errors-health.md):
  `vim.g`, `setup`, `vim.validate`, unknown keys, `notify` versus
  `error`, `:checkhealth`.
- [Testing, types, and help docs](references/testing-types-docs.md):
  headless runner, isolation, async waits, mutants, two-runtime tests,
  LuaCATS, help files.

## Completion evidence

The final report contains:

- `nvim --version` first line and LuaJIT line of every host exercised,
  and the plugin's declared minimum; versions not exercised are listed as
  not verified.
- The cards applied, with their **Do not use when** conditions checked.
- The exact test command, its isolation (XDG temp dirs, `--clean`), and
  the result line (`N passed, M failed`).
- For each new test, the defect it catches: the reverted fix or mutant and
  the failing test name.
- The card metric before and after where one applies (startup `require`
  count, autocmd count, undo steps, notification count).
- `:helptags` plus `:help <tag>` results for new documentation.
- Checks not run (for example LuaLS or `luarocks` not installed) stated as
  not verified, with the command the user can run.
