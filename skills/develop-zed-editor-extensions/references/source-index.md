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
| [Zed extensions documentation](https://zed.dev/docs/extensions) | Primary extension documentation. |
| [Zed extension API source](https://github.com/zed-industries/zed/tree/main/crates/extension_api) | Version-sensitive extension API source. |
| [Zed extensions registry](https://github.com/zed-industries/extensions) | Official extension examples and registry conventions. |
| [docs.rs: zed extension api](https://docs.rs/zed_extension_api/0.7.0/zed_extension_api/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.rs: trait.Extension.html](https://docs.rs/zed_extension_api/0.7.0/zed_extension_api/trait.Extension.html) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [docs.rs: zed extension api](https://docs.rs/zed_extension_api/latest/zed_extension_api/) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: example/example-language](https://github.com/example/example-language) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: zed-industries/zed — README.md](https://github.com/zed-industries/zed/blob/v1.19.2/crates/extension_api/README.md) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub source: zed-industries/zed — lsp_store.rs](https://github.com/zed-industries/zed/blob/v1.19.2/crates/project/src/lsp_store.rs) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [GitHub: zed-industries/zed/releases/tag/v1.19.2](https://github.com/zed-industries/zed/releases/tag/v1.19.2) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: debugger extensions](https://zed.dev/docs/extensions/debugger-extensions) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: developing extensions](https://zed.dev/docs/extensions/developing-extensions) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: icon themes](https://zed.dev/docs/extensions/icon-themes) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: languages](https://zed.dev/docs/extensions/languages) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: mcp extensions](https://zed.dev/docs/extensions/mcp-extensions) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: license requirements](https://zed.dev/docs/extensions/publishing/license-requirements) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: prerequisites](https://zed.dev/docs/extensions/publishing/prerequisites) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: publishing guide](https://zed.dev/docs/extensions/publishing/publishing-guide) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: updating and maintenance](https://zed.dev/docs/extensions/publishing/updating-and-maintenance) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: snippets](https://zed.dev/docs/extensions/snippets) | Use for the exact target version or source revision; verify applicability before copying an API or command. |
| [zed.dev: themes](https://zed.dev/docs/extensions/themes) | Use for the exact target version or source revision; verify applicability before copying an API or command. |

## Updating this reference

Update a link only after confirming the replacement covers the same contract. If
a source disappears, preserve the rule supported by local evidence and mark the
external verification gap; do not invent a new behavior from memory.
