# Providers, cancellation and document ownership

Research: 2026-09-09; stable VS Code API, baseline 1.136.2.

## Register a narrowly selected provider

```ts
import * as vscode from "vscode";
export function activate(context: vscode.ExtensionContext) {
  context.subscriptions.push(
    vscode.languages.registerHoverProvider(
      { language: "plaintext", scheme: "file" },
      {
        async provideHover(document, position, token) {
          const version = document.version;
          const word = document.getWordRangeAtPosition(position);
          if (!word) return;
          const text = document.getText(word);
          const answer = await Promise.resolve(`Length: ${text.length}`);
          if (
            token.isCancellationRequested ||
            document.isClosed ||
            document.version !== version
          )
            return;
          return new vscode.Hover(answer, word);
        },
      },
    ),
  );
}
```

The `file` selector deliberately excludes untitled/virtual documents; broaden it
only when the implementation supports them. Replace the resolved Promise with
the asynchronous operation. Capture immutable inputs before awaiting and reject
stale results afterward. A cancellation token signals intent; pass it to the
real operation or map it to an AbortController/process cancellation when
supported. [Language features][ref-1].

## Edits, undo and diagnostics

For a user command, resolve the target editor/document when invoked, snapshot
version and text, compute outside the edit callback, then re-check
identity/version immediately before `TextEditor.edit` or `workspace.applyEdit`.
Honor the returned boolean. A check followed by a long await still permits stale
edits; versioned protocol edits provide stronger protection when using LSP. Do
not retain a `TextEditorEdit` builder across asynchronous work.

Use a single edit transaction for one logical user operation; define selection
and undo expectations. Apply nonoverlapping replacements against one snapshot.
Unsaved buffers are authoritative over disk content; filesystem reads alone miss
current edits. [Editor/workspace API][ref-2].

Create one owned `DiagnosticCollection`, set results by URI, and remove
diagnostics when a document is no longer relevant. A late analysis must not
overwrite a newer set. Debounce expensive document-change work with per-document
generations, cancel the prior request and clear timers on close. A watcher
indicates a possible filesystem change, not a reliable document version counter.

## Services, trees and process lifetime

A `TreeDataProvider` supplies data and an `onDidChangeTreeData` event; refresh
only the changed subtree when possible. Keep stable item IDs for
expansion/selection continuity. Commands attached to items must validate that
the target still exists. Use host theme colors and semantic icons. [Tree
views][ref-3].

Register disposables through `context.subscriptions` for extension lifetime, and
use shorter ownership for panels/documents. Track child processes, streams and
cancellation separately: disposing a command registration does not kill a
spawned process. Bound shutdown and preserve stderr diagnostics without printing
secrets. Keep activation cheap; load large indexes or tools on the feature's
trigger.

For state migration, store a schema version, validate loaded data, perform
idempotent transformations and write the new version only after successful
conversion. Treat workspace identity and URI scheme/authority as part of cache
keys. Preserve unknown settings instead of overwriting user configuration
wholesale. Refresh the exact API for a minimum host that lacks a method used
here.

[ref-1]:
  https://code.visualstudio.com/api/language-extensions/programmatic-language-features
[ref-2]: https://code.visualstudio.com/api/references/vscode-api
[ref-3]: https://code.visualstudio.com/api/extension-guides/tree-view
