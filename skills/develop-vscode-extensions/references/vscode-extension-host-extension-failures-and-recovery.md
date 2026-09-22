# Extension failures and recovery for Vscode Extension Host

| Failure mode | What it looks like | Required recovery |
| --- | --- | --- |
| **Visual Studio conflation** | VS Code APIs/package are mixed with Visual Studio extension concepts. | Use exact VS Code extension API/VSIX tooling. |
| **Filesystem assumption** | `uri.fsPath`/Node fs is used for remote/virtual/web resources. | Use `workspace.fs` and URI APIs when appropriate. |
| **Stale async edit** | Analysis for version N applies to N+1. | Capture and revalidate document identity/version/generation. |
| **Disposable leak** | Reload creates duplicate commands/watchers/processes. | Own and dispose all registrations/resources. |
| **Trust bypass** | Workspace-controlled command runs in untrusted workspace. | Enforce trust at execution boundary. |
| **Node-only web bundle** | Extension declares web support but imports unavailable APIs. | Separate/conditional host implementation and test. |
| **Package omission** | Runtime asset is not included in VSIX. | Inspect package manifest and archive contents. |

## Recovery discipline

Preserve the first observable VS Code extension failure and the state that
produced it. Stop dependent work after a false prerequisite. If another
equivalent retry cannot add evidence, change the source, instrument, or
hypothesis. Undo only task-owned experiments; preserve unrelated user work.

Do not make the VS Code extension appear successful by swallowing its error,
weakening its oracle, regenerating an unexplained snapshot, adding an
unsupported fallback, or reporting an intermediate checkpoint as completion.
