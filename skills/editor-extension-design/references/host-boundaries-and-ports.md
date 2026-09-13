# Capability mapping and adapter design

Reviewed 2026-09-12. Confirm the actual target host and negotiated capabilities;
these design contracts are not a promise of support in every host release.

## Choose a host by the required surface

- **Language diagnostics/completion across hosts** Natural implementation and
  boundary: An existing LSP server/client implementation where suitable; confirm
  negotiated capabilities and available client support.

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

API sources: [VS Code hosts][1-source-2],
[IntelliJ SDK](https://plugins.jetbrains.com/docs/intellij/welcome.html),
[Eclipse PDE][1-source-1], [Neovim API](https://neovim.io/doc/user/api/),
[Sublime API](https://www.sublimetext.com/docs/api_reference.html), or
[Zed development](https://zed.dev/docs/extensions/developing-extensions).
Refresh API availability for an uncovered capability or different host version.

[1-source-1]:
  https://help.eclipse.org/latest/topic/org.eclipse.pde.doc.user/guide/intro/pde_overview.htm
[1-source-2]: https://code.visualstudio.com/api/advanced-topics/extension-host

## Keep portable semantics free of host objects

Map each required user operation to host capabilities and acceptance evidence
before extracting a shared core. Separate required parity from a negotiable
presentation choice. Compare a direct host implementation, a shared library,
and a server only where viable; include startup latency, data transfer, failure
isolation, runtime availability, and package/update cost in the decision.
Sharing code is not beneficial if it forces every host to emulate another's
document model. Keep cohesive transformation rules together while adapters own
their host-specific state and effects. Trace both data and cancellation through
the chosen boundary, including errors returning to the user.

A shared core can own parsing, transformation and protocol-neutral validation.
Each adapter owns editor identity/version, input snapshots, edits/undo, UI,
settings, storage, process resolution, cancellation and cleanup. Use a shared
library when hosts can load it safely; use a process/protocol boundary when
runtimes differ or isolation is valuable. Use a direct library call for small
local transforms. Include startup, transport, and deployment failures in server
contracts.

Choose the smallest contract the transformation needs. A synchronous text-in,
text-out function needs neither document identity nor an asynchronous service
interface. Add offsets only for partial replacements; define their units and
exclusive ends. Use the host's edit types in the adapter, not a new wire schema.

For asynchronous work that supersedes earlier results, capture identity,
document version, and a generation for that operation in the adapter. Do not
make unrelated features invalidate each other. A version check alone cannot
distinguish two requests on the same unchanged document. Apply only a
still-current result, using the host's versioned edit mechanism or a synchronous
check/apply boundary. Keep one logical undo operation. Cancellation is a request
to stop, not proof that work stopped.

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
tests cover only semantic transformation. Do not generalize one API's indexing
rules to every Neovim range: `nvim_buf_set_text` has an inclusive end row and an
exclusive end column, while `nvim_buf_set_lines` uses an exclusive end row. Test
visual-selection conversion separately from the resulting API range.

## Worked port: native language plugin to Zed

Separate grammar/query assets and an LSP-capable server from IDE-specific PSI
services. Register language/grammar/server IDs in Zed and return the server
command through supported WASM hooks. Port diagnostics/hover using negotiated
LSP features; keep unsupported native project-model/refactoring behavior
explicit. Verify hook availability and mapped behavior in Zed.

## State and release migration

Do not introduce persistence, a schema version, or a migration framework for a
stateless extension. For an existing persisted compatibility boundary, identify
its owner and format before changing it. Prefer the host's storage APIs and
existing migration convention. When a format change actually needs migration,
make retries safe and write a completion marker only after success. Handle
malformed data explicitly. Migrate renamed command/settings IDs only when
existing consumers require compatibility. Shared server version, adapter version
and host compatibility range are independent; define which server versions each
adapter accepts and release in an order compatible with installed clients.

Package each adapter with its runtime assets and dependencies. Select external
binaries by version/platform and honor configured tool overrides. Read
[LSP and DAP contracts](protocols-and-synchronization.md) when introducing a
protocol boundary.
