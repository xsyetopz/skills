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
| [IntelliJ Platform SDK](https://plugins.jetbrains.com/docs/intellij/welcome.html) | Primary plugin development guide. |
| [Threading model](https://plugins.jetbrains.com/docs/intellij/threading-model.html) | Read/write and coroutine threading rules. |
| [Plugin configuration file](https://plugins.jetbrains.com/docs/intellij/plugin-configuration-file.html) | plugin.xml registration and metadata. |
| [GitHub: JetBrains/intellij-platform-gradle-plugin/releases/tag/2.18.1](https://github.com/JetBrains/intellij-platform-gradle-plugin/releases/tag/2.18.1) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: action system.html](https://plugins.jetbrains.com/docs/intellij/action-system.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: build number ranges.html](https://plugins.jetbrains.com/docs/intellij/build-number-ranges.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: disposers.html](https://plugins.jetbrains.com/docs/intellij/disposers.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: documents.html](https://plugins.jetbrains.com/docs/intellij/documents.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: indexing and psi stubs.html](https://plugins.jetbrains.com/docs/intellij/indexing-and-psi-stubs.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: persisting state of components.html](https://plugins.jetbrains.com/docs/intellij/persisting-state-of-components.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: plugin services.html](https://plugins.jetbrains.com/docs/intellij/plugin-services.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: plugin signing.html](https://plugins.jetbrains.com/docs/intellij/plugin-signing.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: psi.html](https://plugins.jetbrains.com/docs/intellij/psi.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: publishing plugin.html](https://plugins.jetbrains.com/docs/intellij/publishing-plugin.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: tools intellij platform gradle plugin tasks.html](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-tasks.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: tools intellij platform gradle plugin types.html](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin-types.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [plugins.jetbrains.com: tools intellij platform gradle plugin.html](https://plugins.jetbrains.com/docs/intellij/tools-intellij-platform-gradle-plugin.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
