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
| [VS Code Extension API](https://code.visualstudio.com/api) | Primary extension API and guides. |
| [VS Code extension host](https://code.visualstudio.com/api/advanced-topics/extension-host) | Host placement and capability model. |
| [Workspace Trust](https://code.visualstudio.com/docs/editor/workspace-trust) | Trust semantics for workspace-controlled execution. |
| [code.visualstudio.com: tree view](https://code.visualstudio.com/api/extension-guides/tree-view) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: virtual workspaces](https://code.visualstudio.com/api/extension-guides/virtual-workspaces) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: web extensions](https://code.visualstudio.com/api/extension-guides/web-extensions) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: webview](https://code.visualstudio.com/api/extension-guides/webview) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: workspace trust](https://code.visualstudio.com/api/extension-guides/workspace-trust) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: programmatic language features](https://code.visualstudio.com/api/language-extensions/programmatic-language-features) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: activation events](https://code.visualstudio.com/api/references/activation-events) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: extension manifest](https://code.visualstudio.com/api/references/extension-manifest) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: vscode api](https://code.visualstudio.com/api/references/vscode-api) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: publishing extension](https://code.visualstudio.com/api/working-with-extensions/publishing-extension) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: testing extension](https://code.visualstudio.com/api/working-with-extensions/testing-extension) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [code.visualstudio.com: updates](https://code.visualstudio.com/updates) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: microsoft/vscode-docs — publishing-extension.md](https://github.com/microsoft/vscode-docs/blob/main/api/working-with-extensions/publishing-extension.md) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
