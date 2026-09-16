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
| [Sublime Text API reference](https://www.sublimetext.com/docs/api_reference.html) | Primary host API reference. |
| [Sublime packages](https://www.sublimetext.com/docs/packages.html) | Package/resource/distribution behavior. |
| [Sublime plugin basics](https://www.sublimetext.com/docs/plugin_basics.html) | Commands and lifecycle concepts. |
| [GitHub: SublimeText/UnitTesting](https://github.com/SublimeText/UnitTesting) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [packagecontrol.io: submitting a package](https://packagecontrol.io/docs/submitting_a_package) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.sublimetext.com: api environments.html](https://www.sublimetext.com/docs/api_environments.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.sublimetext.com: command line.html](https://www.sublimetext.com/docs/command_line.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.sublimetext.com: minihtml.html](https://www.sublimetext.com/docs/minihtml.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.sublimetext.com: safe mode.html](https://www.sublimetext.com/docs/safe_mode.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.sublimetext.com: syntax.html](https://www.sublimetext.com/docs/syntax.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [www.sublimetext.com: download](https://www.sublimetext.com/download) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
