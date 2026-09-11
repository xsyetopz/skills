# Neovim capability and starter evaluation

Evaluated 2026-09-11. Scope: `neovim-plugin-development`, not the full editor
collection or all repository requirements.

## Boundary and implementation

The starter is now one synchronous range command using `vim.json.encode` and one
buffer replacement. It demonstrates the actual boundary between inclusive Ex
ranges and zero-based, end-exclusive buffer APIs. It does not implement JSON
escaping, impose a plugin manager, or invent a package manifest.

Removed the greeting, configuration module, unnecessary setup function, and a
health check that warned about a placeholder executable. Two references replace
six inherited fragments and explain runtime ownership and integration/validation
without an extra router. Public help describes actual command behavior instead
of template text.

The inherited uncommitted explicit-only metadata addition was absent from the
original committed skill and unsupported by a user request. It was removed to
retain ordinary discovery. Skill counts were not used as a design constraint.

## Primary evidence and tools

- [Neovim 0.12.5 release][source-1]:
  current stable returned by the official releases endpoint. Its official macOS
  ARM64 binary was downloaded and executed.
- [Neovim 0.10.4 release][source-3]:
  separately downloaded and executed as the example's declared support floor.
  This does not claim the APIs were introduced in 0.10.4.
- Installed help plus pinned upstream
  [API](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/api.txt),
  [Lua](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt),
  [startup][source-2],
  and [undo](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/undo.txt)
  contracts: range indexing, textlock, subprocess startup errors, JSON encoding,
  noninteractive script exits, and undo boundaries.
- [StyLua 2.5.2](https://github.com/JohnnyMorganz/StyLua/releases/tag/v2.5.2):
  official formatter binary and its actual CLI help. Formatting/checks used
  `--indent-type Spaces --indent-width 2` to preserve existing Lua conventions.
  No lint rule or formatter configuration was disabled. The user's current
  public repository inventory had no other matching Lua/Neovim project to copy
  tooling from; no speculative root configuration was added.

## Executed host checks

The inherited smoke command ran successfully on 0.12.5, but checked
registration, health invocation, and help-tag generation rather than a useful
buffer operation. The new smoke script checks actual outcomes:

- a multi-line range with quotes, backslashes, Unicode, and an empty line;
- preservation of the surrounding lines;
- whole-command undo and redo;
- the cursor line as the default range;
- an empty buffer line encoded as an empty string, not a missing element;
- `nomodifiable` rejects mutation without changing the buffer;
- `readonly` still permits in-memory editing, unlike `nomodifiable`;
- the command works after repeated plugin loading;
- generated help tags resolve the advertised command topic.

An initial expectation of an Ex `E21` diagnostic was incorrect for this API
path. The test now asserts that the host rejects the operation and preserves
contents, not a diagnostic string belonging to a different interface.

The script passed on both 0.10.4 and 0.12.5. Runs used copied workspaces with
isolated XDG config/data/state/cache directories and the documented invocation:

```sh
nvim --clean --headless -u tests/minimal_init.lua -l tests/smoke.lua
```

A temporary fault changed the one-based range conversion from `first - 1` to
`first`. The first range assertion failed with the wrong retained/encoded lines
and exit status 1. This verifies that test success depends on the boundary
behavior, not just command registration.

## Artifact and static checks

A TAR archive contained only `plugin/example.lua`, `lua/example/init.lua`, and
`doc/example.txt`. It was extracted into a new path containing a space. Tests
were copied there separately; no source checkout was on its runtimepath. The
same behavior/help checks passed against the extracted artifact on both hosts.
Generated help tags remained in the disposable workspace, not the repository.

StyLua check, official skills-ref, bundled quick validation, existing Markdown
rules, relative links, and `git diff --check` passed. No system Lua interpreter
or mock `vim` module was used as evidence for editor behavior.

This starter does not exercise rendered UI, LSP servers, native dependencies,
other operating systems, hosted publication, or a production async integration.
Those remain separate task-specific validation obligations.

## Independent forward evaluation

A fresh-context reviewer used the skill to repair a supplied asynchronous
external filter that read and wrote buffer `0` at different times. The task
required preserving the external process, preventing overwrites of another
buffer or intervening edits, reporting failed invocations, and stating any
unspecified concurrency/newline policy. No repository implementation was
supplied.

The repair captures the original buffer, changedtick, and buffer-local request
identity. It schedules application, rejects stale/unloaded/unmodifiable targets,
and reports nonzero exit/signal status with stderr. It preserves literal LF
splitting and explicitly chooses latest-started-request wins. It adds neither a
formatter nor a shell command. Buffer-local identity avoids a global table of
visited buffers.

Real Neovim subprocess tests exercised `cat`, switching buffers during a delayed
process, and an exit-7/stderr failure. Separate tests mocked only process
completion delivery inside the real editor to order overlapping requests and an
intervening user edit deterministically. These are not presented as real
subprocess ordering evidence. Both scripts passed on 0.10.4 and 0.12.5.

Integration review found the original overlap assertion could pass using only
changedtick: applying the newer output itself invalidated the older one. An
additional case fails the newer request without changing the text, then delivers
the older success. Both hosts reject that superseded success. Removing only the
request-identity check in a temporary fault copy makes this assertion fail with
`old output` and exit status 1. This distinguishes request ownership from text
freshness.

The forward repair does not cancel an external process on buffer wipe; it only
prevents its result from applying. Process teardown, hung processes, synchronous
spawn failure, and rendered UI remain untested. This evaluation proves the
requested overwrite repair, not complete async resource-lifecycle coverage.
Temporary forward fixtures are not added as another production starter.

Final metadata routing was evaluated for all seven required prompt categories:

| Prompt category                   | Observed routing                  |
| --------------------------------- | --------------------------------- |
| Explicit skill request            | Neovim skill                      |
| Paraphrased Neovim overwrite bug  | Neovim skill                      |
| Incomplete Neovim repair request  | Neovim; obtain missing behavior   |
| Adjacent VS Code extension repair | VS Code skill, not Neovim         |
| Unrelated browser application     | No Neovim skill                   |
| Ambiguous editor extension        | Select host before implementation |
| Neovim plugin plus GitHub Actions | Neovim and CI skills together     |

These are reviewer routing decisions from metadata, not telemetry proving that
every client or model activates the skill identically.

[source-1]: https://github.com/neovim/neovim/releases/tag/v0.12.5
[source-2]: https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/starting.txt
[source-3]: https://github.com/neovim/neovim/releases/tag/v0.10.4
