# LSP, DAP and document synchronization

Research: 2026-09-09. LSP baseline: stable 3.17; use newer draft features only
when both endpoints explicitly support them. DAP evolves through capability
negotiation rather than a blanket feature-version promise.

## LSP lifecycle and transport

LSP uses JSON-RPC 2.0. A stdio transport frames UTF-8 JSON with `Content-Length`
in **bytes**, followed by CRLF CRLF; ordinary logging belongs on stderr. Buffer
partial reads and parse multiple frames per read. One read is not necessarily
one message. Requests have IDs and need a result/error response; notifications
have no response. [Base protocol][ref-1].

Start with `initialize` containing client capabilities, root/workspace folders
and initialization options. Read the server capabilities and selected position
encoding, then send `initialized`. Only use advertised features. At shutdown,
request `shutdown`, await its response, then send `exit`; bound cleanup if the
process fails to respond. Terminate client-owned server processes at shutdown.
Disconnect from externally managed servers without taking ownership.

## Open buffers are authoritative

Send `textDocument/didOpen` with URI, languageId, version and complete text.
Follow the server's full/incremental synchronization capability. Incremental
`didChange` edits must apply in order against the state produced by preceding
changes, with increasing document versions. Send `didClose` when the client
relinquishes ownership; the server may then read disk. `didSave` inclusion of
text follows negotiated options.

LSP positions use zero-based lines and negotiated code units; UTF-16 is the
compatibility default when negotiation is absent. Do not count UTF-8 bytes for
an emoji-containing line. Preserve URI schemes/authority and distinguish
workspace folders in multi-root operation. A rename/delete must invalidate old
diagnostics and document identity correctly. [Document synchronization][ref-2].

## Cancellation and edits

Cancel a request with `$/cancelRequest` referencing its ID, but still handle its
eventual response. Cancellation is not guaranteed rollback. Maintain
per-document generations and discard stale hover/completion/diagnostic results.
Dynamic registration can change available features during the session; static
initialization is not the only capability source.

A `WorkspaceEdit` may contain versioned `TextDocumentEdit`s and resource
operations. Respect document versions, capability support and failure-handling
semantics; do not partially apply a multi-file rename while claiming atomic
success. On `workspace/applyEdit`, respond with actual `applied` and failure
information. Apply resource operations through URI-aware host APIs. Diagnostics
can be push or negotiated pull, and stale result IDs/versions require correct
invalidation. [Workspace edits][ref-3].

For synchronization changes, test unsaved text, non-ASCII positions, rapid
edits, cancellation, and close. Check undo/focus behavior in the affected host.

## DAP session and object lifetime

DAP uses length-framed JSON messages with `seq`, `type`, request `command`, and
response `request_seq`/`success`. It is not JSON-RPC. Exchange `initialize`
capabilities first, then launch or attach. The adapter emits `initialized` when
ready for breakpoint configuration; the client sends source breakpoint sets and,
when supported, `configurationDone`. Do not wait for a launch response before
sending configuration if the adapter is waiting for that configuration to
complete launch. [DAP overview][ref-4].

`setBreakpoints` replaces the set for a source, rather than appending individual
breakpoints. Report unverified or relocated breakpoints accurately. After
`stopped`, request threads, stack trace, scopes and variables. Frame/variable
references are session/suspension-scoped; do not reuse stale references after
execution resumes. Respect client path format and line/column-base capabilities.
[DAP schema][ref-5].

Launch owns starting a debuggee; attach connects to an existing process. Define
disconnect behavior using the supported terminate/suspend options so closing a
UI does not accidentally kill a user-owned process. `runInTerminal` is a reverse
request requiring client support and a concrete command/environment contract.
Validate program paths and arguments as data. Keep adapter logs off protocol
stdout and restrict listening sockets to the intended local/session boundary.

[ref-1]:
  https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#baseProtocol
[ref-2]:
  https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#textDocument_synchronization
[ref-3]:
  https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/#workspaceEdit
[ref-4]: https://microsoft.github.io/debug-adapter-protocol/overview
[ref-5]:
  https://github.com/microsoft/debug-adapter-protocol/blob/main/debugAdapterProtocol.json
