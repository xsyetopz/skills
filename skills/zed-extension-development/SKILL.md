---
name: zed-extension-development
description: >-
  Build or diagnose Zed extensions using declarative assets or supported
  Rust/WASM APIs for languages, grammars, themes, LSP, DAP, MCP, and packaging.
---

# Zed Extension Development

Resolve the requested capability, host/API versions, and `extension.toml`. Use
declarative assets for supported static features and Rust/WASM hooks for
procedural behavior.

Read [host API and registry][ref-1] when changing manifests, server resolution,
downloads, lifecycle, or distribution. Read [languages and debuggers][ref-2] for
grammar, query, debugger-adapter, theme, snippet, or MCP-server changes.

Align language names, grammar/server IDs, query nodes, and manifest paths.
Resolve tools through runtime worktree/host APIs. Pin managed downloads by
version, platform, and architecture. Handle partial downloads and launch
failures.

Validate affected assets and build procedural changes for the compatible WASM
target. Use a Dev Extension for affected host behavior. Check registry
requirements for publication.

For scaffolding, use the [language starter][ref-3] for grammar/query assets or
the [LSP starter][ref-4] for a procedural language-server adapter. Do not load
both unless the requested feature needs both.

[ref-1]: references/host-api-and-registry.md
[ref-2]: references/languages-and-debuggers.md
[ref-3]: assets/language-extension-template/TEMPLATE.md
[ref-4]: assets/lsp-extension-template/TEMPLATE.md
