# Neovim range-command starter

A working `:ExampleJsonLines` command converts a one-based inclusive line range
into one JSON array of strings using `vim.json.encode`. With no range it uses
the current line. It changes no other lines, writes no files, preserves empty
lines as empty strings, and supports one-step undo/redo.

This is an adaptation example, not a recommendation to publish another JSON
utility. Check built-in commands and existing plugins first. Replace the
`example` module, loaded flag, public command, and help tags consistently. There
is no configuration, setup function, health check, external process, or default
keymap because this feature needs none.

## Runtime contract

The example is tested on Neovim 0.10.4 and 0.12.5 and declares 0.10.4 as its
minimum supported build. That is a tested support boundary, not a claim that
these APIs were first introduced there. Keep LuaJIT-compatible syntax. Change
the minimum only after checking the actual feature APIs and dependencies.

## Headless behavior tests

Copy this directory to a disposable workspace; help-tag generation writes into
that copy. From its root, run with the target `nvim` on PATH:

```sh
profile=$(mktemp -d)
XDG_CONFIG_HOME="$profile/config" XDG_DATA_HOME="$profile/data" \
  XDG_STATE_HOME="$profile/state" XDG_CACHE_HOME="$profile/cache" \
  nvim --clean --headless -u tests/minimal_init.lua -l tests/smoke.lua
```

The script checks actual range edits, untouched lines, Unicode/escaping,
undo/redo, the default cursor line, an empty line, nonmodifiable and read-only
buffers, repeated plugin loading, and installed help lookup. An assertion fails
the process. It does not skip missing commands or replace the editor API with
mocks. Remove the temporary profile after the process exits.

Run on both the minimum and current supported host. `readonly` does not mean
`nomodifiable`: the former restricts ordinary file writes, while the latter
rejects this buffer edit. The test suite exercises that distinction.

## Installation artifact

The runtime files are `plugin/example.lua`, `lua/example/init.lua`, and
`doc/example.txt`. Install their parent directory as one runtimepath entry.
Exclude generated `doc/tags`, editor caches, and test files from a release
archive. Include the real project's license and other required release files.

Extract a candidate archive into a new directory, add that directory to a clean
runtimepath, and invoke the command and help topic there. Source-checkout tests
alone do not establish correct archive layout or complete runtime contents.
