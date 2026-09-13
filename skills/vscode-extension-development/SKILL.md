---
name: vscode-extension-development
description: >-
  Build or diagnose VS Code extensions across desktop, remote, and web hosts,
  including manifests, commands, providers, webviews, tests, and VSIX packaging.
---

# VS Code Extension Development

Resolve minimum `engines.vscode`, contributions, activation, `main`/`browser`,
and supported desktop/remote/web hosts. Match type declarations and packaged
entrypoints to that contract.

Read [hosts, trust, and packaging][ref-1] for manifests, placement, storage,
webviews, debugging, and distribution. Read
[document lifecycle](references/document-lifecycle.md) for providers, edits,
diagnostics, trees, cancellation, and state.

Use URI-aware workspace APIs. Browser workers cannot use Node filesystem/process
APIs. Guard workspace-controlled execution with Workspace Trust. Validate
webview messages and constrain scripts/resources.

Dispose registrations and owned processes at the correct lifetime. Reject
canceled or stale document results. Honor edit success and undo boundaries.

Run checks for affected hosts and features. Inspect production output and VSIX
contents for packaging changes. Use the
[starter](assets/extension-template/TEMPLATE.md) for scaffolding.

[ref-1]: references/hosts-trust-and-packaging.md
