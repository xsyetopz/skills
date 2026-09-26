# Protocols and pipelines

Architecture choices at protocol boundaries (LSP, DAP) and the contracts
of processing pipelines. The LSP examples run in
[`assets/examples/protocols/`][protocols]. Editor-specific wiring lives in
the editor skills (`$develop-vscode-extensions`, `$develop-neovim-plugins`,
`$develop-zed-editor-extensions`, and others).

## Contents

- LSP framing counts bytes
- Position encoding negotiation
- LSP lifecycle and document ownership
- Cancellation is not rollback
- Debug adapter sessions
- Pipeline contracts by kind
- Host adapter around a portable core

## LSP framing counts bytes

**Definition.** LSP uses JSON-RPC 2.0. Each message starts with a
`Content-Length` header that counts the **bytes** of the UTF-8 body;
`\r\n\r\n` separates the header from the body. One read can hold part
of a message or several messages ([LSP 3.17][lsp]).

**Use when.** Writing or debugging a client or server transport.

**Do not use when.** A maintained LSP library exists for your language;
use it instead of hand-writing framing.

**Example.** From `lsp_framing.py`:

```python
def encode(message: dict) -> bytes:
    body = json.dumps(message, ensure_ascii=False).encode("utf-8")
    return f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
```

The `Reader` class buffers chunks; the test feeds two frames in 7-byte
pieces and gets both messages.

**Cost removed.** Hangs and parse errors on non-ASCII text, whose
character count differs from its byte count.

**Verify.**

1. `test_length_counts_bytes_not_characters` and
   `test_split_and_merged_reads` pass.

## Position encoding negotiation

**Definition.** LSP positions are a zero-based line and a `character`
offset. The offset counts UTF-16 code units unless the peers negotiated
UTF-8 or UTF-32 through `positionEncoding`.

**Use when.** Converting between editor columns and LSP positions.

**Do not use when.** No exception: never assume the offset counts bytes
or Python characters.

**Example.** On the line `a😀b`, the column before `b`:

| Encoding | `character` |
| --- | --- |
| utf-16 (default) | 3 |
| utf-8 | 5 |
| utf-32 | 2 |

**Cost removed.** Diagnostics and edits that land one or two characters
off after an emoji or other non-BMP character.

**Verify.**

1. `test_position_units_differ_after_an_emoji` passes, and the client
   reads `positionEncoding` from the initialize result.

## LSP lifecycle and document ownership

**Definition.** A session runs these steps:

1. `initialize`, with client capabilities;
1. the server replies with its capabilities;
1. `initialized`;
1. work, using only the features the server advertised;
1. `shutdown`, then `exit`.

While a document is open (from `didOpen` to `didClose`), the client's
buffer is the truth, not the disk. The version increases with each
`didChange`.

**Use when.** Designing the editor/server split.

**Do not use when.** No exception: a server that reads an open file from
disk sees stale text.

**Example.** A formatter server receives `didOpen` with the full text
and version 1. Each edit sends `didChange` with the version increased by
one, and the server computes results against that version.

**Cost removed.** Edits applied to the wrong version of a file.

**Verify.**

1. In an integration test, the client discards a stale-version result
   and does not apply its edit.

## Cancellation is not rollback

**Definition.** `$/cancelRequest` asks the other side to stop. The
response may still arrive, and effects that already happened stay. Track
a generation per document and drop results older than the current
generation.

**Use when.** A request can be superseded: completion, formatting,
diagnostics.

**Do not use when.** You need to undo a write; cancellation does not.

**Example.** A format result for version 4 arrives after the buffer is
at version 5. The client drops it instead of applying it.

**Cost removed.** Stale edits clobbering newer text.

**Verify.**

1. A test sends a change during a slow request and asserts that the old
   result is not applied.

## Debug adapter sessions

**Definition.** The Debug Adapter Protocol has its own lifecycle:
`initialize`, then `launch` or `attach`, `configurationDone`, events,
and `disconnect`. Object references such as variables and frames are
valid only while execution is stopped ([DAP][dap]).

**Use when.** Integrating a debugger with an editor.

**Do not use when.** You would reuse LSP's envelope or lifetimes; DAP is a
different protocol.

**Example.** Cache `variablesReference` values only until the next
`continued` event.

**Cost removed.** Invalid-reference errors after stepping.

**Verify.**

1. After a step, the client requests frames again instead of reusing
   old references.

## Pipeline contracts by kind

**Definition.** Each kind of pipeline has its own guarantees to design and
test:

| Kind | Contract | Test |
| --- | --- | --- |
| In-process transform | typed stages, local errors | stage outputs, error propagation |
| ETL | provenance, replay, schema evolution | rerun from checkpoint, bad records |
| Stream | event time, ordering, backpressure | late and duplicate events |
| Message queue | durability, ack after effect, idempotency | duplicate delivery, crash before ack |
| CI/CD | immutable artifacts, promotion, rollback | same digest promoted; rollback drill |

**Use when.** Designing or reviewing any pipeline.

**Do not use when.** You would choose a pipeline tool before knowing its
contract.

**Example.** A message consumer places orders through the same
`place_order(..., idempotency_key=message_id)`, so a redelivered message
creates no second order.

**Cost removed.** Pipelines that lose or duplicate data under failure.

**Verify.**

1. Each contract in the row has a test that triggers its failure mode.

## Host adapter around a portable core

**Definition.** Keep portable logic free of host objects. The host
adapter translates the editor's documents, settings, and edits into the
core's plain types, and owns processes, cancellation, and undo.

**Use when.** One capability targets several editors or hosts.

**Do not use when.** There is one host and no second one planned; write
it natively.

**Example.** The formatter decision in
`assets/boundary-decision-example.md`:

- the host owns document identity and undo;
- the adapter owns the child process;
- the formatter owns only its bytes.

**Cost removed.** Rewriting the core for each editor.

**Verify.**

1. The core's tests import no host API. Run `check_layers.py` with a host
   layer that only the adapters may use.

[protocols]: ../assets/examples/protocols/lsp_framing.py
[lsp]: https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/
[dap]: https://microsoft.github.io/debug-adapter-protocol/overview
