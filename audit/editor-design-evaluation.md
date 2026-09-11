# Cross-editor design evaluation

Evaluated 2026-09-12. This accepts the planning skill, not the pending editor
implementation templates or a claim of runtime parity across all editors.

## Scope and corrections

Consolidated nine short fragments and two routing references into two
substantive references. Their only live callers were the skill's own routers;
the baseline inventory remains a historical record. No separate skill was added.

Removed the unconditional requirement to assign persistent data a schema
version. Stateless ports require no persistence or migration system. Existing
persisted compatibility boundaries now determine whether migration is needed.
Removed an unnecessary asynchronous TypeScript interface from the
simple-transform design; start with text-in/text-out and add only required
adapter responsibilities.

An implicit planning skill must not indirectly activate a manual implementation
skill. The entrypoint now preserves that invocation boundary explicitly.

## Source verification

Rechecked official VS Code host placement, Zed extension surfaces, LSP 3.17
source, and DAP lifecycle guidance. Removed inherited blanket host-version
baselines rather than implying that every host had been exercised here.

The rendered LSP page exposed navigation without the detailed sections. Read the
[official Markdown source][lsp-source] and its position, workspace-edit,
didOpen, didChange, and shutdown includes instead. Verified byte-counted
framing, cancellation response obligations, negotiated positions, ordered
changes, workspace failure semantics, and shutdown-before-exit sequencing.

Corrected two overgeneralizations:

- UTF-8 bytes are valid position units when UTF-8 is negotiated. UTF-16 remains
  the compatibility default, not the only permitted representation.
- The [DAP overview][dap] distinguishes stopped-stack reference lifetime from
  thread IDs and evaluate/output references; not every identifier expires on
  resume.

Request generations belong to a superseding operation, not a global counter that
invalidates unrelated features. Push diagnostics lack an originating request ID;
do not pretend a local request-generation test orders those notifications.

## Independent forward task and integration

A fresh-context evaluator used the skill to plan a stateless VS Code JSON sorter
port to Neovim, a remote LSP adapter with same-version overlapping requests, and
the evidence needed before promising IntelliJ PSI-to-Zed parity. The evaluator
received no expected answer and made no repository edits.

The answer retained a synchronous core, proposed no persistence/backend,
required single-undo and non-mutation-on-error checks, reused maintained LSP
machinery, recognized the same-version race, and declined unsupported PSI parity
claims. It distinguished untestable push ordering from request/response
ordering. This is design evidence, not an executed port.

Integration rejected two claims in the answer: “never UTF-8 byte counts” and a
blanket end-exclusive description of Neovim ranges. The reference now states the
actual `nvim_buf_set_text` end-row/end-column distinction. The evaluator's raw
answer remains at `/tmp/editor-design-forward-result.md`; it is not normative
guidance. The [Neovim API reference][nvim] governs the range contracts.

## Validation and limits

The package passes official skills-ref and the bundled quick validator. Its
three Markdown files pass the strict repository configuration, and all local
Markdown links resolve. No executable assets were added. Earlier real Neovim and
Sublime host tests remain separately scoped evidence, not proof of LSP/DAP
transport behavior or Zed/IntelliJ feature parity.

[lsp-source]:
  https://github.com/microsoft/language-server-protocol/blob/gh-pages/_specifications/lsp/3.17/specification.md
[dap]: https://microsoft.github.io/debug-adapter-protocol/overview
[nvim]: https://neovim.io/doc/user/api/#nvim_buf_set_text()
