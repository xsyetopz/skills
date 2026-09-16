# Editor-extension boundaries

Use the host's declarative contribution mechanism first when it fully implements
the feature: language configuration, grammar, snippets, theme, key binding, or
command contribution. Add executable code only for behavior the host cannot
express declaratively.

Keep host handles, editor documents, UI objects, cancellation tokens, and host
lifecycle in the host adapter. Share a pure transformation library when the
runtimes and packaging permit it. Use LSP for language intelligence and DAP for
debugging when those protocols fit; do not invent a competing JSON-RPC dialect
merely to share code. A companion process is justified by an existing
tool/runtime or isolation need, not by the number of editors alone.

For each request, capture document identity and version plus a request
generation. On completion, check cancellation, document lifetime, and freshness
before applying results. A delayed result for version N must not overwrite
version N+1. Map position encodings explicitly; byte offsets, UTF-16 positions,
and code-point indices are not interchangeable.

Specify process ownership, startup readiness, shutdown, crash reporting, and
bounds on queued work. Distinguish a restartable failed tool from a
non-idempotent operation that may already have changed files. Do not silently
retry writes after losing a response.

Expose native host settings and protocol capabilities without flattening them to
the least capable editor. An unsupported capability must be reported, not
simulated through a misleading UI. Keep the shared core independent of host
event buses and filesystem assumptions.

Validate one complete feature in each claimed host: activation, request,
user-visible result, undo/cancellation where applicable, and cleanup on unload.
A shared unit test or protocol handshake does not prove all host integrations
work.

Sources: [LSP specification][ref-lsp-specification], [DAP
overview][ref-dap-overview], [VS Code extension
architecture][ref-vs-code-extension-architecture].

[ref-lsp-specification]: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/
[ref-dap-overview]: https://microsoft.github.io/debug-adapter-protocol/overview
[ref-vs-code-extension-architecture]: https://code.visualstudio.com/api/advanced-topics/extension-host
