# Providers, cancellation and document ownership

Research: 2026-09-11; stable VS Code API, baseline 1.137.

## Register a narrowly selected provider

Choose a document selector whose language and URI schemes match the provider's
actual inputs. Register it through `context.subscriptions`. Use the synchronous
provider form for a cheap synchronous result; do not add artificial promises to
justify cancellation scaffolding.

For a real asynchronous analysis, capture the document version, requested range
and input text before awaiting. Pass cancellation to the operation when
supported. Before publishing the result, check cancellation, document closure
and version changes. Maintain separate generations when concurrent requests can
supersede each other without a document edit.

A `file` selector excludes untitled/virtual documents; broaden it only when the
implementation supports them. Capture immutable inputs before awaiting and
reject stale results afterward. A cancellation token signals intent; pass it to
the real operation or map it to an AbortController/process cancellation when
supported. [Language features][source-0-1].

[source-0-1]:
  https://code.visualstudio.com/api/language-extensions/programmatic-language-features

## Edits, undo and diagnostics

For a user command, resolve the target editor/document when invoked. If work
awaits external results, snapshot version/text and re-check identity/version
immediately before `TextEditor.edit` or `workspace.applyEdit`. Synchronous
transformations can construct the edit immediately without redundant version
state. Honor the returned boolean. A check followed by a long await still
permits stale edits; versioned protocol edits provide stronger protection when
using LSP. Do not retain a `TextEditorEdit` builder across asynchronous work.

Use a single edit transaction for one logical user operation; define selection
and undo expectations. Apply nonoverlapping replacements against one snapshot.
Unsaved buffers are authoritative over disk content; filesystem reads alone miss
current edits.
[Editor/workspace API](https://code.visualstudio.com/api/references/vscode-api).

Create one owned `DiagnosticCollection`, set results by URI, and remove
diagnostics when a document is no longer relevant. A late analysis must not
overwrite a newer set. Debounce expensive document-change work with per-document
generations, cancel the prior request and clear timers on close. A watcher
indicates a possible filesystem change, not a reliable document version counter.

## Services, trees and process lifetime

A `TreeDataProvider` supplies data and an `onDidChangeTreeData` event; refresh
only the changed subtree when possible. Keep stable item IDs for
expansion/selection continuity. Commands attached to items must validate that
the target still exists. Use host theme colors and semantic icons.
[Tree views](https://code.visualstudio.com/api/extension-guides/tree-view).

Register disposables through `context.subscriptions` for extension lifetime, and
use shorter ownership for panels/documents. Track child processes, streams and
cancellation separately: disposing a command registration does not kill a
spawned process. Bound shutdown and preserve stderr diagnostics without printing
secrets. Keep activation cheap; load large indexes or tools on the feature's
trigger.

When an existing persisted format actually changes, validate loaded data and
perform an explicit migration. Add a version discriminator only if incompatible
representations require one; ordinary transient state needs no migration system.
Treat workspace identity and URI scheme/authority as part of cache keys.
Preserve unknown settings instead of overwriting user configuration wholesale.
Refresh the exact API for a minimum host that lacks a method used here.
