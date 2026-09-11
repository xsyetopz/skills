---
name: editor-extension-design
description: >-
  Choose an editor target, design a cross-editor extension, or plan an extension
  port. Excludes ordinary implementation for an already-selected editor.
---

# Editor Extension Design

Use this skill for host selection, shared extension behavior, or ports. Route
ordinary implementation to the selected editor's workflow. Do not implicitly
invoke a manual implementation skill; its named-invocation policy still applies.

Map each capability to its execution location: UI, workspace, remote host,
browser, or external process. Confirm API availability before promising parity.

Read [host boundaries and ports][ref-1] for capability mapping, shared-core
contracts, adapter ownership, and worked ports. Read [protocols and
synchronization][ref-2] for LSP/DAP integration.

Keep portable semantics independent of host objects. Adapters own document
identity/version, position conversion, edits/undo, UI, settings, process
resolution, cancellation, and cleanup.

For ports, map commands, settings, persisted state, diagnostics, and
distribution. Define changed or unsupported behavior. Verify shared semantics
and affected adapter behavior separately. Shared tests alone do not establish
host parity.

[ref-1]: references/host-boundaries-and-ports.md
[ref-2]: references/protocols-and-synchronization.md
