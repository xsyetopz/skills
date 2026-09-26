# Documents, edits, diagnostics, providers, and logging

Cards for code that reads and changes text. API facts come from
[`vscode.d.ts`][dts] unless another link is given. `Executed (host)`
means the mocha suite `assets/examples/extension/test/host/` passed in
VS Code 1.139.1 and 1.74.0 through `sh assets/examples/verify.sh
network`. `Executed (unit)` means `bun test` in the offline mode.

## Contents

- [TextDocument version and dirty state](#textdocument-version-and-dirty-state)
- [Edit versus save](#edit-versus-save)
- [Pre-save edits with onWillSaveTextDocument][toc-1]
- [WorkspaceEdit and workspace.applyEdit](#workspaceedit-and-workspaceapplyedit)
- [TextEditor.edit for selection edits](#texteditoredit-for-selection-edits)
- [Stale asynchronous result guard](#stale-asynchronous-result-guard)
- [DiagnosticCollection](#diagnosticcollection)
- [Document selectors with schemes](#document-selectors-with-schemes)
- [Language feature providers](#language-feature-providers)
- [LogOutputChannel](#logoutputchannel)

## TextDocument version and dirty state

**Definition.** `TextDocument.version` strictly increases after each
change, including undo and redo. `isDirty` is `true` while the buffer
has unsaved changes. `isClosed` is `true` after the document closes, and
VS Code does not reuse a closed document when the resource reopens.
`onDidChangeTextDocument` also fires for dirty-state changes, with an
empty `contentChanges` array. Its `reason` is `Undo`, `Redo`, or
`undefined` (typings since 1.62).

**Use when.**

- Deciding whether a result computed earlier still matches the text:
  compare `version`.
- Deciding whether the disk content matches the editor: `isDirty`.

**Do not use when.**

- Reacting to text changes only. Skip events with
  `contentChanges.length === 0`, or dirty-flag flips re-run the work.
- Reading the file from disk with `fs` or `workspace.fs` to get the
  current text. Unsaved edits exist only in the `TextDocument`.

**Example.** `src/common.ts`:

```ts
vscode.workspace.onDidChangeTextDocument((e) => {
  if (e.contentChanges.length > 0) relint(e.document);
}),
```

**Cost removed.** Re-lints on save and on dirty-flag changes. Observe
them through the `log.debug` lines (`lint <uri> v<version>`) at log
level Debug.

**Verify.**

1. Host test `WorkspaceEdit dirties the buffer; save runs onWillSave`
   asserts `version === before + 1` after one edit, and `isDirty` before
   and after the save.
1. Set **Developer: Set Log Level... > Debug** and check that saving
   adds no `lint` line.

## Edit versus save

**Definition.** An edit (`applyEdit`, `TextEditor.edit`, typing)
changes the in-memory document and makes it dirty. The file on disk
stays unchanged until `document.save()`, `workspace.save`, or the user
saves. `onDidSaveTextDocument` fires after the write. Save events fire
for every document, including `vscode-userdata:` settings files.

**Use when.**

- The user should review and undo the change: edit only.
- A tool reads the file from disk next: save after editing, and check
  the boolean that `save()` returns.

**Do not use when.**

- Saving for the user after each edit. That defeats review and
  triggers other save participants (formatters, linters).
- Handling save events without a filter. The fixture's first host run
  logged `saved vscode-userdata:.../User/settings.json` from its own
  listener until it filtered with `languages.match`.

**Example.** `test/host/trusted.test.ts` (excerpt):

```ts
assert.equal(doc.isDirty, true);
assert.equal(await disk(), initial, "edit must not write disk");
assert.equal(await doc.save(), true);
assert.equal(doc.isDirty, false);
assert.equal(saved, 1);
```

**Cost removed.** Lost edits and surprise writes. Executed (host): the
disk bytes are unchanged after the edit and match the buffer after
`save()`, and `onDidSaveTextDocument` fired once for the file.

**Verify.**

1. The host test above passes.
1. Run `rg -n 'onDidSaveTextDocument|onWillSaveTextDocument' src` and
   check that each handler filters documents first.

## Pre-save edits with onWillSaveTextDocument

**Definition.** `onWillSaveTextDocument` fires before a save.
`event.waitUntil(thenable)` delays the save and applies the returned
`TextEdit[]`. Call `waitUntil` synchronously during dispatch; an async
call throws. VS Code ignores the edits after a concurrent modification.
Listeners share a 1.5 s budget, and a listener that misbehaves 3 times
is no longer called. The editor can save without firing the event, for
example on shutdown with dirty files.

**Use when.**

- Normalizing text as part of the save (trim, fix line endings).

**Do not use when.**

- The edit needs slow work (network, a process). It eats the shared
  budget and can be skipped; run it as a command instead.
- Correctness depends on it. The event is not guaranteed.

**Example.** `src/common.ts`:

```ts
vscode.workspace.onWillSaveTextDocument((e) => {
  if (!ours(e.document)) return; // settings.json saves arrive here too
  const config = vscode.workspace.getConfiguration(SECTION, e.document);
  if (!config.get<boolean>("trimTrailingWhitespaceOnSave", true)) return;
  const edits = trailingWhitespace(e.document.getText()).map((r) =>
    vscode.TextEdit.delete(new vscode.Range(r.line, r.start, r.line, r.end)),
  );
  e.waitUntil(Promise.resolve(edits)); // synchronous call
}),
```

**Cost removed.** A second save or a separate formatting step.
Executed (host): the buffer `"TODO(ann) fix  \nTODO(ann) b\n"` is
saved as `"TODO(ann) fix\nTODO(ann) b\n"`.

**Verify.**

1. Host test `WorkspaceEdit dirties the buffer; save runs onWillSave`
   asserts the trimmed disk content.
1. `rg -n 'waitUntil' src` shows no call inside `await`, `then`, or a
   timer callback.

## WorkspaceEdit and workspace.applyEdit

**Definition.** A `WorkspaceEdit` collects text edits, and file
creates, renames, and deletes, across documents.
`workspace.applyEdit(edit)` applies them in insertion order and
resolves to `true` or `false`. An edit with only text changes is
all-or-nothing. It works on documents that no editor shows.

**Use when.**

- Edits target a document by URI or span several documents.
- Edits come from a code action or a command with no active editor.

**Do not use when.**

- Only the active editor's selections change and the edit must keep
  them. Use `TextEditor.edit` (next card).
- The caller ignores the boolean. `false` means nothing applied.

**Example.** `src/common.ts`:

```ts
function ownerEdit(
  document: vscode.TextDocument,
  ranges: readonly vscode.Range[],
  owner: string,
): vscode.WorkspaceEdit {
  const edit = new vscode.WorkspaceEdit();
  const suffix = ownerSuffix(owner);
  for (const range of ranges) {
    edit.insert(document.uri, range.end, suffix);
  }
  return edit;
}
// ...
return vscode.workspace.applyEdit(ownerEdit(document, ranges, owner));
```

**Cost removed.** Partial edits across ranges. Executed (host): one
`applyEdit` with two inserts changed the document once (`version ===
before + 1`) and returned `true`.

**Verify.**

1. The host test asserts `applied === true`, the new text, and the
   version.
1. `rg -n 'applyEdit\(' src` shows every result returned or checked.

## TextEditor.edit for selection edits

**Definition.** `editor.edit(callback)` builds edits with a
`TextEditorEdit` builder that is valid only during the callback. All
edits of one call form one undo step. The call resolves to whether they
applied.

**Use when.**

- Transforming the active editor's selections in place.

**Do not use when.**

- The builder would be used after an `await`. It is invalid by then.
- No visible editor shows the document. Use `WorkspaceEdit`.

**Example.** Salvaged from the earlier template, now
`todoOwner.encodeJsonStrings` in `src/common.ts`:

```ts
const selections = editor.selections.filter((s) => !s.isEmpty);
if (selections.length === 0) return false;
return editor.edit((builder) => {
  for (const selection of selections) {
    const text = editor.document.getText(selection);
    builder.replace(selection, JSON.stringify(text));
  }
});
```

**Cost removed.** One undo step per selection. Executed (host): three
selections (one empty) encode `α"x` and `second\line`, a single `undo`
restores the text, and an empty selection leaves `version` unchanged.

**Verify.**

1. Host test `encodeJsonStrings: one undo step, empty selection no-op`
   passes.
1. Mutation: remove `JSON.stringify` in a copy; the test must fail.

## Stale asynchronous result guard

**Definition.** Before an `await`, record the document key, its
`version`, and a per-key generation number. After it, publish only if
the document is still open at that version and no newer request for
the key has started. The version catches edits, the generation catches
a newer request at the same version, and a missing document catches a
close.

**Use when.**

- A result computed across an `await` (process, network, worker) is
  written back as an edit, diagnostic, or decoration.

**Do not use when.**

- The work is synchronous. There is no window for staleness, so do not
  add promises to justify the guard.
- The API passes a `CancellationToken` and cancels for you
  (providers). Also check `token.isCancellationRequested`, but keep the
  version check before an edit.

**Example.** `src/core.ts` (pure, unit tested):

```ts
export class RequestGenerations {
  private readonly latest = new Map<string, number>();

  start(key: string): number {
    const next = (this.latest.get(key) ?? 0) + 1;
    this.latest.set(key, next);
    return next;
  }

  isCurrent(key: string, generation: number, startedVersion: number,
    currentVersion: number | undefined): boolean {
    return this.latest.get(key) === generation &&
      currentVersion === startedVersion;
  }

  forget(key: string): void {
    this.latest.delete(key);
  }
}
```

`applyOwner` in `src/common.ts` calls `start` before `await
resolveOwner(...)`, looks the document up again in
`workspace.textDocuments`, and logs `discarded stale owner edit` when
`isCurrent` is false. `onDidCloseTextDocument` calls `forget`.

**Cost removed.** Edits computed for version N applied to N+1.
Executed (unit): 4 tests cover the current request, a changed version,
a superseded request, and a closed document. No host test covers the
race itself: the ordering between the host and the renderer is not
deterministic, so such a test would be flaky.

**Verify.**

1. `bun test test/unit` shows the 4 `RequestGenerations` tests passing.
1. Run `rg -n 'await' src/common.ts` and check that the `isCurrent`
   check follows each await that precedes a write.

## DiagnosticCollection

**Definition.** `languages.createDiagnosticCollection(name)` returns a
collection keyed by URI. `set(uri, diagnostics)` replaces that URI's
list, `delete(uri)` removes it, `clear()` empties the collection, and
`dispose()` clears and frees it ([language features][langfeat]).

**Use when.**

- Publishing problems that the extension computes. An LSP client owns
  its own collection.

**Do not use when.**

- Appending. `set` replaces, so merge first or keep one collection per
  source.
- The code never calls `delete` on close. Problems for closed files
  then stay in the Problems view.

**Example.** `src/common.ts` (excerpt):

```ts
const diagnostics = vscode.languages.createDiagnosticCollection(SECTION);
context.subscriptions.push(diagnostics);
// lint():
const d = new vscode.Diagnostic(range, "TODO has no owner", severity);
d.source = "todo-owner";
d.code = "unowned-todo";
diagnostics.set(document.uri, found);
// onDidCloseTextDocument:
diagnostics.delete(document.uri);
```

**Cost removed.** Stale problems. Executed (host):
`languages.getDiagnostics(uri)` has 1 entry for `a TODO fix` and 0 after
inserting `(ann)`.

**Verify.**

1. Host test `diagnostics follow edits and the severity setting`
   passes.
1. `rg -n 'createDiagnosticCollection' src` shows the collection pushed
   to `context.subscriptions`.

## Document selectors with schemes

**Definition.** A `DocumentSelector` is a list of filters with
`language`, `scheme`, and `pattern`. `languages.match(selector, doc)`
returns a score, 0 for no match. VS Code logs `Extension '<id>' uses a
document selector without scheme` when a filter omits `scheme`
(observed in `exthost.log`, VS Code 1.139.1).

**Use when.**

- Registering any provider. List only the schemes the code handles:
  `file`, `untitled`, and `vscode-vfs` for virtual workspaces
  ([virtual workspaces][virtual]).
- Filtering workspace-wide events (save, open) to your documents.

**Do not use when.**

- The provider reads the file with Node `fs` or `uri.fsPath`. Then
  only `scheme: "file"` is correct.

**Example.** `src/common.ts`:

```ts
const SCHEMES = ["file", "untitled", "vscode-vfs"];
const SELECTOR: vscode.DocumentSelector = ["plaintext", "markdown"].flatMap(
  (language) => SCHEMES.map((scheme) => ({ language, scheme })),
);
const ours = (document: vscode.TextDocument): boolean =>
  vscode.languages.match(SELECTOR, document) > 0;
```

**Cost removed.** Providers that run on output, git, and settings
documents. Executed: the first host run logged the warning. After the
schemes were added, `verify.sh network` asserts that the warning is
absent.

**Verify.**

1. `verify.sh network` check `no 'document selector without scheme'`.
1. `rg -n 'language: ' src` shows a `scheme` next to every `language`.

## Language feature providers

**Definition.** `languages.register<Feature>Provider(selector,
provider)` connects a feature (hover, completion, code actions,
formatting, definitions, and 20 more in the [listing][langfeat]) to
documents. VS Code calls the provider with a `CancellationToken`.
`registerCodeActionsProvider` takes `providedCodeActionKinds` metadata.

**Use when.**

- The feature serves one language and fits in the extension host.

**Do not use when.**

- The server is shared across editors. Use a language server through
  `vscode-languageclient` instead ([language features][langfeat]).
- Formatting returns the whole document as one edit. Return the
  smallest edits, or markers and diagnostics lose their positions.
- Heavy work runs inside the provider without checking the token.

**Example.** Quick fix for the TODO diagnostic, `src/common.ts`:

```ts
class AddOwnerAction implements vscode.CodeActionProvider {
  static readonly kinds = [vscode.CodeActionKind.QuickFix];

  provideCodeActions(document: vscode.TextDocument, _range: vscode.Range,
    context: vscode.CodeActionContext): vscode.CodeAction[] {
    return context.diagnostics
      .filter((d) => d.code === "unowned-todo")
      .map((d) => {
        const action = new vscode.CodeAction(
          "Add owner", vscode.CodeActionKind.QuickFix);
        action.diagnostics = [d];
        action.command = {
          command: "todoOwner.addOwner",
          title: "Add owner",
          arguments: [document.uri, d.range],
        };
        return action;
      });
  }
}
```

**Cost removed.** Fixing each finding by hand. Executed (host):
`executeCommand("vscode.executeCodeActionProvider", uri, range)` returns
an action titled `Add owner`.

**Verify.**

1. Host test `diagnostics follow edits and the severity setting` checks
   the action through `vscode.executeCodeActionProvider`.
1. `rg -n 'register\w+Provider' src` shows each registration pushed to
   `context.subscriptions`.

## LogOutputChannel

**Definition.** `window.createOutputChannel(name, { log: true })`
(typings since 1.74) returns a `LogOutputChannel` with `trace`, `debug`,
`info`, `warn`, `error`, and a `logLevel` that follows the editor log
level. Plain `createOutputChannel(name)` returns an `OutputChannel` with
only `append`/`appendLine`.

**Use when.**

- Users attach the log to bug reports. They raise verbosity with
  **Developer: Set Log Level...**, so the extension needs no setting of
  its own.

**Do not use when.**

- The floor is below 1.74. Use `OutputChannel`.
- Logging secrets, tokens, or document text. Logs are files on disk.

**Example.** `src/extension.node.ts` and `src/common.ts`:

```ts
const log = vscode.window.createOutputChannel("TODO Owner", { log: true });
context.subscriptions.push(log);
log.info(`activated in ${vscode.env.appHost}, trusted=` +
  `${vscode.workspace.isTrusted}`);
log.debug(`lint ${document.uri.toString()} v${document.version}`, count);
log.info("API token stored"); // never log the value
```

**Cost removed.** Custom log-level settings and ad hoc timestamps.
Executed (host): the channel wrote `TODO Owner.log` under
`<user-data-dir>/logs/<session>/window1/exthost/skills-example.todo-owner/`
with `[info] activated in desktop, trusted=true`. `debug` lines were
absent at the default Info level.

**Verify.**

1. `verify.sh network` check `LogOutputChannel wrote ...`.
1. Run `rg -n 'log\.(info|warn|error|debug)\(' src` and read each hit
   for secret values.

[dts]: https://github.com/microsoft/vscode/blob/main/src/vscode-dts/vscode.d.ts
[langfeat]: https://code.visualstudio.com/api/language-extensions/programmatic-language-features
[virtual]: https://code.visualstudio.com/api/extension-guides/virtual-workspaces
[toc-1]: #pre-save-edits-with-onwillsavetextdocument
