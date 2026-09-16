# Source index and freshness rules

This index is for source discovery and version checking. It is not a substitute
for the operational rules in `SKILL.md` and the other references. Open the
underlying source; do not treat a search snippet, generated summary, or copied
example as authority.

## Source order

1. Inspect the target repository, installed tool versions, lockfiles, generated
   relationships, and existing validation commands.
1. Use the exact product or language version's official documentation and
   source.
1. Use standards and protocol specifications for normative behavior.
1. Use issue trackers and community reports to discover failure patterns, then
   reproduce the relevant behavior locally before changing production code.

For changing products, record the page or source revision and access date in the
work product when the decision depends on it. Do not silently transfer an API or
limit from another version, fork, operating system, runtime, or hosting tier.

## Primary sources

| Source | Applicability |
| --- | --- |
| [Neovim API](https://neovim.io/doc/user/api.html) | Primary Neovim API reference. |
| [Lua plugin guide](https://neovim.io/doc/user/lua-guide.html) | Neovim Lua plugin organization and APIs. |
| [Testing Neovim](https://neovim.io/doc/user/testing.html) | Host testing guidance where applicable. |
| [GitHub source: neovim/neovim — api.txt](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/api.txt) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: neovim/neovim — health.txt](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/health.txt) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: neovim/neovim — helphelp.txt](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/helphelp.txt) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: neovim/neovim — lsp.txt](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lsp.txt) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: neovim/neovim — lua.txt](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/lua.txt) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: neovim/neovim — starting.txt](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/starting.txt) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: neovim/neovim — undo.txt](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/undo.txt) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: neovim/neovim — usr_05.txt](https://github.com/neovim/neovim/blob/v0.12.5/runtime/doc/usr_05.txt) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: neovim/neovim/releases/tag/v0.12.5](https://github.com/neovim/neovim/releases/tag/v0.12.5) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [neovim.io: api](https://neovim.io/doc/user/api/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [neovim.io: lua guide](https://neovim.io/doc/user/lua-guide/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [neovim.io: lua](https://neovim.io/doc/user/lua/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
