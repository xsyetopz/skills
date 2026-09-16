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
| [DuckStation source](https://github.com/stenzek/duckstation) | Authoritative upstream source and build/config behavior. |
| [DuckStation official site](https://www.duckstation.org/) | Official releases and user-facing information. |
| [psx-spx](https://psx-spx.consoledev.net/) | Technical PlayStation hardware/reference material; validate against target behavior. |
| [GitHub: duckstation/dependencies](https://github.com/duckstation/dependencies) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: stenzek/duckstation.git](https://github.com/stenzek/duckstation.git) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: stenzek/duckstation — README.md](https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/README.md) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: stenzek/duckstation — gdb_server.cpp](https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/gdb_server.cpp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: stenzek/duckstation — hotkeys.cpp](https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/hotkeys.cpp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: stenzek/duckstation — pcdrv.cpp](https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/pcdrv.cpp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: stenzek/duckstation — settings.cpp](https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/settings.cpp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: stenzek/duckstation — settings.h](https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/settings.h) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: stenzek/duckstation — system.cpp](https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/core/system.cpp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: stenzek/duckstation — qthost.cpp](https://github.com/stenzek/duckstation/blob/cbe7951be624a3fd69c81858647a8f84e4a1d06b/src/duckstation-qt/qthost.cpp) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: stenzek/duckstation — README.md](https://github.com/stenzek/duckstation/blob/master/README.md) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: stenzek/duckstation/wiki/Enabling-Logging](https://github.com/stenzek/duckstation/wiki/Enabling-Logging) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: stenzek/duckstation/wiki/Texture-Replacement](https://github.com/stenzek/duckstation/wiki/Texture-Replacement) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
