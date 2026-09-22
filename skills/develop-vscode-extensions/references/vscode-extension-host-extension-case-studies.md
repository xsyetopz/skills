# Extension case studies for Vscode Extension Host

## VS Code: stale asynchronous result guard

```ts
const uri = document.uri.toString();
const version = document.version;
const generation = ++requestGeneration;
const result = await analyze(document.getText(), token);
if (token.isCancellationRequested || generation !== requestGeneration) return;
const current = vscode.workspace.textDocuments.find(
  (document) => document.uri.toString() === uri,
);
if (!current || current.version !== version) return;
publish(result);
```

The generation and document version protect different races. An extension-host
test must change the document before completion and observe that no stale result
is published.

## Lifecycle evidence checklist

- activate/load once and twice;
- invoke normal and failing inputs;
- start async work, then edit/close/dispose before completion;
- cancel and verify no late publication;
- unload/reload or close/reopen project/workspace;
- inspect duplicate registrations, processes, timers, handles, and persisted
  state;
- build package, inspect contents, install in a clean declared host;
- distinguish stub/unit tests from real host execution.
