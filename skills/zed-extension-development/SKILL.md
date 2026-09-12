---
name: zed-extension-development
description: >-
  Build, repair, or review Zed extensions using declarative assets or
  supported Rust/WASM APIs with grammar and registry contracts. Use when
  implementing or diagnosing Zed languages, grammars, themes, snippets, LSP,
  DAP, MCP, extension.toml, registry packaging, or host behavior.
---

# Zed Extension Development

Select this workflow automatically when the task matches its description.
Selection supplies guidance only; it does not authorize operations beyond the
user's request.

Resolve the requested capability, host/API versions, and `extension.toml`. Use
declarative assets for supported static features and Rust/WASM hooks for
procedural behavior.

Read [host API and registry][ref-1] for manifests, server resolution, downloads,
lifecycle, and distribution. Read [languages and debuggers][ref-2] for grammars,
queries, DAP, themes, snippets, and MCP.

Align language names, grammar/server IDs, query nodes, and manifest paths.
Resolve tools through runtime worktree/host APIs. Pin managed downloads by
version, platform, and architecture. Handle partial downloads and launch
failures.

Validate affected assets and build procedural changes for the compatible WASM
target. Use a Dev Extension for affected host behavior. Check registry
requirements for publication.

Use the [language starter][ref-3] or [LSP starter][ref-4] for scaffolding.

[ref-1]: references/host-api-and-registry.md
[ref-2]: references/languages-and-debuggers.md
[ref-3]: assets/language-extension-template/TEMPLATE.md
[ref-4]: assets/lsp-extension-template/TEMPLATE.md
