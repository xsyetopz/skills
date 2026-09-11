---
name: vscode-extension-development
description: >-
  Use only when explicitly invoked by name. Build, repair, or review VS Code
  extensions across desktop, remote, or web hosts with Workspace Trust, URI, and
  lifecycle constraints.
---

# VS Code Extension Development

Run this workflow only when the user explicitly invokes this skill by name. A
related keyword or an ordinary implementation request is not an invocation.

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
