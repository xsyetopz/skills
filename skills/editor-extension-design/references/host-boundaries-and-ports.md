# Capability mapping and adapter design

Research: 2026-09-09. Host baselines examined: VS Code 1.136.2, IntelliJ
Platform 2026.2 documentation, current Eclipse/PDE with Tycho 5.0.4, Neovim
0.12.5, Sublime stable 4200, and Zed 1.18.1/API 0.7.0.

## Choose a host by the required surface

- **Language diagnostics/completion across hosts** Natural implementation and
  boundary: Shared LSP server plus host configuration; confirm negotiated
  capabilities and available client support.

- **Deep IntelliJ refactoring/index integration** Natural implementation and
  boundary: PSI/index APIs in a product-compatible plugin; LSP alone may not
  expose the same semantics.

- **VS Code custom views/web UI** Natural implementation and boundary:
  Tree/custom editors/webviews through supported APIs; browser/remote placement
  changes filesystem and process access.

- **Eclipse workspace/RCP contributions** Natural implementation and boundary:
  OSGi/PDE extensions, Jobs and SWT; target-platform resolution owns
  compatibility.

- **Neovim commands and buffer behavior** Natural implementation and boundary:
  Lua/runtimepath APIs with byte-index and event-loop constraints.

- **Sublime command/syntax package** Natural implementation and boundary:
  Embedded Python and declarative package resources; no full browser DOM in
  minihtml.

- **Zed language/theme/debugger contribution** Natural implementation and
  boundary: Declarative assets or allowed WASM hooks; no promise of arbitrary
  editor event/UI parity.

API sources: [VS Code hosts][ref-1], [IntelliJ SDK][ref-2], [Eclipse
PDE][ref-3], [Neovim API](https://neovim.io/doc/user/api/), [Sublime
API][ref-4], or [Zed development][ref-5]. Refresh API availability for an
uncovered capability or different host version.

## Keep portable semantics free of host objects

A shared core can own parsing, transformation and protocol-neutral validation.
Each adapter owns editor identity/version, input snapshots, edits/undo, UI,
settings, storage, process resolution, cancellation and cleanup. Use a shared
library when hosts can load it safely; use a process/protocol boundary when
runtimes differ or isolation is valuable. Use a direct library call for small
local transforms. Include startup, transport, and deployment failures in server
contracts.

Example adapter contract:

```ts
type Snapshot = { uri: string; version: number; text: string };
type Replacement = { startUtf16: number; endUtf16: number; text: string };
type Analysis = { version: number; edits: Replacement[] };
interface Core {
  analyze(snapshot: Snapshot, signal: AbortSignal): Promise<Analysis>;
}
```

Define UTF-16 offsets, exclusive ends, nonoverlapping edits and
error/cancellation semantics. A host converts its byte/codepoint positions at
the boundary. The core must not return live editor objects or assume a URI is a
local path. The adapter rejects stale versions before applying one logical undo
operation. If the host cannot atomically check/apply, document the remaining
race or use its versioned edit mechanism.

## Worked port: VS Code transform to Neovim

Inventory the source command ID, configuration defaults/scopes, selected-text
rules, unsaved-buffer behavior, error messages and undo grouping. Extract the
pure transformation with text-in/text-out semantics. In VS Code, capture
`TextDocument.version` and apply through the editor API. In Neovim, capture
buffer number and changedtick, convert UTF-16 offsets to byte columns, schedule
mutation where required and check validity/tick immediately before editing.

Expose a namespaced Neovim command or `<Plug>` mapping; do not overwrite the
user's keybinding to mimic VS Code. Map workspace settings to explicit plugin
configuration/root selection, not a global shared default. A preview webview can
become a scratch buffer with accept/cancel commands if that meets the product
requirement; report that presentation change explicitly. Check non-ASCII
selection, concurrent edits and close/cancel behavior in each host; shared core
tests cover only semantic transformation.

## Worked port: native language plugin to Zed

Separate grammar/query assets and an LSP-capable server from IDE-specific PSI
services. Register language/grammar/server IDs in Zed and return the server
command through supported WASM hooks. Port diagnostics/hover using negotiated
LSP features; keep unsupported native project-model/refactoring behavior
explicit. Verify hook availability and mapped behavior in Zed.

## State and release migration

Assign persistent data a schema version and owner. Validate and migrate
idempotently. Commit the version marker after success. Handle malformed data
explicitly. Migrate renamed command/settings IDs and their consumers. Shared
server version, adapter version and host compatibility range are independent;
define which server versions each adapter accepts and release in an order
compatible with installed clients.

Package each adapter with its runtime assets and dependencies. Select external
binaries by version/platform and honor configured tool overrides. Read [LSP and
DAP contracts][ref-6] when introducing a protocol boundary.

[ref-1]: https://code.visualstudio.com/api/advanced-topics/extension-host
[ref-2]: https://plugins.jetbrains.com/docs/intellij/welcome.html
[ref-3]:
  https://help.eclipse.org/latest/topic/org.eclipse.pde.doc.user/guide/intro/pde_overview.htm
[ref-4]: https://www.sublimetext.com/docs/api_reference.html
[ref-5]: https://zed.dev/docs/extensions/developing-extensions
[ref-6]: protocols-and-synchronization.md
